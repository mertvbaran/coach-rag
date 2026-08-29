# Where the Search Gets It Wrong

A single accuracy figure says how often the search is right, not where it goes wrong. This report takes every test question, checks how far down the list the correct source appeared, and looks closely at the ones it ranked worst — those are where the interesting failures are.

Of 47 test questions, 38 put a correct source first. The 9 that did not are examined below.

## Two patterns behind most of the mistakes

**A page can sound like the answer without being it.** When a question describes a symptom instead of naming the concept, the search often lands on pages that share the phrasing but not the subject. Asking what explains a model that does well in training and badly in production brings up the pages about imbalanced data — they are full of "looks good on one measure, fails in practice" language — ahead of the section that actually covers overfitting.

**Broad pages crowd out specific ones.** Several questions rank a wide course summary above the short page written about exactly that concept. The summary mentions the term among many others, so it matches a little on everything; the focused page matches strongly on one thing. At the very top of the list, breadth sometimes wins.

Neither is a bug with a fix. Both follow from comparing whole passages at once, and knowing about them sets a realistic expectation of what this search will and will not get right.

## The questions it ranked worst

Worst first. Only the top 3 results are shown for each.

### The right page was 12th in the list — asked in different words than the notes use

**Question:** Eğitim setinde çok iyi ama gerçek veride kötü sonuç veren bir model neyle açıklanır?  
**Expected source:** cart-algoritmasi, cross-validation

| score | page | section |
|---|---|---|
| 0.5703 | imbalanced-datasets | Neden bu ders var? |
| 0.5127 | dengesiz-veri-setleri | Neden accuracy yanıltır |
| 0.5077 | dengesiz-veri-setleri | Kritik kural — Resampling nereye uygulanır |

### The right page was 10th in the list — asked in different words than the notes use

**Question:** Çıktıyı 0 ile 1 arasına sıkıştırıp olasılık gibi yorumlayan yöntem hangisi?  
**Expected source:** lojistik-regresyon

| score | page | section |
|---|---|---|
| 0.4952 | siniflandirma-metrikleri | Classification Threshold (Sınıflandırma Eşiği) |
| 0.4926 | olcumleme-problemleri | 3. Sorting Reviews (Yorum Sıralama) — "En faydalı yorum hangisi?" |
| 0.4892 | olcumleme-problemleri | Neden bu ders var? |

### The right page was 7th in the list — asked in different words than the notes use

**Question:** İki tasarım varyantından hangisinin gerçekten daha iyi olduğuna nasıl karar veririm?  
**Expected source:** istatistik-ab-testi

| score | page | section |
|---|---|---|
| 0.3847 | olcumleme-problemleri | 4. A/B Testing — "Fark gerçek mi, şans mı?" |
| 0.3646 | wilson-lower-bound | Problem |
| 0.3627 | sql-veri-tipleri | Sık karıştırılan noktalar / Test sonrası notlar |

### The right page was 3rd in the list — asked in different words than the notes use

**Question:** Elimde etiket yok, müşterileri gruplara nasıl ayırabilirim?  
**Expected source:** k-means, unsupervised-learning

| score | page | section |
|---|---|---|
| 0.6030 | cluster-then-label | Neden yapılır |
| 0.5321 | cluster-then-label | Daha iyi cevap iskeleti |
| 0.5174 | cluster-then-label | None |

### The right page was 3rd in the list — asked using the same words as the notes

**Question:** SQL'de char ile varchar arasında nasıl seçim yapılır?  
**Expected source:** sql-veri-tipi-secimi

| score | page | section |
|---|---|---|
| 0.7273 | sql-veri-tipleri | Sık karıştırılan noktalar / Test sonrası notlar |
| 0.6888 | sql-veri-tipleri-flashcards | None |
| 0.6692 | sql-veri-tipi-secimi | None **&larr; expected** |

### The right page was 2nd in the list — asked using the same words as the notes

**Question:** Feature extraction'da binary/flag değişken nasıl türetilir?  
**Expected source:** feature-extraction

| score | page | section |
|---|---|---|
| 0.6572 | FEATURE-ENGINEERING | 5. Feature Extraction — "Veride görünmeyen ama var olan sinyali nasıl açığa çıkarırsın?" |
| 0.6439 | feature-extraction | 4 Kategori **&larr; expected** |
| 0.5813 | feature-extraction | None **&larr; expected** |

### The right page was 2nd in the list — asked using the same words as the notes

**Question:** Ağırlıklı puanlamada zaman faktörü neden hesaba katılır?  
**Expected source:** agirlikli-puanlama-ve-siralama

| score | page | section |
|---|---|---|
| 0.6301 | olcumleme-problemleri | 1. Rating (Puanlama) — "Ortalama seni kandırır" |
| 0.5978 | agirlikli-puanlama-ve-siralama | Rating (Puanlama) **&larr; expected** |
| 0.5867 | agirlikli-puanlama-ve-siralama | None **&larr; expected** |

### The right page was 2nd in the list — asked in different words than the notes use

**Question:** Az oy almış ama yüksek puanlı bir ürünü listede nereye koymalıyım?  
**Expected source:** agirlikli-puanlama-ve-siralama, wilson-lower-bound

