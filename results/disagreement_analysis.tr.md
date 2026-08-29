# Aramanın Yanıldığı Yerler

Tek bir başarı yüzdesi, aramanın ne sıklıkla doğru bulduğunu söyler; nerede yanıldığını söylemez. Bu rapor her test sorusunu alıp doğru kaynağın listenin kaçıncı sırasında çıktığına bakıyor ve en kötü sıraladıklarını yakından inceliyor — ilginç hatalar orada.

47 test sorusundan 38 tanesinde doğru kaynak ilk sırada çıktı. Çıkmayan 9 soru aşağıda inceleniyor.

## Hataların çoğunun ardındaki iki örüntü

**Bir sayfa, cevap olmadan cevap gibi durabilir.** Soru kavramın adını vermek yerine bir belirtiyi tarif ettiğinde, arama çoğu zaman aynı ifadeyi paylaşan ama konusu farklı sayfalara gidiyor. Eğitimde iyi, gerçek veride kötü sonuç veren bir modelin nedenini sorduğunuzda, dengesiz veri setleriyle ilgili sayfalar öne çıkıyor — çünkü onlar "bir ölçüte göre iyi görünüyor ama pratikte başarısız" diline sahip — ve asıl overfitting'i anlatan bölümün önüne geçiyorlar.

**Geniş kapsamlı sayfalar, özel sayfaların önüne geçiyor.** Bazı sorularda geniş bir ders özeti, tam o kavram için yazılmış kısa sayfanın üstünde çıkıyor. Ders özeti terimi diğer birçok terimle birlikte andığından her şeye biraz benziyor; odaklı sayfa ise tek bir şeye çok benziyor. Listenin en tepesinde bazen genişlik kazanıyor.

İkisi de düzeltilecek bir hata değil. Her ikisi de metinleri bütün olarak karşılaştırmanın doğal sonucu; bunları bilmek, bu aramanın neyi doğru bulup neyi bulamayacağına dair gerçekçi bir beklenti veriyor.

## En kötü sıraladığı sorular

En kötüden başlayarak. Her soru için yalnızca ilk 3 sonuç gösteriliyor.

### Doğru sayfa listenin 12. sırasındaydı — notlardan farklı kelimelerle soruldu

**Soru:** Eğitim setinde çok iyi ama gerçek veride kötü sonuç veren bir model neyle açıklanır?  
**Beklenen kaynak:** cart-algoritmasi, cross-validation

| skor | sayfa | bölüm |
|---|---|---|
| 0.5703 | imbalanced-datasets | Neden bu ders var? |
| 0.5127 | dengesiz-veri-setleri | Neden accuracy yanıltır |
| 0.5077 | dengesiz-veri-setleri | Kritik kural — Resampling nereye uygulanır |

### Doğru sayfa listenin 10. sırasındaydı — notlardan farklı kelimelerle soruldu

**Soru:** Çıktıyı 0 ile 1 arasına sıkıştırıp olasılık gibi yorumlayan yöntem hangisi?  
**Beklenen kaynak:** lojistik-regresyon

| skor | sayfa | bölüm |
|---|---|---|
| 0.4952 | siniflandirma-metrikleri | Classification Threshold (Sınıflandırma Eşiği) |
| 0.4926 | olcumleme-problemleri | 3. Sorting Reviews (Yorum Sıralama) — "En faydalı yorum hangisi?" |
| 0.4892 | olcumleme-problemleri | Neden bu ders var? |

### Doğru sayfa listenin 7. sırasındaydı — notlardan farklı kelimelerle soruldu

**Soru:** İki tasarım varyantından hangisinin gerçekten daha iyi olduğuna nasıl karar veririm?  
**Beklenen kaynak:** istatistik-ab-testi

| skor | sayfa | bölüm |
|---|---|---|
| 0.3847 | olcumleme-problemleri | 4. A/B Testing — "Fark gerçek mi, şans mı?" |
| 0.3646 | wilson-lower-bound | Problem |
| 0.3627 | sql-veri-tipleri | Sık karıştırılan noktalar / Test sonrası notlar |

### Doğru sayfa listenin 3. sırasındaydı — notlardan farklı kelimelerle soruldu

**Soru:** Elimde etiket yok, müşterileri gruplara nasıl ayırabilirim?  
**Beklenen kaynak:** k-means, unsupervised-learning

