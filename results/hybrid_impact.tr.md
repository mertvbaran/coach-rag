# Hibrit Arama: Denendi ve Reddedildi

Sistem kaynakları anlama göre buluyor: soru ve metin parçası birer sayı dizisine çevriliyor, en yakın olanlar döndürülüyor. Bu yöntem sorunun farklı kelimelerle sorulmasını iyi kaldırıyor ama bazen tam terimi kaçırabiliyor. Anahtar kelime araması ise tam tersi: birebir kelime eşleşmesine bakıyor, başka bir şeye değil.

İkisini birleştirmek yaygın bir tavsiye — her birinin diğerinin kör noktasını kapatacağı düşüncesiyle. Buradaki ölçüm, bunun gerçekten işe yarayıp yaramadığına bakıyor.

47 soru üzerinde, `by_heading` indeksiyle ölçüldü.

## Üç yaklaşım

| yöntem | doğru kaynak 1. sırada | ilk 3'te | ilk 5'te | sıralama kalitesi |
|---|---|---|---|---|
| yalnızca anlama dayalı arama | **0.809** | 0.936 | 0.936 | **0.865** |
| ikisi eşit karışım | 0.723 | 0.872 | 0.915 | 0.798 |
| yalnızca anahtar kelime araması | 0.638 | 0.809 | 0.872 | 0.727 |

İlk sütun, doğru kaynağın ilk sıraya konduğu soruların oranı — en önemli ölçüt bu, çünkü insanlar en üstteki sonucu okuyor. Anlama dayalı arama 0.809, anahtar kelime araması 0.638 veriyor; ikisini karıştırmak ise iyi olanın üstüne çıkmak yerine altında kalıyor.

## Farklı bir karışım oranı işe yarar mı?

1.0 ağırlık, yalnızca anlama dayalı arama demek; değer düştükçe anahtar kelime aramasının payı artıyor.

| anlama dayalı aramanın ağırlığı | doğru kaynak 1. sırada | ilk 3'te | ilk 5'te | sıralama kalitesi |
|---|---|---|---|---|
| 1.0 (yalnızca anlam) | **0.809** | 0.936 | 0.936 | **0.865** |
| 0.3 | 0.702 | 0.851 | 0.915 | 0.784 |
| 0.5 | 0.723 | 0.872 | 0.915 | 0.798 |
| 0.7 | 0.745 | 0.915 | 0.936 | 0.827 |
| 0.9 | 0.766 | 0.936 | 0.936 | 0.844 |
## Neden burada işe yaramıyor

Hiçbir karışım, tek başına anlama dayalı aramayı geçemiyor. En yakını 0.9 ağırlığı (0.766) ve o da 0.809 değerinin altında kalıyor.

Sebep, üzerinde çalışılan metinlerin kendisi. Anahtar kelime araması, belgelerde nadir ve birebir eşleşen ifadeler olduğunda değer katar — ürün kodu, hata numarası, alışılmadık isimler gibi. Buradaki notlar ise tam tersi: aynı makine öğrenmesi kelime dağarcığını paylaşan birkaç düzine sayfa. Neredeyse her sayfada "model", "veri", "metrik" geçiyor; bu kelimelere bakarak eşleşme yapmak neredeyse hiçbir şeyi ayırt etmiyor, karışıma eklendiğinde ise güçlü sinyali sulandırıyor.

Sonuç varsayılmadı, ölçüldü ve kod değiştirilmedi: `query.py` hâlâ yalnızca anlama dayalı aramayı kullanıyor.
