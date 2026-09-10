"""
Link shortener: the demo service for Lab 02 (Secure 2-Tier).

Deliberately a real-shaped little service (the kind a team runs for internal
"go/" links): a stateless web/API tier that reads and writes rows in a
database on a private subnet. The app is the boring part on purpose, what
matters is WHERE the DB lives and WHO can reach it.

The seam: every piece of the DB connection comes from the environment (see
/etc/app.env) and the driver is pymssql (SQL Server's wire protocol, TCP
1433). So moving from the Lab 02 private DB VM to a managed Azure SQL
Database is a config change only, this code does not change.

Parameterized queries (%s placeholders), pymssql escapes the values, so
nothing here is open to SQL injection.
"""
import os
import secrets
import string

import pymssql
from flask import Flask, request, redirect, render_template, jsonify, abort

app = Flask(__name__)

ALPHABET = string.ascii_lowercase + string.digits


def db_conn():
    return pymssql.connect(
        server=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "1433"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
        login_timeout=5,
        timeout=5,
    )


def gen_code(n=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


@app.route("/", methods=["GET"])
def index():
    error = None
    links = []
    try:
        conn = db_conn()
        cur = conn.cursor(as_dict=True)
        cur.execute(
            "SELECT TOP 50 code, target, hits, created_at "
            "FROM dbo.links ORDER BY id DESC"
        )
        links = cur.fetchall()
        conn.close()
    except Exception as e:  # DB tier not up yet / unreachable, show it, don't 500
        error = str(e)
    return render_template(
        "index.html",
        links=links,
        error=error,
        db_host=os.environ.get("DB_HOST", "?"),
    )


@app.route("/", methods=["POST"])
def create():
    target = (request.form.get("target") or "").strip()[:2048]
    custom = "".join(c for c in (request.form.get("code") or "") if c in ALPHABET)[:16]
    if target.startswith(("http://", "https://")):
        code = custom or gen_code()
        try:
            conn = db_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO dbo.links (code, target) VALUES (%s, %s)",
                (code, target),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # collision / unreachable, fall through to the list
    return redirect("/")


@app.route("/api/links", methods=["GET"])
def api_links():
    """JSON view of the same data, the 'API tier' face of the service."""
    conn = db_conn()
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT code, target, hits, created_at FROM dbo.links ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


@app.route("/healthz")
def healthz():
    """Proves the web tier can reach the DB tier. Used by the healthz check."""
    try:
        conn = db_conn()
        conn.close()
        return "ok", 200
    except Exception:
        return "db-unreachable", 503


@app.route("/<code>")
def follow(code):
    """Resolve a short code -> 302 redirect. This read hits the private DB live."""
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT target FROM dbo.links WHERE code = %s", (code,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE dbo.links SET hits = hits + 1 WHERE code = %s", (code,))
        conn.commit()
    conn.close()
    if not row:
        abort(404)
    return redirect(row[0])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
