# Genel Bakış

Kişisel bir bilgi tabanı üzerinde çalışan bir arama aracı. Gündelik dille bir soru sorup cevabı içeren bölümleri kaynağıyla birlikte alıyorsunuz. Her şey kurulu olduğu makinede çalışıyor — hiçbir metin dışarı gönderilmiyor.

## Nasıl çalışıyor

Sıradan arama kelimeleri eşleştirir. Bu ise anlamı eşleştiriyor: notlardaki her metin parçası, ne anlattığını temsil eden bir sayı dizisine çevriliyor; soru da aynı şekilde çevriliyor ve en yakın parçalar geri geliyor. Notlardan farklı kelimelerle sorulmuş bir soru bile onları bulabiliyor.

Koleksiyon 91 dosyadan oluşuyor ve bölüm başlıklarından 319 parçaya ayrılmış durumda.

## Ne kadar iyi çalışıyor

İçeriğe göre yazılmış 57 soru üzerinde ölçüldü: 47 tanesinin doğru kaynağı biliniyor, 10 tanesi ise bilerek bilgi tabanında hiç geçmeyen konularda.

| | sonuç |
|---|---|
| doğru kaynak ilk sırada | soruların **%81**'i |
| aynısı, belge yapısı kullanılmadan | %72 |
| kapsanan ve kapsanmayan soruları ayırt etme | 1.0 üzerinden **0.979** |

İlk iki satır arasındaki farkın büyük kısmı, belgeleri kelime sayısına göre değil başlıklarına göre bölmekten geliyor — aynı notlar, farklı kesilmiş.

## Ne zaman cevap vermeyeceğini bilmek

Arama her zaman en yakın eşleşmesini döndürür — bilgi tabanıyla hiç ilgisi olmayan bir soru için bile. Bu yüzden sistem cevap vermeden önce sorunun kapsanıp kapsanmadığını denetliyor ve kapsanmıyorsa bunu söylüyor.

Bu denetimi doğru kurmak üç deneme aldı. Basit bir benzerlik eşiği işe yaramadı — başka teknik alanlardan gelen sorular gerçek sorular kadar yüksek skor alıyor. Soruyu ve metni birlikte okuyan ikinci bir model işe yaradı, ama yalnızca bu karar için: sonuçları yeniden sıralamak için kullanmak onları kötüleştirdi. Eşiğin kendisi ise önce gözle seçilmişti ve soru farklı kelimelerle sorulduğunda kararını değiştirdiği ortaya çıktı; şimdi veriden hesaplanıyor (-3.68) ve hesaplanmadığı sorularla sınanıyor.

## İşe yaramayanlar

Üç fikir denendi, ölçüldü ve bırakıldı. Raporlarda tutuluyorlar, çünkü ölçülmüş bir başarısızlık, sınanmamış bir varsayımdan daha değerli.

- **Anlama dayalı aramayla anahtar kelime aramasını birleştirmek.** Yaygın bir tavsiye ama denenen her karışım oranında sonuçları kötüleştirdi. Bu notların hepsi aynı kelime dağarcığını paylaştığından, kelime eşleşmesi neredeyse hiçbir şeyi ayırt etmiyor.
- **Sonuçları ikinci bir modelle yeniden sıralamak.** İlk sıra doğruluğunu belirgin şekilde düşürdü. O model uzun ve açıklayıcı metinleri tercih ediyor, bu notlar ise bilinçli olarak kısa ve odaklı.
- **Bir kuralı mükemmel skor verene kadar ayarlamak.** Verdi — ama yalnızca ayarlandığı sorularda; saklanan sorularda başarısız oldu. Dürüst sayının, seçimin yapılmadığı veride ölçülen sayı olduğunun hatırlatıcısı.

## Nereye bakmalı

Bu sekmedeki diğer raporlar bunların her birini açıyor:

- **Metni nasıl bölmeli?** — yukarıdaki sayıların arkasındaki karşılaştırma.
- **Aramanın yanıldığı yerler** — en kötü sıraladığı sorular ve arkalarındaki iki örüntü.
- **Hibrit arama** ve **Yeniden sıralama** — reddedilen iki fikir ve ölçümleri.
- **Basit eşik neden yetmedi**, **Eşik nasıl belirlendi**, **Eşik farklı ifadelere dayanıklı mı?** ve **Kapsam denetiminin ölçümü** — cevapla-ya da reddet kararının tüm hikayesi.
