# Steam Price Watcher — run in Docker
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY steam/ steam/
COPY storage/ storage/
COPY notifier/ notifier/
COPY watcher/ watcher/
COPY main.py .

# SQLite DB and logs live in data/ (mount as volume)
RUN mkdir -p /app/data

# Unbuffered stdout/stderr so docker logs show output immediately
ENV PYTHONUNBUFFERED=1

# Default: run watcher in loop; override with ["python", "main.py", "--once"] for single run
CMD ["python", "main.py"]
