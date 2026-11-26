FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends clamav clamav-freshclam && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn==0.30.6
WORKDIR /scanner
COPY server.py .
COPY start.sh .
RUN chown -R clamav:clamav /scanner /var/lib/clamav
USER clamav
EXPOSE 8080
CMD ["sh","start.sh"]
