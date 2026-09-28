"""Precision/recall of the improvement rule (85-abstract sample) and paired result for the 134 full texts."""
import math
import pandas as pd
from pathlib import Path
D = Path(__file__).resolve().parent / "data"

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * p, 1), round(100 * (c - h), 1), round(100 * (c + h), 1)

a = pd.read_csv(D / "hand_labels_85.csv")
ct = pd.crosstab(a.rule_flag, a.label); print(ct)
tp, fp = ct.loc["improvement", "Y"], ct.loc["improvement", "N"]
fn, tn = ct.loc["none", "Y"], ct.loc["none", "N"]
p, fo = tp / (tp + fp), fn / (fn + tn)
print("precision % (CI):", wilson(tp, tp + fp))
print("estimated recall %:", round(100 * 0.727 * p / (0.727 * p + 0.273 * fo), 1))
print("estimated share of 4,228 abstracts with explicit claim %:", round(100 * (0.727 * p + 0.273 * fo), 1))

b = pd.read_csv(D / "hand_labels_134.csv")
print(pd.crosstab(b.rule_flag, b.label))
y = b[b.label == "Y"]
print("explicit claims:", wilson(len(y), len(b)))
print("claimers reporting an own green-metric value:", int((y.metric_verdict == "genuine").sum()), "of", len(y))
