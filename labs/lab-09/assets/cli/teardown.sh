#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lab 09 - TEARDOWN. Reverse dependency order: schedule -> API -> permissions
# -> Lambda functions -> IAM role policies/roles -> DynamoDB table.
#
# Nothing here bills by the hour (Lambda/API Gateway/DynamoDB on-demand/
# EventBridge Scheduler are all pay-per-use), but this is the cost-discipline
# habit anyway: don't leave resources around you're not actively using.
#
# Every command is `|| true` - safe to re-run if a previous teardown partially
# failed, and safe to run even if deploy.sh only got halfway.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

REGION="us-west-2"
TABLE_NAME="lab09-items"
LAMBDA_ROLE_NAME="lab09-lambda-role"
SCHEDULER_ROLE_NAME="lab09-scheduler-role"
ITEMS_FN="lab09-items-api"
JOB_FN="lab09-daily-job"
API_NAME="lab09-items-api"
SCHEDULE_NAME="lab09-daily-summary"

echo "==> [1/6] Deleting EventBridge Scheduler schedule: $SCHEDULE_NAME"
aws scheduler delete-schedule --name "$SCHEDULE_NAME" --region "$REGION" || true

echo "==> [2/6] Deleting HTTP API: $API_NAME"
API_ID="$(aws apigatewayv2 get-apis --region "$REGION" \
  --query "Items[?Name=='$API_NAME'].ApiId | [0]" --output text 2>/dev/null)"
if [[ -n "$API_ID" && "$API_ID" != "None" ]]; then
  aws apigatewayv2 delete-api --api-id "$API_ID" --region "$REGION" || true
  echo "    deleted API $API_ID"
else
  echo "    no API found - skipping."
fi

echo "==> [3/6] Deleting Lambda functions: $ITEMS_FN, $JOB_FN"
aws lambda delete-function --function-name "$ITEMS_FN" --region "$REGION" || true
aws lambda delete-function --function-name "$JOB_FN" --region "$REGION" || true

echo "==> [4/6] Removing role policies + roles"
aws iam detach-role-policy --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true
aws iam delete-role-policy --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name items-table-access || true
aws iam delete-role --role-name "$LAMBDA_ROLE_NAME" || true

aws iam delete-role-policy --role-name "$SCHEDULER_ROLE_NAME" \
  --policy-name invoke-daily-job || true
aws iam delete-role --role-name "$SCHEDULER_ROLE_NAME" || true

echo "==> [5/6] Deleting DynamoDB table: $TABLE_NAME"
aws dynamodb delete-table --table-name "$TABLE_NAME" --region "$REGION" || true

echo "    Deleting explicit log groups (created with 14-day retention in deploy.sh)"
aws logs delete-log-group --log-group-name "/aws/lambda/$ITEMS_FN" --region "$REGION" || true
aws logs delete-log-group --log-group-name "/aws/lambda/$JOB_FN" --region "$REGION" || true

echo "==> [6/6] Cleaning local build artifacts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "$(dirname "$SCRIPT_DIR")/.build"

echo ""
echo "Lab 09 torn down. Only lab09-* resources were targeted - nothing else"
echo "in the account was touched."
