import json
import re
import time as _time

from .scoring import PROFILES, compute_routes, load_data, recommend

HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


def respond(code, body):
    return {"statusCode": code, "headers": HEADERS, "body": json.dumps(body)}


def parse_request(event):
    """Returns (time, profile, error_response)."""
    try:
        req = json.loads(event.get("body") or "{}")
    except ValueError:
        return None, None, respond(400, {"error": "Request body must be valid JSON."})
    t, p = req.get("time", "13:00"), req.get("profile", "pedestrian")
    if not isinstance(t, str) or not TIME_RE.match(t):
        return None, None, respond(400, {"error": "time must look like 13:00."})
    if p not in PROFILES:
        return None, None, respond(400, {"error": "profile must be one of: " + ", ".join(PROFILES)})
    return t, p, None


def lambda_handler(event, context):
    start = _time.time()
    t, p, err = parse_request(event)
    if err:
        return err
    try:
        bucket, routes = compute_routes(t, p)
        meta = load_data()["meta"]
    except Exception as exc:  # logged to CloudWatch, generic message to the user
        print(json.dumps({"event": "route_score_error", "error": str(exc)}))
        return respond(500, {"error": "Could not load heat data. Please try again."})
    print(json.dumps({"event": "route_score", "bucket": bucket, "profile": p,
                      "ms": round((_time.time() - start) * 1000)}))
    return respond(200, {"meta": meta, "time": t, "bucket": bucket, "profile": p,
                         "routes": routes, "recommendation": recommend(routes)})
