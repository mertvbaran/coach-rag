# İkinci Bir Modelle Yeniden Sıralama: Denendi ve Reddedildi

Buradaki arama tek adımda çalışıyor: her metin parçası önceden sayılara çevriliyor, soruya en yakın olanlar döndürülüyor. Bu hızlı bir yöntem ama karşılaştırma dolaylı — soru ile metin ayrı ayrı ölçülüp sonra kıyaslanıyor.

İkinci tür bir model ise soruyu ve metni *birlikte* okuyup ne kadar örtüştüklerine karar veriyor. Çok daha yavaş olduğu için tüm belgeleri puanlayamaz, ama ilk birkaç sonucu yeniden sıralayabilir. Genel beklenti bunun sıralamayı iyileştirmesi. Buradaki ölçüm, gerçekten iyileştirip iyileştirmediğine bakıyor.

## Yeniden sıralama öncesi ve sonrası sıralama kalitesi

Aşağı ok, yeniden sıralamanın o ölçütü kötüleştirdiği anlamına geliyor.

| chunker | soru | doğru kaynak 1. sırada: önce → sonra | sıralama kalitesi: önce → sonra |
|---|---|---|---|
| whole_doc | 47 | 0.745 → 0.745 → | 0.840 → 0.846 ↑ |
| by_heading | 47 | 0.809 → 0.596 ↓ | 0.870 → 0.762 ↓ |

**Sonucu kötüleştiriyor.** Sistemin fiilen kullandığı indekste, doğru cevabın ilk sıraya konduğu soruların oranı 0.809 değerinden 0.596 değerine düşüyor.

Hangi cevapların değiştiğine bakınca tutarlı bir örüntü çıkıyor: ikinci model uzun ve açıklayıcı metinleri — soru-cevap biçimindeki flashcard sayfalarını ve geniş ders özetlerini — tam o kavram için yazılmış kısa ve odaklı sayfaya tercih ediyor. Bir örnekte soru "support, confidence, lift" kavramlarını soruyor; bu terimleri birebir kullanan sayfa özgün aramada ilk sıradayken, yeniden sıralama onun üstüne genel bir flashcard sayfasını çıkarıyor.

Bu tercih rastgele değil. Bu tür modeller genellikle web arama verisiyle eğitiliyor ve orada daha iyi cevap gerçekten de çoğu zaman daha uzun, daha açıklayıcı olan oluyor. Buradaki notlar ise tam tersi: sayfa başına tek fikir, bilinçli olarak kısa. Modelin eğitimi, bu sayfaların yazılma biçimine ters düşüyor.

## İkinci model nerede işe yarıyor

Sonuçları yeniden sıralamak bu model için yanlış görevmiş. Bir sorunun kapsam içinde olup olmadığına karar vermek ise doğru görev çıktı.

Skoru -3.68 değerinin altına düştüğünde cevap vermeyi reddetmek, notların hakkında hiçbir şey söylemediği 10 sorudan 8 tanesini doğru şekilde geri çeviriyor. Özgün arama, basit bir benzerlik eşiğiyle 10 sorudan 0 tanesini yakalayabiliyor.

Bu yüzden model yalnızca bu iş için kullanılıyor: sıralamaya hiç dokunulmuyor, ikinci model sadece uyarı gösterilip gösterilmeyeceğine karar veriyor. İki ayrı görev ve birinde iyi olan bir model, otomatik olarak diğerinde de iyi değil.
