# Kapsam Denetimi Ne Kadar İyi Çalışıyor?

Sistem cevap vermeden önce, sorunun bilgi tabanında karşılığı olup olmadığına karar veriyor. Bu kararı iki ayrı parça olarak ölçmek gerekiyor: alttaki skorun iki tür soruyu ne kadar ayırt edebildiği ve kullanılan belirli eşiğin ne kadar iyi çalıştığı.

İkisini ayrı tutmak önemli. Skorun kendisi grupları ayıramıyorsa hiçbir eşik bunu düzeltemez. Ayırabiliyorsa, kötü bir sonuç eşik sorunudur, model sorunu değil.

Ölçüm, notların kapsadığı 47 soru ve kapsamadığı 32 soru üzerinde yapıldı. Kapsam dışı sorular iki gruba ayrılmış: 12 tanesi daha önce bir kural denenirken kullanılmıştı, 20 tanesi ise hiçbir ayarlamada kullanılmayıp saklanmıştı. İkisini ayrı raporlamak, önceki ayarlamanın sonucu şişirip şişirmediğini gösteriyor.

Bu, threshold_selection.md'nin kullandığı veriden farklı olarak sabit bir soru seti: AUROC gibi bir sinyal-kalitesi sayısının her raporda aynı şeyi ifade etmesi için, data/gate_feedback.jsonl'da biriken düzeltmelerle birlikte değişmeden sabit kalıyor. Kullanılan eşiğin kendisi ise bu düzeltmeleri hesaba katıyor -- onları da içeren sayı için bkz. threshold_selection.md.

## Skor ikisini ayırt edebiliyor mu?

Bu ölçüt şunu soruyor: notların kapsadığı bir soru ile kapsamadığı bir soru seçilse, kapsanan olan ne sıklıkla daha yüksek skor alır? 0.5 skorun yazı-turadan farksız olduğu, 1.0 ise sıralamayı her zaman doğru yaptığı — yani bir yerde mükemmel bir eşik bulunduğu anlamına gelir.

| kapsam dışı grup | soru | skor |
|---|---|---|
| önceki ayarlamada kullanılan | 12 | 0.995 |
| hiç kullanılmayan | 20 | 0.969 |
| **hepsi birlikte** | 32 | **0.979** |

0.979 değeriyle skor iki grubu iyi ayırıyor ve saklanan grup, ayarlamada kullanılana yakın sonuç veriyor — yani bu kalite gerçek, o sorular üzerinde ayarlama yapmış olmanın bir yan etkisi değil.

## Kullanılan eşik nasıl çalışıyor

Aynı kararlara üç farklı bakış. *Yaptığı reddetmelerin kaçı doğruydu* ile *reddetmesi gereken sorulardan kaçını yakaladı* birbirine ters çalışıyor; üçüncü sütun ikisini tek bir sayıda dengeliyor.

| kapsam dışı grup | doğru olan reddetmeler | yakaladığı kapsam dışı | denge | doğru reddedilen | yanlışlıkla reddedilen gerçek soru | kaçırılan |
|---|---|---|---|---|---|---|
| önceki ayarlamada kullanılan | 0.857 | 1.000 | 0.923 | 12 | 2 | 0 |
| hiç kullanılmayan | 0.900 | 0.900 | 0.900 | 18 | 2 | 2 |
| hepsi birlikte | 0.938 | 0.938 | 0.938 | 30 | 2 | 2 |
## Daha çok cevaplamak, daha çok yanılmak demek

Olası her eşik ve yaptığı takas. *Cevaplanan*, sistemin yanıt verdiği soruların oranı; *hatalı cevap*, bu yanıtların içinde reddedilmesi gereken sorulara gidenlerin oranı. Eşiği düşürmek daha çok soruyu cevaplatıyor ve daha çoğunu yanlış yapıyor.

| eşik | cevaplanan | hatalı cevap | cevaplanan gerçek soru | cevaplanan kapsam dışı |
|---|---|---|---|---|
| 10.75 | %1 | %0 | 1/47 | 0/32 |
| 8.90 | %5 | %0 | 4/47 | 0/32 |
| 8.12 | %9 | %0 | 7/47 | 0/32 |
| 7.01 | %13 | %0 | 10/47 | 0/32 |
| 5.90 | %16 | %0 | 13/47 | 0/32 |
| 3.41 | %20 | %0 | 16/47 | 0/32 |
| 2.82 | %24 | %0 | 19/47 | 0/32 |
| 2.17 | %28 | %0 | 22/47 | 0/32 |
| 1.52 | %32 | %0 | 25/47 | 0/32 |
| 0.41 | %35 | %0 | 28/47 | 0/32 |
| -0.35 | %39 | %0 | 31/47 | 0/32 |
| -0.89 | %43 | %3 | 33/47 | 1/32 |
| -1.94 | %47 | %3 | 36/47 | 1/32 |
| -2.15 | %51 | %2 | 39/47 | 1/32 |
| -2.79 | %54 | %5 | 41/47 | 2/32 |
| -3.35 ← | %58 | %4 | 44/47 | 2/32 |
| -4.41 | %62 | %8 | 45/47 | 4/32 |
| -4.85 | %66 | %12 | 46/47 | 6/32 |
| -5.50 | %70 | %16 | 46/47 | 9/32 |
| -5.71 | %73 | %19 | 47/47 | 11/32 |
| -6.46 | %77 | %23 | 47/47 | 14/32 |
| -6.82 | %81 | %27 | 47/47 | 17/32 |
| -7.25 | %85 | %30 | 47/47 | 20/32 |
| -7.78 | %89 | %33 | 47/47 | 23/32 |
| -8.23 | %92 | %36 | 47/47 | 26/32 |
| -8.55 | %96 | %38 | 47/47 | 29/32 |
| -8.74 | %100 | %41 | 47/47 | 32/32 |

Kapsam dışı soruların hepsini reddetmek mümkün, ama bunun için eşiği -0.39 yapmak gerekiyor — o da 15 gerçek soruyu geri çeviriyor. Kullanılan ayar, cevaplaması gereken soruların çok daha fazlasını cevaplamak karşılığında birkaç hatayı kabul ediyor.


Ölçüt seçimi Wen ve ark., *Know Your Limits: A Survey of Abstention in Large Language Models*, TACL 2025 (13:529-556) çalışmasını izliyor; bu çalışma tek bir başarı yüzdesi yerine ayrım gücünün, hata oranlarının ve kapsam takasının birlikte raporlanmasını öneriyor.
