# Eşik Farklı İfadelere Dayanıklı mı?

Kapsam-dışı denetimi (eşik -3.68, nasıl hesaplandığı için bkz. threshold_selection.md) kalibrasyon sırasında kapsam dışı her konu için tek bir sabit ifadeyle sınanmıştı. Burada farklı bir soru soruluyor: aynı soru farklı kelimelerle sorulduğunda -- aynı konu, aynı niyet, farklı kelimeler -- denetimin kararı değişiyor mu?

## Kubernetes network policy

| soru | CE skoru | kapsamda mı? |
|---|---|---|
| Kubernetes pod network policy nasıl tanımlanır? | -6.82 | doğru şekilde reddedildi |
| Kubernetes'te pod'lar arası network policy nasıl tanımlanır? | -5.46 | doğru şekilde reddedildi |
| Kubernetes'te pod'lar arasındaki ağ trafiğini nasıl kısıtlarım? | -5.71 | doğru şekilde reddedildi |

İfadeler arası fark: 1.36 (skorlar -6.82 ile -5.46 arasında)

## React useEffect

| soru | CE skoru | kapsamda mı? |
|---|---|---|
| React useEffect hook ne zaman tetiklenir? | -8.63 | doğru şekilde reddedildi |
| React'te useEffect hook'u ne zaman çalışır? | -8.74 | doğru şekilde reddedildi |
| useEffect'in bağımlılık dizisi (dependency array) nasıl çalışır? | -7.86 | doğru şekilde reddedildi |

İfadeler arası fark: 0.88 (skorlar -8.74 ile -7.86 arasında)

## Blockchain consensus

| soru | CE skoru | kapsamda mı? |
|---|---|---|
| Blockchain konsensüs algoritmaları nelerdir? | -5.70 | doğru şekilde reddedildi |
| Blockchain'de konsensüs nasıl sağlanır? | -4.38 | doğru şekilde reddedildi |
| Proof of work ile proof of stake arasındaki fark nedir? | -6.69 | doğru şekilde reddedildi |

İfadeler arası fark: 2.31 (skorlar -6.69 ile -4.38 arasında)

## Transformer attention

| soru | CE skoru | kapsamda mı? |
|---|---|---|
| Transformer mimarisinde self-attention nasıl çalışır? | -6.46 | doğru şekilde reddedildi |
| Transformer'larda self-attention mekanizması nedir? | -7.08 | doğru şekilde reddedildi |
| Attention is all you need makalesindeki temel fikir nedir? | -6.33 | doğru şekilde reddedildi |

İfadeler arası fark: 0.75 (skorlar -7.08 ile -6.33 arasında)

## Yorum

Bu örnekteki tüm ifadeler doğru şekilde reddedildi -- eşik burada farklı ifadelere karşı dayanıklı çıktı, ama daha önceki canlı kullanım bulgusu (Kubernetes ifadesinin o zamanki eşiğe karşı -5.46 alması) eşiğin evrensel olarak dayanıklı olmadığını gösteriyor.
