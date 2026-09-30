#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lab 09 - Serverless API & Automation - DEPLOY
#
# Builds, in order: a DynamoDB table -> two IAM roles (least privilege, one
# per Lambda's job) -> two Lambda functions (the items API + the daily job)
# -> an HTTP API in front of the items function -> an EventBridge Scheduler
# schedule pointed at the daily-job function.
#
# IDEMPOTENT: safe to re-run. Every create step checks "does this already
# exist?" first and skips or updates instead of failing on a duplicate.
#
# Region is hardcoded to us-west-2 per the lab spec -- change REGION below if
# you fork this for another lab.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REGION="us-west-2"
TABLE_NAME="lab09-items"
LAMBDA_ROLE_NAME="lab09-lambda-role"
SCHEDULER_ROLE_NAME="lab09-scheduler-role"
ITEMS_FN="lab09-items-api"
JOB_FN="lab09-daily-job"
API_NAME="lab09-items-api"
SCHEDULE_NAME="lab09-daily-summary"
TAGS="Key=env,Value=lab Key=owner,Value=cam Key=project,Value=lab09"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$ASSETS_DIR/lambda"
POLICY_DIR="$ASSETS_DIR/policies"
BUILD_DIR="$ASSETS_DIR/.build"
mkdir -p "$BUILD_DIR"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
echo "==> Account: $ACCOUNT_ID  Region: $REGION"

# ── 1. DynamoDB table ────────────────────────────────────────────────────────
echo "==> [1/7] DynamoDB table: $TABLE_NAME"
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" >/dev/null 2>&1; then
  echo "    already exists - skipping create."
else
  aws dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=env,Value=lab Key=owner,Value=cam Key=project,Value=lab09 \
    --region "$REGION" >/dev/null
  echo "    created - waiting for ACTIVE..."
fi
aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
TABLE_ARN="$(aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" \
  --query 'Table.TableArn' --output text)"
echo "    ACTIVE - $TABLE_ARN"

# Point-in-time recovery -- the standard reliability checkbox for any table
# that isn't purely throwaway: continuous backups, restore to any second in
# the last 35 days, no manual snapshot schedule to maintain.
aws dynamodb update-continuous-backups --table-name "$TABLE_NAME" \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --region "$REGION" >/dev/null
echo "    point-in-time recovery: enabled"

# ── 2. IAM role for both Lambda functions (least privilege on THIS table) ──
echo "==> [2/7] IAM role: $LAMBDA_ROLE_NAME"
if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" >/dev/null 2>&1; then
  echo "    already exists - skipping create."
else
  aws iam create-role \
    --role-name "$LAMBDA_ROLE_NAME" \
    --assume-role-policy-document "file://$POLICY_DIR/lambda-trust-policy.json" \
    --tags Key=env,Value=lab Key=owner,Value=cam Key=project,Value=lab09 >/dev/null
fi
# CloudWatch Logs (every Lambda needs this to emit logs at all).
aws iam attach-role-policy --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
# The scoped data-plane policy, rendered from the JSONC teaching copy with
# THIS table's real ARN substituted in (not the AWS-managed, account-wide
# AWSLambdaDynamoDBExecutionRole policy -- see policies/items-table-policy.json).
python3 - "$POLICY_DIR/items-table-policy.json" "$TABLE_ARN" "$BUILD_DIR/items-table-policy.rendered.json" <<'PYEOF'
import json, re, sys
src, table_arn, out = sys.argv[1:4]
text = open(src).read()
# Strip // line comments (JSONC -> JSON) before parsing.
text = re.sub(r'^\s*//.*$', '', text, flags=re.MULTILINE)
doc = json.loads(text)
doc["Statement"][0]["Resource"] = table_arn
json.dump(doc, open(out, "w"), indent=2)
PYEOF
aws iam put-role-policy --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name items-table-access \
  --policy-document "file://$BUILD_DIR/items-table-policy.rendered.json"

echo "    waiting ~10s for IAM propagation (new roles aren't instantly assumable)..."
sleep 10

# ── 3. Package + create/update the items-api Lambda ─────────────────────────
echo "==> [3/7] Lambda: $ITEMS_FN"
( cd "$LAMBDA_DIR/items_api" && zip -q -X -r "$BUILD_DIR/items_api.zip" index.py )
LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
# Advanced Logging Controls -- Lambda's current, native structured-logging
# feature: platform log lines come out as JSON instead of plain text, and the
# log level is set per function instead of baked into the code.
LOGGING_CONFIG="LogFormat=JSON,ApplicationLogLevel=INFO,SystemLogLevel=INFO"
if aws lambda get-function --function-name "$ITEMS_FN" --region "$REGION" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$ITEMS_FN" \
    --zip-file "fileb://$BUILD_DIR/items_api.zip" --region "$REGION" >/dev/null
  aws lambda wait function-updated-v2 --function-name "$ITEMS_FN" --region "$REGION"
  aws lambda update-function-configuration --function-name "$ITEMS_FN" \
    --environment "Variables={TABLE_NAME=$TABLE_NAME}" \
    --logging-config "$LOGGING_CONFIG" --region "$REGION" >/dev/null
  echo "    updated existing function."
