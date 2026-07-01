FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY policies/ policies/

RUN pip install --no-cache-dir -e .

EXPOSE 7860 8000

CMD ["guardweave", "agent", "dashboard"]
