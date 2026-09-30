"""
Lab 09 - the automated daily job.

EventBridge Scheduler fires this Lambda once a day, no server, no cron
daemon, nobody watching a clock. It scans the same items table and writes a
one-line summary to CloudWatch Logs -- stand-in for "email a daily report" /
"clean up stale rows", the two examples the plan calls out. The summary is
the automation's receipt: proof it ran, and what it found.

Same least-privilege shape as the API function: this role can Scan (and, if
you extend it, DeleteItem for a real cleanup job) on this one table only.
"""
import json
import os
import time

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    result = table.scan(Select="COUNT")
    count = result.get("Count", 0)

    summary = {
        "job": "daily-items-summary",
        "table": TABLE_NAME,
        "itemCount": count,
        "ranAtEpoch": int(time.time()),
    }

    # This print IS the deliverable for the lab: it lands in CloudWatch Logs
    # and is the evidence that the schedule actually fired.
    print(json.dumps(summary))

    return summary