else
  aws lambda create-function \
    --function-name "$ITEMS_FN" \
    --runtime python3.13 \
    --role "$LAMBDA_ROLE_ARN" \
    --handler index.handler \
    --zip-file "fileb://$BUILD_DIR/items_api.zip" \
    --timeout 10 --memory-size 128 \
    --environment "Variables={TABLE_NAME=$TABLE_NAME}" \
    --logging-config "$LOGGING_CONFIG" \
    --tags env=lab,owner=cam,project=lab09 \
    --region "$REGION" >/dev/null
  echo "    created."
fi
aws lambda wait function-active-v2 --function-name "$ITEMS_FN" --region "$REGION"
ITEMS_FN_ARN="$(aws lambda get-function --function-name "$ITEMS_FN" --region "$REGION" \
  --query 'Configuration.FunctionArn' --output text)"

# Create the log group up front with a 14-day retention -- the default is
# "never expire," which quietly racks up storage cost forever. Setting this
# explicitly, before the function ever runs, is the habit.
aws logs create-log-group --log-group-name "/aws/lambda/$ITEMS_FN" \
  --region "$REGION" >/dev/null 2>&1 || true
aws logs put-retention-policy --log-group-name "/aws/lambda/$ITEMS_FN" \
  --retention-in-days 14 --region "$REGION"

# ── 4. Package + create/update the daily-job Lambda ─────────────────────────
echo "==> [4/7] Lambda: $JOB_FN"
( cd "$LAMBDA_DIR/daily_job" && zip -q -X -r "$BUILD_DIR/daily_job.zip" index.py )
if aws lambda get-function --function-name "$JOB_FN" --region "$REGION" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$JOB_FN" \
    --zip-file "fileb://$BUILD_DIR/daily_job.zip" --region "$REGION" >/dev/null
  aws lambda wait function-updated-v2 --function-name "$JOB_FN" --region "$REGION"
  aws lambda update-function-configuration --function-name "$JOB_FN" \
    --environment "Variables={TABLE_NAME=$TABLE_NAME}" \
    --logging-config "$LOGGING_CONFIG" --region "$REGION" >/dev/null
  echo "    updated existing function."
else
  aws lambda create-function \
    --function-name "$JOB_FN" \
    --runtime python3.13 \
    --role "$LAMBDA_ROLE_ARN" \
    --handler index.handler \
    --zip-file "fileb://$BUILD_DIR/daily_job.zip" \
    --timeout 10 --memory-size 128 \
    --environment "Variables={TABLE_NAME=$TABLE_NAME}" \
    --logging-config "$LOGGING_CONFIG" \
    --tags env=lab,owner=cam,project=lab09 \
    --region "$REGION" >/dev/null
  echo "    created."
fi
aws lambda wait function-active-v2 --function-name "$JOB_FN" --region "$REGION"
JOB_FN_ARN="$(aws lambda get-function --function-name "$JOB_FN" --region "$REGION" \
  --query 'Configuration.FunctionArn' --output text)"

aws logs create-log-group --log-group-name "/aws/lambda/$JOB_FN" \
  --region "$REGION" >/dev/null 2>&1 || true
aws logs put-retention-policy --log-group-name "/aws/lambda/$JOB_FN" \
  --retention-in-days 14 --region "$REGION"

# ── 5. HTTP API (API Gateway) in front of items-api ─────────────────────────
echo "==> [5/7] HTTP API: $API_NAME"
API_ID="$(aws apigatewayv2 get-apis --region "$REGION" \
  --query "Items[?Name=='$API_NAME'].ApiId | [0]" --output text)"
if [[ "$API_ID" == "None" || -z "$API_ID" ]]; then
  API_ID="$(aws apigatewayv2 create-api \
    --name "$API_NAME" --protocol-type HTTP \
    --tags env=lab,owner=cam,project=lab09 \
    --region "$REGION" --query 'ApiId' --output text)"
  echo "    created API $API_ID"
else
  echo "    already exists - API $API_ID"
fi

INTEGRATION_ID="$(aws apigatewayv2 get-integrations --api-id "$API_ID" --region "$REGION" \
  --query "Items[?IntegrationUri=='$ITEMS_FN_ARN'].IntegrationId | [0]" --output text)"
if [[ "$INTEGRATION_ID" == "None" || -z "$INTEGRATION_ID" ]]; then
  INTEGRATION_ID="$(aws apigatewayv2 create-integration --api-id "$API_ID" \
    --integration-type AWS_PROXY --integration-method POST \
    --integration-uri "$ITEMS_FN_ARN" --payload-format-version 2.0 \
    --region "$REGION" --query 'IntegrationId' --output text)"
  echo "    created integration $INTEGRATION_ID"
