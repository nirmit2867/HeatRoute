"""Load the demo heat data into DynamoDB. Usage: python infrastructure/seed_dynamodb.py <TableName>"""
import json
import os
import sys
from decimal import Decimal

import boto3

src = os.path.join(os.path.dirname(__file__), "..", "backend", "lambda", "route_score", "demo_heat_data.json")
data = json.load(open(src))
dec = lambda o: json.loads(json.dumps(o), parse_float=Decimal)
table = boto3.resource("dynamodb").Table(sys.argv[1])
with table.batch_writer() as w:
    w.put_item(Item={"cell_id": "meta", "kind": "meta", "json": json.dumps(data["meta"])})
    for key, b in data["buckets"].items():
        w.put_item(Item=dec({"cell_id": f"bucket#{key}", "kind": "bucket", **b}))
    for r in data["routes"]:
        for i, s in enumerate(r["segments"]):
            item = {**s, "cell_id": s["id"], "kind": "segment", "route_id": r["id"], "route_name": r["name"],
                    "route_kind": r["kind"], "order": i, "path": json.dumps(s["path"])}
            item.pop("id")
            w.put_item(Item=dec(item))
print("Seeded", sys.argv[1])
