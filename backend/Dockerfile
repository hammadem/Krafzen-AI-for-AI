FROM python:3.12-slim
# Create a non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install system dependencies (potrace for local DXF conversion)
RUN apt-get update && apt-get install -y \
    potrace \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
