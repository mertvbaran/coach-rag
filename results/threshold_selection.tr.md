# Eşik Nasıl Belirlendi?

Sistem, bilgi tabanının kapsamadığı bir soru geldiğini düşündüğünde cevap vermeyi reddediyor. Bu karar tek bir sayıya dayanıyor: bir skor ve altına düşüldüğünde sorunun geri çevrildiği bir eşik.

Bu eşiği gözle seçmek kolayca yanlış gidiyor — ilk denemede gerçek bir sorunun aldığı en düşük skorun hemen altına konmuştu; seçildiği sorular üzerinde güvenli görünüyordu ama pratikte alakasız soruların dörtte birini içeri alıyordu. Bu rapor eşiği, bir hatanın maliyetini açıkça yazıp gerisini veriye bırakarak seçiyor.

Ölçüm, notların kapsadığı 47 soru ve kapsamadığı 33 soru üzerinde yapıldı. İki hata türü farklı ağırlıklandırıldı: kapsam dışı bir soruyu cevaplamak 2.0 puan, gerçek bir soruyu reddetmek 1.0 puan — yanlış cevap gereksiz reddetmeden daha maliyetli, çünkü reddedilen kişi soruyu yeniden sorabilir ama kendinden emin görünen yanlış bir cevabın yanlış olduğunu anlayamaz.

Bunlardan 1 tanesi arayüz üzerinden düzeltilen kararlardan geliyor — uydurulmuş test soruları değil, sistemin gerçek kullanımda yanıldığı sorular.

## Verinin seçtiği eşik

Olası her eşik denenip toplam maliyeti en düşük olan seçildiğinde **-3.68** çıkıyor. Bu ayarda 2 kapsam dışı soru cevaplanıyor, 2 gerçek soru reddediliyor.

## Seçilmediği sorularda da tutuyor mu?

Bir eşik, üzerinde ayarlandığı soru kümesinde her zaman iyi görünür. Dürüst bir sayı elde etmek için sorular 5 gruba ayrılıyor: eşik 4 grupta hesaplanıp dışarıda bırakılan grupta test ediliyor ve bu 5 kez tekrarlanıyor. Aşağıdaki her hata, eşiğin hiç görmediği bir soruda.

| tur | diğerlerinde hesaplanan eşik | cevaplanan kapsam dışı | reddedilen gerçek soru |
|---|---|---|---|
| 1 | -2.99 | 0 | 3 |
| 2 | -3.68 | 1 | 0 |
| 3 | -3.68 | 1 | 0 |
| 4 | -3.94 | 1 | 1 |
| 5 | -3.68 | 0 | 1 |
| **toplam** | ortalama -3.59 | **33 sorudan 3** | **47 sorudan 5** |

Hangi sorular dışarıda bırakılırsa bırakılsın eşik -3.94 ile -2.99 arasında kalıyor — verinin genel biçimini takip ediyor, tek bir sorunun üzerinde dengede durmuyor.

## Yanlış cevabın maliyeti farklı olsaydı?

Yanlış cevabı gereksiz reddetmenin iki katı ağırlıkta saymak bir tercih. Aynı yöntemin başka ağırlıklarda ne verdiği aşağıda — tercih varsayılmak yerine görülebilsin diye.

| yanlış cevabın yanlış reddetmeye oranı | eşik | cevaplanan kapsam dışı | reddedilen gerçek soru |
|---|---|---|---|
| 1:1 | -3.68 | 2/33 | 2/47 |
| 2:1 ← | -3.68 | 2/33 | 2/47 |
| 3:1 | -3.68 | 2/33 | 2/47 |
| 5:1 | -3.08 | 2/33 | 6/47 |
| 10:1 | -0.63 | 0/33 | 15/47 |

Ok, kullanılan ayarı gösteriyor. İki hatayı eşit saymak da, yanlış cevabı üç kat ağır saymak da aynı eşiği veriyor — seçim bu tercihin üzerinde dengede durmuyor.

## Skoru yüzdeye çevirmek

Ham skor tek başına bir şey ifade etmiyor — -3.68 yakın mı, uzak mı? Skorlara küçük bir eğri uydurmak onları okunabilir bir şeye çeviriyor: sorunun kapsam içinde olma ihtimali. Böylece eşik, çıplak bir sayı yerine "%50 güvenin üstünde cevapla" biçiminde ifade edilebiliyor.

| güven eşiği | ham skor karşılığı | cevaplanan kapsam dışı | reddedilen gerçek soru |
|---|---|---|---|
| %30 | -4.66 | 6/33 | 2/47 |
| %50 | -3.58 | 2/33 | 3/47 |
| %70 | -2.50 | 2/33 | 7/47 |
| %90 | -0.79 | 1/33 | 15/47 |
### Yüzdeler gerçekten söyledikleri anlama geliyor mu?

Sorular, aldıkları güven değerine göre gruplanıp her grubun gerçekte ne kadarının kapsam içinde olduğuna bakılıyor. Son iki sütunun birbirini takip etmesi bekleniyor.

| verilen güven | soru | ortalama güven | gerçekte kapsam içi |
|---|---|---|---|
| %0–%20 | 25 | %7 | %4 |
| %20–%40 | 7 | %29 | %14 |
| %40–%60 | 5 | %50 | %80 |
| %60–%80 | 7 | %73 | %86 |
| %80–%100 | 36 | %97 | %97 |

Her grupta yalnızca birkaç soru olduğu için bu kesin bir ölçüm değil, bir sağlama — ama iki sütun birlikte hareket ediyor ve olması gereken de bu.
