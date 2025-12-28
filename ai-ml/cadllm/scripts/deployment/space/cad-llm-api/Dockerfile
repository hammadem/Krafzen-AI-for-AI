# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# Based on Hugging Face's recommended Dockerfile format
FROM python:3.11-slim

# Create a non-root user (recommended by Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY --chown=user:user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user:user . /app

# Expose port (Spaces Docker uses port 7860)
EXPOSE 7860

# Run the application using uvicorn directly (recommended by Hugging Face)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
