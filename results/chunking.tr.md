# Chunking Stratejisi Karşılaştırması

Bir dokümanın embedding öncesinde nasıl parçalandığı, arama sisteminin neyi bulabileceğini belirler. Burada üç strateji aynı sorular üzerinde karşılaştırılıyor:

- **`whole_doc`** — her dosyayı tek bir chunk sayar.
- **`by_heading`** — markdown `## ` başlıklarından böler.
- **`fixed_window`** — belgenin yapısına hiç bakmadan her 300 kelimede bir keser. Karşılaştırmanın alt sınırı: yapı bilgisi kullanmanın gerçekten bir fark yaratıp yaratmadığını görmek için burada.

Ölçüm 57 soruluk gold-standard set üzerinde yapıldı: 47 sorunun beklenen bir kaynağı var, 10 tanesi ise bilerek kapsam dışı seçildi. Sorular ve beklenen cevaplar `eval/questions.yaml` dosyasında.

## Sonuçlar

Doğru kaynağı ilk sıraya koyma başarısına göre iyiden kötüye sıralı. Her sütunun en iyi değeri **koyu renkte** gösteriliyor.

| chunker | parça | doğru kaynak 1. sırada | ilk 5'te bulundu | tüm kaynaklar ilk 5'te | 5 sonuçtan doğru oranı | sıralama kalitesi |
|---|---|---|---|---|---|---|
| **by_heading** | 319 | **0.809** | 0.936 | **0.904** | **0.251** | **0.870** |
| whole_doc | 91 | 0.745 | **0.957** | 0.883 | 0.234 | 0.840 |
| fixed_window | 239 | 0.723 | 0.936 | 0.858 | 0.230 | 0.822 |

**Sütunlar ne anlama geliyor.** Tüm değerler 0 ile 1 arasında, yüksek olan iyidir.

- **doğru kaynak 1. sırada** — ilk sonucun doğru çıkma oranı. En katı ölçüt ve pratikte en önemlisi: insanlar en üsttekini okur. *(HitRate@1)*
- **ilk 5'te bulundu** — doğru kaynağın gösterilen beş sonuçtan herhangi birinde çıkma oranı. *(HitRate@5)*
- **tüm kaynaklar ilk 5'te** — bazı soruların birden fazla doğru kaynağı var; bunların ne kadarının bulunduğunu gösterir. *(Recall@5)*
- **5 sonuçtan doğru oranı** — zorunlu olarak düşük: soruların çoğunun tek veya iki doğru kaynağı olduğundan, beş sıranın üçü hiçbir zaman doğru olamaz. *(Precision@5)*
- **sıralama kalitesi** — konumu ve doğruluğu birleştiren tek sayı. Doğru kaynağı listeye sokmayı değil, *başa* koymayı ödüllendirir. *(MRR)*

**Tablo nasıl okunur.** Doğru kaynağı en sık ilk sıraya koyan `by_heading` (0.809); sıralama kalitesinde de en iyi o (0.870). Sistemde kullanılan strateji bu. İlk 5'te bulma ölçütünde ise `whole_doc` önde (0.957): dosyanın tamamı tek parça olduğunda doğru dokümanı tamamen kaçırmak zorlaşıyor, ama onu ilk sıraya koymak da zorlaşıyor. Başlıklardan bölmek, arama sistemine bir sorunun kapsamına denk düşen bir birim veriyor: bir bölüm, bir fikir.

## Daha fazla sonuç döndürmek işe yarıyor mu?

Gösterilen sonuç sayısı arttıkça doğru kaynağın bulunma oranı. Ancak on sonuçta başa baş gelen bir strateji, doğru dokümanı buluyor ama aşağıda bırakıyor demektir.

| chunker | 1. sırada | ilk 3'te | ilk 5'te | ilk 10'da |
|---|---|---|---|---|
| by_heading | **0.809** | 0.936 | 0.936 | 0.979 |
| whole_doc | 0.745 | 0.936 | 0.957 | 0.979 |
| fixed_window | 0.723 | 0.936 | 0.936 | 0.979 |

On sonuç gösterildiğinde üçü de aynı noktada buluşuyor; yani aralarındaki fark hangi dokümanlara ulaşabildikleri değil, onları nasıl sıraladıkları.

## Bilgi tabanının kapsamadığı soruları reddetmek

Arama sistemi, corpus'un hakkında hiçbir şey söylemediği bir soru için bile en yakın eşleşmeleri döndürür. Buradaki soru şu: bi-encoder'ın benzerlik skoruna konacak basit bir eşik, bu tür soruları yakalamaya yeter mi?

| chunker | kapsam dışı soru | 0.3 altında doğru reddedilen |
|---|---|---|
| whole_doc | 10 | 3/10 |
| by_heading | 10 | 3/10 |
| fixed_window | 10 | 3/10 |

Yetmiyor: hiçbir chunking stratejisi, yalnızca benzerlik skoruna bakarak kapsam içi ve kapsam dışı soruları güvenilir şekilde ayıramıyor. Sistemde şu an kullanılan cross-encoder tabanlı kapsam denetimi bu negatif sonucun ardından geldi. Devamı iki raporda: *Kapsam-dışı eşik analizi* ham benzerlik skorunun neden yetersiz kaldığını, *Eşik seçimi* ise yerine gelen eşiğin nasıl belirlendiğini anlatıyor.
