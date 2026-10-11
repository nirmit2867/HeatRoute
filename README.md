# HeatRoute

**Maps optimize your journey. HeatRoute optimizes your exposure.**
Track: Heat and Water. Environmental Hacks, Bharat Builds Tour.

HeatRoute compares routes by an estimated Heat Exposure Score as well as travel time, and explains the recommendation. The score is an environmental estimate, not a medical prediction.

## Run locally (no AWS needed)
```bash
python backend/local_server.py     # http://127.0.0.1:8000
```
Uses the same Lambda handlers as AWS. Explanations use a template unless `BEDROCK_MODEL_ID` is set and AWS credentials are available.

## Deploy to AWS
```bash
cd infrastructure && sam build && sam deploy --guided --parameter-overrides BedrockModelId=<model-or-profile-id>
python seed_dynamodb.py <TableName from outputs>
# set window.HEATROUTE_API in frontend/public/config.js to the ApiUrl output, then:
aws s3 sync ../frontend/public s3://<SiteBucketName>
```
Enable model access for your Bedrock model in your region first. The site bucket is public by design (static site); delete it after judging.

## AWS services
API Gateway (HTTP API) and Lambda (`route_score`, `explain_route`), DynamoDB (`HeatCells`: heat buckets and route segments), S3 (static site), Amazon Bedrock (explanations), CloudWatch (structured Lambda logs).

## Data honesty
All heat inputs are **simulated demo values** for one corridor (see `data/README.md`). The UI says so. Time conditions are modelled for 3 buckets: morning, midday, evening.

## Credits and licences
Code: MIT. Fonts via Google Fonts: Bricolage Grotesque and IBM Plex Sans, both SIL Open Font License 1.1. No external datasets are used yet.
