import concurrent.futures
import threading
from unittest import mock

from dikte import api, audio, progressive, worker
from tests.support import DikteTest, make_wav, speech


class Progressive(DikteTest):
    def session(self):
        session = progressive.Session(self.config(transcribe_provider="local", language="tr"))
        self.addCleanup(session.cancel)
        return session

    def feed_phrase(self, session):
        pcm = b"\x01\x01" * 1024
        for _ in range(80):
            session.feed(pcm, 0.1)
        for _ in range(12):
            session.feed(bytes(2048), 0.0001)

    def test_pause_starts_work_before_stop_and_preserves_audio_coverage(self):
        session = self.session()
        seen = []
        def transcribe(pcm):
            seen.append(pcm)
            return "çok çok önemli" if len(seen) == 1 else "silme", "tr"
        session._transcribe = transcribe
        self.feed_phrase(session)
        session.parts[0].result(timeout=2)
        self.assertEqual(len(seen), 1)
        tail = b"\x02\x02" * 48000
        session.feed(tail, 0.1)
        full = seen[0][:-8000] + bytes(session.buffer)
        path = make_wav(self.path("full.wav"), full)
        result = session.finish(path, threading.Event())
        self.assertEqual(result, ("çok çok önemli silme", "tr"))
        self.assertEqual(seen[0][:-8000] + seen[1], full)

    def test_no_forced_cut_during_continuous_speech(self):
        session = self.session()
        for _ in range(300):
            session.feed(bytes(2048), 0.1)
        self.assertEqual(session.parts, [])
        self.assertIsNone(session.finish("unused", threading.Event()))

    def test_tiny_final_tail_rechecks_last_phrase_without_losing_samples(self):
        session = self.session()
        seen = []
        def transcribe(pcm):
            seen.append(pcm)
            return "silme", "tr"
        session._transcribe = transcribe
        self.feed_phrase(session)
        session.parts[0].result(timeout=2)
        extra = b"\x02\x02" * 1000
        session.feed(extra, 0.1)
        full = seen[0] + extra
        path = make_wav(self.path("tiny-tail.wav"), full)
        self.assertEqual(session.finish(path, threading.Event()), ("silme", "tr"))
        self.assertEqual(seen[-1], full)

    def test_finished_pieces_bypass_full_transcription(self):
        conf = self.config(transcribe_provider="local", language="tr",
                           cleanup_enabled=False, auto_paste=False, skip_silent=False)
        session = progressive.Session(conf)
        self.addCleanup(session.cancel)
        path = make_wav(self.path("success.wav"), speech(2))
        with mock.patch.object(session, "finish", return_value=("çok çok önemli silme", "tr")), \
                mock.patch.object(api, "transcribe") as transcribe, \
                mock.patch("dikte.paste.copy"):
            done = []
            pipeline = worker.Pipeline(conf)
            pipeline.finished.connect(lambda *args: done.append(args))
            pipeline._work(path, 2, (), False, progressive=session)
            self.assertEqual(done[0][0], "çok çok önemli silme")
            transcribe.assert_not_called()

    def test_slow_inference_does_not_queue_every_pause(self):
        session = self.session()
        gate = threading.Event()
        self.addCleanup(gate.set)
        session._transcribe = lambda pcm: (gate.wait(2) and "hello", "tr")
        self.feed_phrase(session)
        self.feed_phrase(session)
        self.assertEqual(len(session.parts), 1)

    def test_cancel_keeps_new_audio_out(self):
        session = self.session()
        session.cancel()
        session.feed(b"abc", 0.1)
        self.assertEqual(session.buffer, b"")

    def test_partial_failure_falls_back_to_full_recording(self):
        conf = self.config(transcribe_provider="local", language="tr",
                           cleanup_enabled=False, auto_paste=False, skip_silent=False)
        session = progressive.Session(conf)
        self.addCleanup(session.cancel)
        path = make_wav(self.path("full.wav"), speech(2))
        with mock.patch.object(session, "finish", side_effect=api.ApiError("piece failed")), \
                mock.patch.object(api, "transcribe", return_value="tam kayıt silme") as transcribe, \
                mock.patch("dikte.paste.copy"):
            done = []
            pipeline = worker.Pipeline(conf)
            pipeline.finished.connect(lambda *args: done.append(args))
            pipeline._work(path, 2, (), False, progressive=session)
            self.assertEqual(done[0][0], "tam kayıt silme")
            self.assertEqual(transcribe.call_args.args[1], path)

    def test_stop_interrupts_wait_for_partial_result(self):
        session = self.session()
        future = concurrent.futures.Future()
        session.parts.append(future)
        stop = threading.Event()
        stop.set()
        with self.assertRaises(api.ApiError):
            session.finish("unused", stop)
