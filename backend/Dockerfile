FROM python:3.11-slim AS base

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code
COPY backend /app/backend

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run uvicorn
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
