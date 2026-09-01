[README.md](https://github.com/user-attachments/files/31683326/README.md)
# Yörünge MVP

TeknoChallenge demo prototipi. Hastalık-agnostik çekirdek (hasta profili, tahlil takibi,
doktor değerlendirmesi, reçete/randevu) + onkolojiye özel takip katmanı.

## Kurulum

```
cd yorunge_mvp
pip install -r requirements.txt
streamlit run app.py
```

Tarayıcınızda otomatik olarak `http://localhost:8501` açılır. İlk açılışta demo veri
(2 hasta, 3 doktor, tahlil geçmişi, randevular, mesajlar) otomatik oluşturulur.

## Görünümler

Sol menüden üç görünüm arasında geçiş yapılır:

- **Hasta** — günaydın karşılaması, ruh hali/ağrı check-in'i (0-10 skala), tedavi özeti,
  ilaç/tahlil hatırlatmaları, online görüşme talebi oluşturma, doktor özeti
- **Doktor** — günaydın karşılaması, hızlı istatistikler (bugünkü randevu / acil bildirim /
  onay bekleyen), acil bildirimler kartı, 3 sekme (Randevularım / Tahlil sonuçları / Hasta
  mesajları), hasta detayında AI özeti + meslektaştan görüş alma + not/reçete girme,
  randevu onaylama veya yeni tarih önerme
- **Hastane Yönetimi** — verimlilik metrikleri (pilot veri toplandıkça dolacak placeholder'lar)

## AI Özeti hakkında

`db.generate_ai_summary()` şu an kural tabanlı, deterministik bir özet üretiyor (API anahtarı
gerektirmiyor). Gerçek bir AI entegrasyonu için bu fonksiyonu Anthropic API'ye (Claude) hastanın
tahlil/not/mesaj geçmişini gönderip özet ürettirecek şekilde genişletebilirsiniz — kod içinde
fonksiyonun üstünde bunun için not bırakıldı.

## Yarışma sunumu için önerilen demo akışı

1. **Hasta** görünümünde bir check-in yapın (ağrı skalasını yüksek girin) ve online görüşme talebi oluşturun
2. **Doktor** görünümüne geçin — üstteki "Acil bildirimler" ve "Onay bekleyen" sayılarının güncellendiğini gösterin
3. Randevu talebini **onaylayın** ya da **yeni tarih önerin** — hasta tarafında durumun değiştiğini anlatın
4. Hasta detayında **AI Özeti**'ni gösterin, bir değerlendirme notu girin
5. **Hastane Yönetimi** panelini açıp vizyonu anlatın ("pilot başladığında bu sayılar dolacak")

Bu 5 adım, sistemin uçtan uca "tanı sonrası süreci yönetme" değerini 3-4 dakikada anlatır.
