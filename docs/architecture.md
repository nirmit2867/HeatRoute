# Architecture
Browser (S3 static site) -> API Gateway HTTP API -> Lambda `route_score` (reads `HeatCells` in DynamoDB, scores routes) and Lambda `explain_route` (recomputes the same facts server-side, calls Bedrock Converse, falls back to a template). CloudWatch receives structured JSON logs. The explanation uses only computed numbers, never client-supplied text.