| score | page | section |
|---|---|---|
| 0.4530 | olcumleme-problemleri | 2. Sorting Products (Ürün Sıralama) — "Tek metrikle sıralama yanıltır" |
| 0.4515 | agirlikli-puanlama-ve-siralama | Yanlış anlamalar / tuzaklar **&larr; expected** |
| 0.4443 | wilson-lower-bound | Yanlış anlamalar / tuzaklar **&larr; expected** |

### The right page was 2nd in the list — mixes Turkish and English terms

**Question:** Pandas'ta missing value'ları fillna ile nasıl doldururum?  
**Expected source:** eksik-deger-yontemleri, pandas-temel-operasyonlar

| score | page | section |
|---|---|---|
| 0.7182 | FEATURE-ENGINEERING | 2. Missing Values (Eksik Değerler) — "Boş hücreyi nasıl doldurursun, yoksa doldurmamalı mısın?" |
| 0.6918 | eksik-deger-yontemleri | Yöntemler (basitten karmaşığa) **&larr; expected** |
| 0.5820 | eksik-deger-yontemleri | None **&larr; expected** |

## The questions it got right

Listed without detail. All 38 ranked a correct source first.

| question | how it was asked |
|---|---|
| ROC eğrisi neden eşikten bağımsız bir metrik? | asked using the same words as the notes |
| Wilson Lower Bound ne işe yarar? | asked using the same words as the notes |
| RFM analizinde Recency, Frequency, Monetary neyi ölçer? | asked using the same words as the notes |
| CART algoritması nasıl if/else kural zincirine dönüşür? | asked using the same words as the notes |
| K-fold cross validation nedir ve neden holdout'tan daha güvenilir? | asked using the same words as the notes |
| PCA boyut indirgemeyi nasıl yapar? | asked using the same words as the notes |
| IQR yöntemiyle aykırı değerler nasıl tespit edilir? | asked using the same words as the notes |
| Association Rule Learning'de support, confidence ve lift ne anlama gelir? | asked using the same words as the notes |
| Gradient descent'te learning rate neyi kontrol eder? | asked using the same words as the notes |
| KNN neden 'lazy learner' olarak adlandırılır? | asked using the same words as the notes |
| Modelim %95 doğruluk veriyor ama işe yaramıyor, neden olabilir? | asked in different words than the notes use |
| Kategorik bir sütunu modele sayısal olarak nasıl veririm? | asked in different words than the notes use |
| Bir kullanıcının geçmiş alışverişine bakıp gelecekte ne kadar harcayacağını nasıl tahmin ederim? | asked in different words than the notes use |
| Farklı büyüklükteki sayısal sütunları model için nasıl aynı ölçeğe getiririm? | asked in different words than the notes use |
| Ağaçları paralel kurmakla sırayla kurmak arasındaki fark nedir? | needs more than one source |
| Precision, Recall ve F1 skoru arasındaki ilişki nedir, ROC-AUC ile nasıl farklılaşır? | needs more than one source |
| Denetimsiz öğrenmede kümeleme sonrası boyut indirgeme neden birlikte kullanılır? | needs more than one source |
| İçerik tabanlı ve işbirlikçi filtreleme öneri sistemleri nasıl farklılaşır? | needs more than one source |
| Eksik değerleri doldurmanın farklı yöntemleri nelerdir ve outlier tespitiyle nasıl ilişkilidir? | needs more than one source |
| Feature scaling yapmadan KNN çalıştırırsam ne olur? | mixes Turkish and English terms |
| Voting classifier'da hard voting ile soft voting arasındaki fark nedir? | mixes Turkish and English terms |
| Model persistence için joblib kullanırken training-serving skew nasıl önlenir? | mixes Turkish and English terms |
| Doğrusal regresyonda intercept (b) terimi neyi ifade eder? | asked using the same words as the notes |
| Lojistik regresyon neden sigmoid fonksiyonu kullanır? | asked using the same words as the notes |
| MSE, RMSE ve MAE arasındaki fark nedir? | asked using the same words as the notes |
| Parametre ile hiperparametre arasındaki fark nedir? | asked using the same words as the notes |
| A/B testinde hipotez testi adımları nelerdir? | asked using the same words as the notes |
| Python'da list ve dict comprehension nasıl yazılır? | asked using the same words as the notes |
| Python'da list, tuple, set ve dictionary arasındaki farklar nelerdir? | asked using the same words as the notes |
| Pandas'ta groupby ile veri nasıl gruplanır? | asked using the same words as the notes |
| Fonksiyonel EDA yaklaşımı nedir? | asked using the same words as the notes |
| Sürekli bir sayı tahmin eden modelin hatasını nasıl ölçerim? | asked in different words than the notes use |
| Modelin kendi öğrendiği değerler ile benim baştan ayarladıklarım nasıl ayrılır? | asked in different words than the notes use |
| Aynı EDA adımlarını her projede tekrar yazmaktan nasıl kurtulurum? | asked in different words than the notes use |
| Doğrusal regresyon ile lojistik regresyon ne zaman birbirinin yerine kullanılır? | needs more than one source |
| Yeni değişken türetmek ile mevcut değişkenleri ölçeklemek arasındaki fark nedir? | needs more than one source |
| Etiketsiz veriden sınıflandırma modeli kurmanın yolu nedir? | needs more than one source |
| Overfitting'i engellemek için hangi regularization yöntemleri var? | mixes Turkish and English terms |
