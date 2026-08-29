# Basit Bir Eşik Neden Yetmedi?

Arama her zaman bir şey döndürür. Notlarda hiç geçmeyen bir konuyu sorduğunuzda bile en yakın beş tahminini verir ve bunların alakasız olduğuna dair hiçbir işaret göstermez.

Akla gelen ilk çözüm bir eşik koymak: her sonucun 0 ile 1 arasında bir benzerlik skoru var, en iyi skor çok düşükse cevap vermeyi reddet. Bu rapor, böyle bir eşiğin gerçekten işe yarayıp yaramadığını test ediyor.

## Skorlar nasıl dağılıyor

Üç tür soru ve her birinin en iyi eşleşmesinin aldığı benzerlik skoru. Bir eşiğin işe yaraması için bu grupların birbirinden ayrılması gerekir.

| soru türü | adet | en düşük | en yüksek | ortalama |
|---|---|---|---|---|
| notlarda işlenen konular | 47 | 0.335 | 0.801 | 0.610 |
| kapsam dışı, test setinden | 10 | 0.242 | 0.450 | 0.343 |
| kapsam dışı, başka teknik alanlar | 4 | 0.339 | 0.444 | 0.391 |
| kapsam dışı, günlük konular | 6 | 0.219 | 0.427 | 0.292 |

Aralıklar üst üste biniyor. Notlarda işlenen sorular 0.335 kadar aşağı inebiliyor, alakasız teknik sorular ise 0.444 kadar yukarı çıkabiliyor — yani ikisini temiz şekilde ayıran bir çizgi yok.

## Her eşik ve maliyeti

İki hata türü birbirinin tersi yönde çekiyor: katı bir eşik gerçek soruları geri çeviriyor, gevşek bir eşik alakasızları içeri alıyor.

| eşik | yanlışlıkla reddedilen gerçek soru | yanlışlıkla kabul edilen alakasız soru |
|---|---|---|
| 0.30 | 0/47 | 14/20 |
| 0.35 | 1/47 | 9/20 |
| 0.38 | 2/47 | 8/20 |
| 0.40 | 3/47 | 4/20 |
| 0.42 | 4/47 | 4/20 |
| 0.45 | 4/47 | 0/20 |
| 0.50 | 10/47 | 0/20 |
## Bu ne anlama geliyor

**Günlük soruları yakalamak kolay.** Hava durumu, yemek, tarih — bunlar notlarla hiçbir kelime paylaşmıyor, düşük skor alıyorlar ve bir eşik onları güvenilir şekilde geri çeviriyor.

**Başka teknik alanların soruları değil.** Kubernetes, React, Blockchain — bunlar gerçek sorularla aynı aralıkta skor alıyor, çünkü aynı üslupla yazılmışlar: teknik anlatım, benzer cümle yapıları, "model", "sistem", "veri" gibi örtüşen kelimeler. Bir yemek tarifi sorusu bile öneri sistemleri sayfalarıyla eşleşti, çünkü *tarif* ve *öneri* modelin anlam haritasında birbirine yakın duruyor.

**Yani tek bir eşik yetmiyor.** Teknik soruları dışarıda bırakacak kadar sıkarsanız gerçek soruları reddetmeye başlıyor; gerçek soruları içeri alacak kadar gevşetirseniz teknik olanlar da giriyor. Zor vakaları yakalamak için aynı sinyalin daha iyi bir sayısı değil, farklı bir sinyal gerekiyor — *eşik nasıl belirlendi* raporu bunu kuruyor.
