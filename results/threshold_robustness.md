# Is the Threshold Robust to Rephrasing?

The out-of-scope gate (threshold -3.68, see threshold_selection.md for how it was fitted) was checked against one fixed wording per out-of-scope topic during calibration. This asks a different question: does rephrasing the same question -- same topic, same intent, different words -- change the gate's decision?

## Kubernetes network policy

| question | CE score | in scope? |
|---|---|---|
| Kubernetes pod network policy nasıl tanımlanır? | -6.82 | correctly rejected |
| Kubernetes'te pod'lar arası network policy nasıl tanımlanır? | -5.46 | correctly rejected |
| Kubernetes'te pod'lar arasındaki ağ trafiğini nasıl kısıtlarım? | -5.71 | correctly rejected |

Spread across paraphrases: 1.36 (scores range -6.82 to -5.46)

## React useEffect

| question | CE score | in scope? |
|---|---|---|
| React useEffect hook ne zaman tetiklenir? | -8.63 | correctly rejected |
| React'te useEffect hook'u ne zaman çalışır? | -8.74 | correctly rejected |
| useEffect'in bağımlılık dizisi (dependency array) nasıl çalışır? | -7.86 | correctly rejected |

Spread across paraphrases: 0.88 (scores range -8.74 to -7.86)

## Blockchain consensus

| question | CE score | in scope? |
|---|---|---|
| Blockchain konsensüs algoritmaları nelerdir? | -5.70 | correctly rejected |
| Blockchain'de konsensüs nasıl sağlanır? | -4.38 | correctly rejected |
| Proof of work ile proof of stake arasındaki fark nedir? | -6.69 | correctly rejected |

Spread across paraphrases: 2.31 (scores range -6.69 to -4.38)

## Transformer attention

| question | CE score | in scope? |
|---|---|---|
| Transformer mimarisinde self-attention nasıl çalışır? | -6.46 | correctly rejected |
| Transformer'larda self-attention mekanizması nedir? | -7.08 | correctly rejected |
| Attention is all you need makalesindeki temel fikir nedir? | -6.33 | correctly rejected |

Spread across paraphrases: 0.75 (scores range -7.08 to -6.33)

## Interpretation

All paraphrases were correctly rejected in this sample -- the threshold held up across rewordings here, though the earlier interactive finding (Kubernetes phrasing scoring -5.46 against the threshold then in force) shows it is not universally robust.