| skor | sayfa | bölüm |
|---|---|---|
| 0.6030 | cluster-then-label | Neden yapılır |
| 0.5321 | cluster-then-label | Daha iyi cevap iskeleti |
| 0.5174 | cluster-then-label | None |

### Doğru sayfa listenin 3. sırasındaydı — notlardaki terimlerle soruldu

**Soru:** SQL'de char ile varchar arasında nasıl seçim yapılır?  
**Beklenen kaynak:** sql-veri-tipi-secimi

| skor | sayfa | bölüm |
|---|---|---|
| 0.7273 | sql-veri-tipleri | Sık karıştırılan noktalar / Test sonrası notlar |
| 0.6888 | sql-veri-tipleri-flashcards | None |
| 0.6692 | sql-veri-tipi-secimi | None **&larr; beklenen** |

### Doğru sayfa listenin 2. sırasındaydı — notlardaki terimlerle soruldu

**Soru:** Feature extraction'da binary/flag değişken nasıl türetilir?  
**Beklenen kaynak:** feature-extraction

| skor | sayfa | bölüm |
|---|---|---|
| 0.6572 | FEATURE-ENGINEERING | 5. Feature Extraction — "Veride görünmeyen ama var olan sinyali nasıl açığa çıkarırsın?" |
| 0.6439 | feature-extraction | 4 Kategori **&larr; beklenen** |
| 0.5813 | feature-extraction | None **&larr; beklenen** |

### Doğru sayfa listenin 2. sırasındaydı — notlardaki terimlerle soruldu

**Soru:** Ağırlıklı puanlamada zaman faktörü neden hesaba katılır?  
**Beklenen kaynak:** agirlikli-puanlama-ve-siralama

| skor | sayfa | bölüm |
|---|---|---|
| 0.6301 | olcumleme-problemleri | 1. Rating (Puanlama) — "Ortalama seni kandırır" |
| 0.5978 | agirlikli-puanlama-ve-siralama | Rating (Puanlama) **&larr; beklenen** |
| 0.5867 | agirlikli-puanlama-ve-siralama | None **&larr; beklenen** |

### Doğru sayfa listenin 2. sırasındaydı — notlardan farklı kelimelerle soruldu

**Soru:** Az oy almış ama yüksek puanlı bir ürünü listede nereye koymalıyım?  
**Beklenen kaynak:** agirlikli-puanlama-ve-siralama, wilson-lower-bound

| skor | sayfa | bölüm |
|---|---|---|
| 0.4530 | olcumleme-problemleri | 2. Sorting Products (Ürün Sıralama) — "Tek metrikle sıralama yanıltır" |
| 0.4515 | agirlikli-puanlama-ve-siralama | Yanlış anlamalar / tuzaklar **&larr; beklenen** |
| 0.4443 | wilson-lower-bound | Yanlış anlamalar / tuzaklar **&larr; beklenen** |

### Doğru sayfa listenin 2. sırasındaydı — Türkçe ve İngilizce terimler karışık

**Soru:** Pandas'ta missing value'ları fillna ile nasıl doldururum?  
**Beklenen kaynak:** eksik-deger-yontemleri, pandas-temel-operasyonlar

| skor | sayfa | bölüm |
|---|---|---|
| 0.7182 | FEATURE-ENGINEERING | 2. Missing Values (Eksik Değerler) — "Boş hücreyi nasıl doldurursun, yoksa doldurmamalı mısın?" |
| 0.6918 | eksik-deger-yontemleri | Yöntemler (basitten karmaşığa) **&larr; beklenen** |
| 0.5820 | eksik-deger-yontemleri | None **&larr; beklenen** |

## Doğru bulduğu sorular

Ayrıntısız liste. 38 sorunun hepsinde doğru kaynak ilk sırada.

