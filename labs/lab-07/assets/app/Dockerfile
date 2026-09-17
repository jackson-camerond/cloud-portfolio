# aks-demo-api, small, fast-building image for a small demo API.
# Multi-stage-free on purpose: this is a tiny Flask app, not worth the extra
# stage. python:3.13-slim keeps the image small and current.
FROM python:3.13-slim

WORKDIR /app

# Install deps first so Docker/ACR layer-caches them across rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Run as a non-root user, least privilege inside the container, same
# instinct as least-privilege IAM everywhere else in this series.
RUN useradd -u 1000 -m appuser
USER appuser

EXPOSE 8080

# 2 workers is plenty for a demo API; gunicorn gives real WSGI behavior
# instead of Flask's dev server (which warns against production use).
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
