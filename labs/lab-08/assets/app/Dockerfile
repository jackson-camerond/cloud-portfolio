# Lab 08 -- the app the pipeline builds, scans, and ships.
FROM python:3.13-slim

# Run as a non-root user. This is one of the first things Trivy flags on a
# container -- fixed at the source instead of suppressed in the scan.
RUN useradd --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY app.py .

USER appuser

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1

CMD ["python3", "app.py"]