| soru | nasıl soruldu |
|---|---|
| ROC eğrisi neden eşikten bağımsız bir metrik? | notlardaki terimlerle soruldu |
| Wilson Lower Bound ne işe yarar? | notlardaki terimlerle soruldu |
| RFM analizinde Recency, Frequency, Monetary neyi ölçer? | notlardaki terimlerle soruldu |
| CART algoritması nasıl if/else kural zincirine dönüşür? | notlardaki terimlerle soruldu |
| K-fold cross validation nedir ve neden holdout'tan daha güvenilir? | notlardaki terimlerle soruldu |
| PCA boyut indirgemeyi nasıl yapar? | notlardaki terimlerle soruldu |
| IQR yöntemiyle aykırı değerler nasıl tespit edilir? | notlardaki terimlerle soruldu |
| Association Rule Learning'de support, confidence ve lift ne anlama gelir? | notlardaki terimlerle soruldu |
| Gradient descent'te learning rate neyi kontrol eder? | notlardaki terimlerle soruldu |
| KNN neden 'lazy learner' olarak adlandırılır? | notlardaki terimlerle soruldu |
| Modelim %95 doğruluk veriyor ama işe yaramıyor, neden olabilir? | notlardan farklı kelimelerle soruldu |
| Kategorik bir sütunu modele sayısal olarak nasıl veririm? | notlardan farklı kelimelerle soruldu |
| Bir kullanıcının geçmiş alışverişine bakıp gelecekte ne kadar harcayacağını nasıl tahmin ederim? | notlardan farklı kelimelerle soruldu |
| Farklı büyüklükteki sayısal sütunları model için nasıl aynı ölçeğe getiririm? | notlardan farklı kelimelerle soruldu |
| Ağaçları paralel kurmakla sırayla kurmak arasındaki fark nedir? | birden fazla kaynak gerektiriyor |
| Precision, Recall ve F1 skoru arasındaki ilişki nedir, ROC-AUC ile nasıl farklılaşır? | birden fazla kaynak gerektiriyor |
| Denetimsiz öğrenmede kümeleme sonrası boyut indirgeme neden birlikte kullanılır? | birden fazla kaynak gerektiriyor |
| İçerik tabanlı ve işbirlikçi filtreleme öneri sistemleri nasıl farklılaşır? | birden fazla kaynak gerektiriyor |
| Eksik değerleri doldurmanın farklı yöntemleri nelerdir ve outlier tespitiyle nasıl ilişkilidir? | birden fazla kaynak gerektiriyor |
| Feature scaling yapmadan KNN çalıştırırsam ne olur? | Türkçe ve İngilizce terimler karışık |
| Voting classifier'da hard voting ile soft voting arasındaki fark nedir? | Türkçe ve İngilizce terimler karışık |
| Model persistence için joblib kullanırken training-serving skew nasıl önlenir? | Türkçe ve İngilizce terimler karışık |
| Doğrusal regresyonda intercept (b) terimi neyi ifade eder? | notlardaki terimlerle soruldu |
| Lojistik regresyon neden sigmoid fonksiyonu kullanır? | notlardaki terimlerle soruldu |
| MSE, RMSE ve MAE arasındaki fark nedir? | notlardaki terimlerle soruldu |
| Parametre ile hiperparametre arasındaki fark nedir? | notlardaki terimlerle soruldu |
| A/B testinde hipotez testi adımları nelerdir? | notlardaki terimlerle soruldu |
| Python'da list ve dict comprehension nasıl yazılır? | notlardaki terimlerle soruldu |
| Python'da list, tuple, set ve dictionary arasındaki farklar nelerdir? | notlardaki terimlerle soruldu |
| Pandas'ta groupby ile veri nasıl gruplanır? | notlardaki terimlerle soruldu |
| Fonksiyonel EDA yaklaşımı nedir? | notlardaki terimlerle soruldu |
| Sürekli bir sayı tahmin eden modelin hatasını nasıl ölçerim? | notlardan farklı kelimelerle soruldu |
| Modelin kendi öğrendiği değerler ile benim baştan ayarladıklarım nasıl ayrılır? | notlardan farklı kelimelerle soruldu |
| Aynı EDA adımlarını her projede tekrar yazmaktan nasıl kurtulurum? | notlardan farklı kelimelerle soruldu |
| Doğrusal regresyon ile lojistik regresyon ne zaman birbirinin yerine kullanılır? | birden fazla kaynak gerektiriyor |
| Yeni değişken türetmek ile mevcut değişkenleri ölçeklemek arasındaki fark nedir? | birden fazla kaynak gerektiriyor |
| Etiketsiz veriden sınıflandırma modeli kurmanın yolu nedir? | birden fazla kaynak gerektiriyor |
| Overfitting'i engellemek için hangi regularization yöntemleri var? | Türkçe ve İngilizce terimler karışık |
