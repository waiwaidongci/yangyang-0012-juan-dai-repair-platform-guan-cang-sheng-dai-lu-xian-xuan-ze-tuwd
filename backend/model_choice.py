"""Grouped validation and explanations for archive routing."""
from collections import Counter
from math import sqrt
from statistics import mean, pstdev

FEATURES = ("dropout", "snaps", "residue")
ROUTE_LABELS = {"clean":"表面清洁复核","mend":"接带点检","rehouse":"换盘与低张力复核"}

def threshold(row, _training):
    if row["snaps"] >= 4:
        return "mend", "脉冲断点数不少于 4"
    if row["dropout"] >= 12:
        return "rehouse", "间断段数不少于 12"
    return "clean", "间断、脉冲断点均未达到改路线门槛"

def nearest(row, training):
    scales = {key:pstdev(sample[key] for sample in training) or 1 for key in FEATURES}
    def distance(other):
        return sqrt(sum(((row[key]-other[key])/scales[key])**2 for key in FEATURES))
    neighbors = sorted(training, key=lambda other:(distance(other),other["code"]))[:3]
    counts = Counter(sample["known_route"] for sample in neighbors)
    chosen = max(neighbors, key=lambda sample:counts[sample["known_route"]])["known_route"]
    evidence = "、".join(f'{sample["code"]} {ROUTE_LABELS[sample["known_route"]]}' for sample in neighbors)
    return chosen, "三近邻：" + evidence

METHODS = {"rule":threshold,"knn":nearest}

def compare(rows):
    folds = sorted({row["fold"] for row in rows})
    errors = {name:{} for name in METHODS}
    for fold in folds:
        training = [row for row in rows if row["fold"] != fold]
        validation = [row for row in rows if row["fold"] == fold]
        for name, predict in METHODS.items():
            accuracy = mean(predict(row,training)[0] == row["known_route"] for row in validation)
            errors[name][str(fold)] = round(accuracy,4)
    overall = {name:round(mean(scores.values()),4) for name,scores in errors.items()}
    best = max(overall, key=overall.get) # Ordered rule first on a tie.
    return {"folds":errors,"accuracy":overall,"selected":best}
