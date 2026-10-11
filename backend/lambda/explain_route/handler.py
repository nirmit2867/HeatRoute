import json
import os

from route_score.handler import parse_request, respond
from route_score.scoring import MAX_EXTRA, MIN_SAVING, compute_routes, recommend

DISCLAIMER = "Estimated environmental index, not a medical prediction."
SYSTEM = ("You explain a route recommendation in 2-3 plain sentences. Use ONLY the numbers in the JSON "
          "provided; never add data. State the time trade-off and score change. Do not give medical advice. "
          "Say the score is an estimate.")
NAMES = {"temperature": "air temperature", "solar": "direct sun", "surface": "hot surfaces"}


def template(t, fast, rec):
    if fast["id"] == rec["id"]:
        return (f"At {t}, no alternative lowers the estimated score by {MIN_SAVING}+ points within "
                f"{MAX_EXTRA} extra minutes, so the fastest route, {fast['name']} ({fast['minutes']} min, "
                f"score {fast['score']}), is recommended.")
    ff, rf = fast["factors"], rec["factors"]
    diffs = {NAMES[k]: ff[k] - rf[k] for k in NAMES}
    diffs["shade"] = rf["shade_relief"] - ff["shade_relief"]
    top = sorted(diffs.items(), key=lambda kv: -kv[1])[:2]
    return (f"{rec['name']} takes {rec['minutes'] - fast['minutes']} min longer but lowers the estimated heat "
            f"score from {fast['score']} to {rec['score']}. The biggest differences are "
            f"{top[0][0]} ({top[0][1]:+.0f} index points) and {top[1][0]} ({top[1][1]:+.0f}). This is an estimate.")


def bedrock_text(facts):
    import boto3
    client = boto3.client("bedrock-runtime")
    r = client.converse(modelId=os.environ["BEDROCK_MODEL_ID"], system=[{"text": SYSTEM}],
                        messages=[{"role": "user", "content": [{"text": json.dumps(facts)}]}],
                        inferenceConfig={"maxTokens": 220, "temperature": 0.2})
    return r["output"]["message"]["content"][0]["text"].strip()


def lambda_handler(event, context):
    t, p, err = parse_request(event)
    if err:
        return err
    _, routes = compute_routes(t, p)
    rec_info = recommend(routes)
    by_id = {r["id"]: r for r in routes}
    fast, rec = by_id[rec_info["fastest_id"]], by_id[rec_info["recommended_id"]]
    facts = {"time": t, "profile": p, "recommendation": rec_info,
             "fastest": {k: fast[k] for k in ("name", "minutes", "score", "factors")},
             "recommended": {k: rec[k] for k in ("name", "minutes", "score", "factors")}}
    text, source = None, "template"
    if os.environ.get("BEDROCK_MODEL_ID"):
        try:
            text, source = bedrock_text(facts), "bedrock"
        except Exception as exc:
            print(json.dumps({"event": "bedrock_error", "error": str(exc)}))
    return respond(200, {"explanation": text or template(t, fast, rec), "source": source, "disclaimer": DISCLAIMER})