fi

for route in "POST /items" "GET /items" "GET /items/{id}" "DELETE /items/{id}"; do
  existing="$(aws apigatewayv2 get-routes --api-id "$API_ID" --region "$REGION" \
    --query "Items[?RouteKey=='$route'].RouteId | [0]" --output text)"
  if [[ "$existing" == "None" || -z "$existing" ]]; then
    aws apigatewayv2 create-route --api-id "$API_ID" \
      --route-key "$route" --target "integrations/$INTEGRATION_ID" \
      --region "$REGION" >/dev/null
    echo "    route created: $route"
  else
    echo "    route exists:  $route"
  fi
done

if ! aws apigatewayv2 get-stage --api-id "$API_ID" --stage-name '$default' --region "$REGION" >/dev/null 2>&1; then
  aws apigatewayv2 create-stage --api-id "$API_ID" \
    --stage-name '$default' --auto-deploy --region "$REGION" >/dev/null
  echo "    \$default stage created (auto-deploy on)."
fi

# API Gateway needs explicit permission to invoke the Lambda (resource policy).
aws lambda add-permission --function-name "$ITEMS_FN" \
  --statement-id apigw-invoke --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" \
  --region "$REGION" >/dev/null 2>&1 || echo "    (permission already present)"

API_ENDPOINT="$(aws apigatewayv2 get-api --api-id "$API_ID" --region "$REGION" \
  --query 'ApiEndpoint' --output text)"
echo "    endpoint: $API_ENDPOINT"

# ── 6. Scheduler role + schedule for the daily job ──────────────────────────
echo "==> [6/7] EventBridge Scheduler role + schedule: $SCHEDULE_NAME"
if aws iam get-role --role-name "$SCHEDULER_ROLE_NAME" >/dev/null 2>&1; then
  echo "    role already exists - skipping create."
else
  aws iam create-role \
    --role-name "$SCHEDULER_ROLE_NAME" \
    --assume-role-policy-document "file://$POLICY_DIR/scheduler-trust-policy.json" \
    --tags Key=env,Value=lab Key=owner,Value=cam Key=project,Value=lab09 >/dev/null
fi
python3 - "$POLICY_DIR/scheduler-invoke-policy.json" "$JOB_FN_ARN" "$BUILD_DIR/scheduler-invoke-policy.rendered.json" <<'PYEOF'
import json, re, sys
src, fn_arn, out = sys.argv[1:4]
text = open(src).read()
text = re.sub(r'^\s*//.*$', '', text, flags=re.MULTILINE)
doc = json.loads(text)
doc["Statement"][0]["Resource"] = fn_arn
json.dump(doc, open(out, "w"), indent=2)
PYEOF
aws iam put-role-policy --role-name "$SCHEDULER_ROLE_NAME" \
  --policy-name invoke-daily-job \
  --policy-document "file://$BUILD_DIR/scheduler-invoke-policy.rendered.json"
SCHEDULER_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${SCHEDULER_ROLE_NAME}"

echo "    waiting ~10s for IAM propagation..."
sleep 10

if aws scheduler get-schedule --name "$SCHEDULE_NAME" --region "$REGION" >/dev/null 2>&1; then
  echo "    schedule already exists - skipping create."
else
  aws scheduler create-schedule \
    --name "$SCHEDULE_NAME" \
    --schedule-expression "cron(0 13 * * ? *)" \
    --flexible-time-window Mode=OFF \
    --target "Arn=${JOB_FN_ARN},RoleArn=${SCHEDULER_ROLE_ARN}" \
    --region "$REGION" >/dev/null
  echo "    created - fires daily at 13:00 UTC (06:00 Pacific)."
fi

# ── 7. Security lint: validate the custom IAM policies with Access Analyzer ─
echo "==> [7/7] Security scan - IAM Access Analyzer policy validation"
for p in "$BUILD_DIR/items-table-policy.rendered.json" "$BUILD_DIR/scheduler-invoke-policy.rendered.json"; do
  echo "    checking $(basename "$p")..."
  aws accessanalyzer validate-policy --region "$REGION" \
    --policy-type IDENTITY_POLICY --policy-document "file://$p" \
    --query 'findings[?findingType!=`SUGGESTION`]' --output json
done

echo ""
echo "==> Done. Try it:"
echo "curl -s -X POST $API_ENDPOINT/items -d '{\"name\":\"first item\"}'"
echo "curl -s $API_ENDPOINT/items"
echo ""
echo "Check the daily job manually (don't wait for 13:00 UTC):"
echo "aws lambda invoke --function-name $JOB_FN --region $REGION --cli-binary-format raw-in-base64-out /tmp/lab09-job-out.json && cat /tmp/lab09-job-out.json"
