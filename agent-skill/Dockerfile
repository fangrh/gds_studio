FROM python:3.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY gds_collab_skill/ ./gds_collab_skill/
RUN pip install --no-cache-dir .

ENV GDS_COLLAB_API=http://backend:8000
ENV GDS_SCRIPTS_DIR=/data/scripts
ENV GDS_GDS_DIR=/data/gds
ENV POLL_INTERVAL=30

CMD ["python", "-m", "gds_collab_skill.worker"]
