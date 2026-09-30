"""
Lab 09 - items API Lambda handler.

One function, four routes, behind an HTTP API (API Gateway) using AWS_PROXY
(Lambda proxy) integration with payload format version 2.0. The router below
reads event["routeKey"] (e.g. "POST /items") because a payload-v2 event carries
the exact route that matched, so one function can serve create/read/list/delete
without four separate Lambdas or an if/elif chain on the raw path.

Table: DynamoDB, partition key "id" (string). No sort key -- this is a flat
item store, which is all a small CRUD API needs.

Least privilege: this function's IAM role only allows GetItem / PutItem /
DeleteItem / Scan on this ONE table's ARN (see policies/items-table-policy.json).
It cannot touch any other table, and it cannot call CreateTable/DeleteTable.
"""
import base64
import json
import os
import time
import uuid
from decimal import Decimal

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


class _DecimalEncoder(json.JSONEncoder):
    # boto3's DynamoDB resource returns every Number attribute as a
    # decimal.Decimal (so it round-trips exactly), and json.dumps doesn't
    # know how to serialize that type out of the box. Whole numbers (like
    # our epoch-second createdAt) come back out as plain int; anything with
    # a fractional part falls back to float.
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=_DecimalEncoder),
    }


def _request_body(event):
    # API Gateway HTTP API (payload format 2.0) base64-encodes the body and
    # sets isBase64Encoded=true whenever the request's Content-Type isn't one
    # it treats as plain text -- e.g. curl's default
    # "application/x-www-form-urlencoded" for `-d`, not just real binary
    # payloads. Any proxy-integration handler that reads event["body"] as a
    # raw string will break on that case, so decode first when the flag says to.
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return raw


def _create_item(event):
    payload = json.loads(_request_body(event))
    name = payload.get("name")
    if not name:
        return _response(400, {"error": "name is required"})

    item = {
        "id": str(uuid.uuid4()),
        "name": name,
        "createdAt": int(time.time()),
    }
    table.put_item(Item=item)
    return _response(201, item)


def _list_items(event):
    result = table.scan(Limit=50)
    return _response(200, {"items": result.get("Items", [])})


def _get_item(event):
    item_id = event["pathParameters"]["id"]
    result = table.get_item(Key={"id": item_id})
    item = result.get("Item")
    if not item:
        return _response(404, {"error": f"no item with id {item_id}"})
    return _response(200, item)


def _delete_item(event):
    item_id = event["pathParameters"]["id"]
    table.delete_item(Key={"id": item_id})
    return _response(204, {})


ROUTES = {
    "POST /items": _create_item,
    "GET /items": _list_items,
    "GET /items/{id}": _get_item,
    "DELETE /items/{id}": _delete_item,
}


def handler(event, context):
    route_key = event.get("routeKey", "")
    fn = ROUTES.get(route_key)
    if fn is None:
        return _response(404, {"error": f"no route for {route_key}"})
    try:
        return fn(event)
    except Exception as exc:  # noqa: BLE001 -- surface as a clean 500, log the real error
        print(f"ERROR handling {route_key}: {exc}")
        return _response(500, {"error": "internal error"})
