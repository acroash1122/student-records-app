# ---- Flask application image ----
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 5000

# Lightweight healthcheck — calls /health and expects HTTP 200
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c \
        "import urllib.request, sys; \
         r = urllib.request.urlopen('http://localhost:5000/health', timeout=4); \
         sys.exit(0 if r.status == 200 else 1)" \
    || exit 1

CMD ["python", "app.py"]
