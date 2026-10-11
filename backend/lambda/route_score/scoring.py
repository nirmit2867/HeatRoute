"""Transparent Heat Exposure Score (see docs/assumptions.md). Estimated environmental index, not medical."""
import json
import os
from decimal import Decimal

WEIGHTS = {"temperature": .25, "solar": .20, "surface": .15, "duration": .20}
RELIEF_WEIGHTS = {"shade_relief": .10, "vegetation_relief": .05, "wind_relief": .05}
LABELS = [(20, "Very Low"), (40, "Low"), (60, "Moderate"), (80, "High"), (100, "Very High")]
PROFILES = {"pedestrian": 1.00, "cyclist": 1.05, "outdoor_worker": 1.10}
MIN_SAVING = 15   # score points a cooler route must save...
MAX_EXTRA = 10    # ...for at most this many extra minutes
_cache = None


def label(score):
    return next(name for hi, name in LABELS if score <= hi)


def _num(x):
    if isinstance(x, Decimal):
        return float(x)
    if isinstance(x, list):
        return [_num(i) for i in x]
    if isinstance(x, dict):
        return {k: _num(v) for k, v in x.items()}
    return x


def _from_file():
    with open(os.path.join(os.path.dirname(__file__), "demo_heat_data.json")) as f:
        return json.load(f)


def _from_dynamo(table_name):
    import boto3
    table, items, kw = boto3.resource("dynamodb").Table(table_name), [], {}
    while True:
        r = table.scan(**kw)
        items += r["Items"]
        if "LastEvaluatedKey" not in r:
            break
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    data, routes = {"meta": {}, "buckets": {}}, {}
    for i in _num(items):
        if i["kind"] == "meta":
            data["meta"] = json.loads(i["json"])
        elif i["kind"] == "bucket":
            data["buckets"][i["cell_id"].split("#", 1)[1]] = i
        else:
            seg = dict(i, id=i["cell_id"], path=json.loads(i["path"]))
            r = routes.setdefault(i["route_id"], {"id": i["route_id"], "name": i["route_name"],
                                                  "kind": i["route_kind"], "segments": []})
            r["segments"].append(seg)
    for r in routes.values():
        r["segments"].sort(key=lambda s: s["order"])
    data["routes"] = sorted(routes.values(), key=lambda r: r["id"])
    return data


def load_data():
    global _cache
    if _cache is None:
        table = os.environ.get("HEATCELLS_TABLE")
        _cache = _from_dynamo(table) if table else _from_file()
    return _cache


def bucket_for(t):
    h = int(t.split(":")[0])
    return "09:00" if h < 11 else "13:00" if h < 15 else "17:00"


def _factors(segs, b, total_min):
    tot = sum(s["minutes"] for s in segs)

    def avg(fn):
        return sum(fn(s) * s["minutes"] for s in segs) / tot

    veg = avg(lambda s: s["veg"])
    shade = avg(lambda s: min(100, s["shade"] + s["canyon"] * b["low_sun"] * 60))
    f = {"temperature": b["temp"] - b["veg_cooling"] * veg,
         "solar": b["sun"] * (1 - shade / 100),
         "surface": avg(lambda s: s["surface"]) * b["surface"],
         "duration": min(100, total_min / 30 * 100),
         "shade_relief": shade, "vegetation_relief": veg, "wind_relief": b["wind"]}
    return {k: round(v, 1) for k, v in f.items()}


def _score(f, mult):
    s = sum(w * f[k] for k, w in WEIGHTS.items()) + sum(w * (100 - f[k]) for k, w in RELIEF_WEIGHTS.items())
    return max(0, min(100, s * mult))


def compute_routes(time, profile):
    d = load_data()
    key = bucket_for(time)
    b, m, out = d["buckets"][key], PROFILES[profile], []
    for r in d["routes"]:
        total = sum(s["minutes"] for s in r["segments"])
        f = _factors(r["segments"], b, total)
        sc = round(_score(f, m))
        out.append({"id": r["id"], "name": r["name"], "kind": r["kind"], "minutes": total,
                    "score": sc, "label": label(sc), "factors": f,
                    "segments": [{"name": s["name"], "minutes": s["minutes"], "path": s["path"],
                                  "score": round(_score(_factors([s], b, total), m))} for s in r["segments"]]})
    return key, out


def recommend(routes):
    fast = min(routes, key=lambda r: r["minutes"])
    best = None
    for r in routes:
        saved, extra = fast["score"] - r["score"], r["minutes"] - fast["minutes"]
        if r is not fast and saved >= MIN_SAVING and extra <= MAX_EXTRA and (best is None or r["score"] < best["score"]):
            best = r
    rec = best or fast
    saved = fast["score"] - rec["score"]
    return {"fastest_id": fast["id"], "recommended_id": rec["id"],
            "extra_minutes": rec["minutes"] - fast["minutes"], "points_saved": saved,
            "reduction_pct": round(100 * saved / fast["score"]) if fast["score"] else 0,
            "rule": f"Cooler route recommended only if it saves at least {MIN_SAVING} points for at most {MAX_EXTRA} extra minutes."}
