FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any needed (e.g., for psycopg2)
# libpq-dev is often needed for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY src/requirements_app.txt .
RUN pip install --no-cache-dir -r requirements_app.txt

# Copy source code
COPY src /app/src
# Create directories for volumes
RUN mkdir -p /app/dados /app/relatorios

EXPOSE 8501

CMD ["streamlit", "run", "src/app/main.py", "--server.runOnSave", "true", "--server.address", "0.0.0.0"]
