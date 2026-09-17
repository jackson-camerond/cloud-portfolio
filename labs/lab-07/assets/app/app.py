"""
aks-demo-api, the small web API this lab containerizes and runs on AKS.

Three routes, on purpose:
  GET /          -> who answered (pod name, version), proves the LoadBalancer
                    is spreading traffic across multiple pods.
  GET /healthz   -> liveness/readiness probe target.
  GET /work      -> burns CPU for ~`ms` milliseconds. This is the HPA trigger:
                    the load generator in assets/scripts/loadgen.py hammers
                    this route until average CPU crosses the HPA's 50% target
                    and Kubernetes schedules more pods on its own.

No external dependencies beyond Flask + gunicorn, small image, fast build.
"""
import os
import socket
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

VERSION = os.environ.get("APP_VERSION", "v1")
POD_NAME = os.environ.get("POD_NAME", socket.gethostname())


@app.get("/")
def index():
    return jsonify(
        message="hello from AKS",
        pod=POD_NAME,
        version=VERSION,
    )


@app.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200


@app.get("/work")
def work():
    """Busy-loop for `ms` milliseconds (default 200) to generate real CPU load."""
    ms = int(request.args.get("ms", 200))
    end = time.time() + (ms / 1000.0)
    total = 0
    while time.time() < end:
        total += 1  # pure CPU spin, no sleep, this is what trips the HPA
    return jsonify(pod=POD_NAME, burned_ms=ms, iterations=total)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
