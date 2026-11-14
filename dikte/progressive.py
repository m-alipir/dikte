"""Local dictation in silence-delimited pieces; the full WAV remains the fallback."""

import concurrent.futures
import os
import threading
import wave

from . import api, audio, vad


class Levels(list):
    """Carry this recording's session through the existing stopped signal."""


class Session:
    def __init__(self, conf):
        self.target = conf.transcribe_target()
        self.language = conf["language"]
        self.prompt = conf.dictionary_hint()
        self.buffer = bytearray()
        self.offset = 0
        self.last_pcm = b""
        self.quiet = 0
        self.peak = 0.0
        self.parts = []
        self.cancelled = threading.Event()
        self.failed = False

    def feed(self, pcm, rms):
        if self.cancelled.is_set() or self.failed:
            return
        self.buffer.extend(pcm)
        self.peak = max(self.peak, rms)
        quiet = rms < min(0.003, self.peak / 10)
        self.quiet = self.quiet + len(pcm) if quiet else 0
        rate = audio.RATE * audio.SAMPLE_WIDTH
        # shortcut: energy boundaries only, use a trained VAD after microphone validation.
        if (len(self.buffer) < 5 * rate or self.quiet < 0.7 * rate
                or self.peak < 0.01 or (self.parts and not self.parts[-1].done())):
            return
        # Overlap only the quiet margin, so real repeated words are never deduplicated.
        overlap = int(0.25 * rate)
        pcm = bytes(self.buffer)
        self.last_pcm = pcm
        future = concurrent.futures.Future()
        self.parts.append(future)
        threading.Thread(target=self._run, args=(future, pcm), daemon=True).start()
        self.offset += len(pcm) - overlap
        self.buffer = bytearray(pcm[-overlap:])
        self.quiet = overlap
        self.peak = 0.0

    def _run(self, future, pcm):
        if not future.set_running_or_notify_cancel():
            return
        try:
            future.set_result(self._transcribe(pcm))
        except Exception as exc:
            future.set_exception(exc)

    def _transcribe(self, pcm):
        if self.cancelled.is_set():
            raise api.ApiError("Progressive dictation cancelled")
        path = audio.write_wav(pcm)
        try:
            if self.language == "auto":
                result = api.transcribe_detected(self.target, path, language=self.language,
                                                prompt=self.prompt)
            else:
                result = api.transcribe(self.target, path, language=self.language,
                                        prompt=self.prompt), ""
            if vad.looks_like_hallucination(result[0], len(pcm) / (audio.RATE * 2)):
                raise api.ApiError("Uncertain progressive fragment")
            return result
        finally:
            os.unlink(path)

    def finish(self, wav_path, stop):
        try:
            results = []
            for part in self.parts:
                while True:
                    if stop.is_set() or self.cancelled.is_set():
                        raise api.ApiError("Progressive dictation cancelled")
                    try:
                        results.append(part.result(timeout=0.1))
                        break
                    except concurrent.futures.TimeoutError:
                        continue
            if self.failed or not results:
                return None
            with wave.open(wav_path, "rb") as wav:
                wav.setpos(self.offset // audio.SAMPLE_WIDTH)
                tail = wav.readframes(wav.getnframes())
            if len(tail) < 2 * audio.RATE * audio.SAMPLE_WIDTH:
                # A tiny tail may be only boundary silence; recheck its whole phrase.
                results.pop()
                tail = self.last_pcm[:-int(0.25 * audio.RATE * audio.SAMPLE_WIDTH)] + tail
            results.append(self._transcribe(tail))
            return " ".join(text for text, _ in results), next(
                (language for _, language in results if language), "")
        finally:
            for part in self.parts:
                part.cancel()

    def cancel(self):
        self.cancelled.set()
        for part in self.parts:
            part.cancel()
