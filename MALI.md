# Dikte Mali

Kendi fork'umuz: https://github.com/m-alipir/dikte

Windows: çalışan Dikte'yi tepsi menüsünden kapat, ardından `Dikte-Mali.cmd` dosyasına çift tıkla. Python 3.11+ gerekir. İlk çalıştırma sanal ortamı oluşturur ve PyQt6 indirir. Mevcut kurulumun ffmpeg ve yerel modellerini kullanır. Model yoksa uygulamadan indirilebilir.

Kişisel başlatıcı `mali.py`, ayarları `%LOCALAPPDATA%/Dikte/mali-settings/config.json` altında ayrı tutar. Orijinal ayar dosyasını değiştirmez. Yerel modeller, günlük ve geçmiş mevcut Dikte veri klasörünü paylaşır. Aynı anda iki sürümü açma. Standart Dikte'yi tekrar başlatmak geri dönüş için yeterlidir.

Bu başlatıcının ilk varsayılanları: konuşurken işleme açık, Türkçe, cleanup kapalı, sesi saklama açık. Önceden kaydedilmiş kişisel ayarlar bu varsayılanları geçersiz kılar. Kaynak projedeki normal başlatıcıda deneysel özellik varsayılan olarak kapalıdır.

Yerel model seçeneklerinde **Duraksamalarda transkript et (deneysel)** kutusuyla kapatılabilir. Yalnızca yerel normal dikteyi etkiler; toplantılar ve ajana sor modu mevcut akışını kullanır.

En az beş saniye biriktikten sonra düşük enerjili yaklaşık 700 ms duraksamada arka planda transkripsiyon başlar. Sadece sessiz sınırın 250 ms bölümü örtüşür; gerçek sözcük tekrarları silinmez. Mikrofon durdurulmaz. Yavaş çıkarımda yeni parçalar kuyruğa yığılmaz; henüz işlenmemiş ses birikir. Duraksama yoksa zorla kesilmez ve normal tam kayıt yolu kullanılır. Bir parça başarısız veya stok halüsinasyon gibi görünürse tam WAV yeniden işlenir. Son metin bir kez yapıştırılır.

Sınırlar: enerji eşiği eğitimli VAD değildir; düşük sesle konuşmada veya gürültüde yanlış sınır seçebilir. Ayrı parçalarda bağlam daralabilir. Bu nedenle deneysel kabul edilir; kelime kaybı ve hız garantisi yoktur. Gerçek mikrofonla olumsuzluklar, sayılar, tekrarlar ve teknik terimleri karşılaştır. Hata kurtarma tam kayıt nedeniyle yavaşlayabilir. Bulut streaming sağlayıcısı eklenmedi.

Geçmiş JSONL satırlarında `transcribe_elapsed` ve `cleanup_elapsed`, kayıt durduktan sonraki pipeline aşamalarını saniye cinsinden ayırır; kayıt kapatma ve yapıştırmanın toplam süresi değildir. Konuşurken yapılan iş bu transkripsiyon süresinin dışında kalır.

Test: `.venv/Scripts/python.exe -m unittest discover`. Ağ ve mikrofon kullanmayan parça/son ses kapsaması, tekrar ve olumsuzluk koruma, yavaş işçi, iptal ve tam kayda hata dönüşü testleri eklendi. Gerçek Türkçe ses kabul testi ayrıca gerekir.

GPL-3.0 lisansı ve kaynak kod korunmuştur. Bu bir upstream sürümü değildir.

Son parça iki saniyeden kısaysa yalnızca sessiz bir kuyruğu modele vermek yerine son konuşma parçasıyla birlikte tekrar işlenir. Böylece son ses atlanmaz; karşılığında son cümle yeniden hesaplanabilir.


## Metni düzenleme ve geçmişten seçim

Son metin alanı düzenlenebilir. Enter seçili kısmı, seçim yoksa tamamını panoya kopyalar; Shift+Enter yeni satır ekler. Taslağı temizle yalnızca ekrandaki çalışma metnini siler, geçmiş kaydını değiştirmez. Düzenlenmiş bir taslak dururken yeni sonuç gelirse metnin üzerine yazılmaz; Son transkripti yükle düğmesiyle yeni kayda geçilir. Taslak düzenlemeleri oturumluk çalışma metnidir, diske veya geçmişe kaydedilmez; uygulama kapatıldığında kaybolur.

Kayıt sırasında Baştan başla, mevcut kaydı iptal edip yeni kayıt açar; vazgeçilen konuşmayı transkript/geçmişe göndermez. Önceden tamamlanmış geçmiş kayıtlarını silmez.

Geçmiş sekmesinde bir kayıt seçildiğinde aşağıdaki salt okunur alanda tamamı görünür. Fareyle istenen bölüm seçilebilir; Ctrl+C veya Metni kopyala seçimi kopyalar. Seçim yoksa düğme metnin tamamını kopyalar. Geçmişte düzenleme yoktur.

Kişisel başlatıcıda otomatik yapıştırma ilk varsayılanı kapalıdır. Kaydı bitirince metin kontrol edilip kopyalanabilir. Daha önce kaydedilmiş ayarlar önceliklidir.
