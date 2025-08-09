FROM python:3.11-slim

# Ensure stdout/stderr are unbuffered and no .pyc files are written
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system deps (optional, kept minimal for now)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    # watchdog improves Streamlit file watching and performance
    pip install watchdog

# Copy the application code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Default envs for container platforms
ENV PORT=8501

# Streamlit needs to bind to 0.0.0.0 in containers
CMD ["bash", "-lc", "streamlit run main.py --server.port ${PORT} --server.address 0.0.0.0"]


