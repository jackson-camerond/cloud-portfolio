#!/usr/bin/env python3
"""
loadgen.py, hammer the /work endpoint until the HPA scales out.

This is the on-camera load test: it fires concurrent requests at the app's
public LoadBalancer IP, each one burning ~250ms of CPU inside the pod that
answers it. Enough concurrent requests push average CPU across all pods
above the HPA's 50% target, and `kubectl get hpa -w` shows REPLICAS climb
with nobody touching a scale command.

Usage:
    python3 loadgen.py <ip-or-hostname> [--seconds 120] [--workers 40] [--ms 250]

Standard library only (urllib + threading) -- no pip install needed to run
the load test itself.
"""
import argparse
import sys
import threading
import time
import urllib.request


def hit(url: str, ms: int, stop_at: float, counters: dict, lock: threading.Lock) -> None:
    while time.time() < stop_at:
        try:
            with urllib.request.urlopen(f"{url}/work?ms={ms}", timeout=5) as resp:
                resp.read()
            with lock:
                counters["ok"] += 1
        except Exception:
            with lock:
                counters["fail"] += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Load test the aks-demo-api /work endpoint.")
    parser.add_argument("host", help="Public IP or hostname of the aks-demo-api Service (no http://)")
    parser.add_argument("--seconds", type=int, default=120, help="How long to hammer it (default 120)")
    parser.add_argument("--workers", type=int, default=40, help="Concurrent request threads (default 40)")
    parser.add_argument("--ms", type=int, default=250, help="CPU-burn ms per request (default 250)")
    args = parser.parse_args()

    url = args.host if args.host.startswith("http") else f"http://{args.host}"
    stop_at = time.time() + args.seconds
    counters = {"ok": 0, "fail": 0}
    lock = threading.Lock()

    print(f"Hammering {url}/work for {args.seconds}s with {args.workers} workers "
          f"({args.ms}ms of CPU per request)...")
    print("Watch it scale in another terminal:  kubectl get hpa -n aks-demo -w")

    threads = [
        threading.Thread(target=hit, args=(url, args.ms, stop_at, counters, lock), daemon=True)
        for _ in range(args.workers)
    ]
    for t in threads:
        t.start()

    try:
        while time.time() < stop_at:
            time.sleep(5)
            with lock:
                print(f"  ...{counters['ok']} ok / {counters['fail']} failed so far")
    except KeyboardInterrupt:
        print("\nStopped early.")

    for t in threads:
        t.join(timeout=2)

    print(f"Done. {counters['ok']} ok, {counters['fail']} failed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
