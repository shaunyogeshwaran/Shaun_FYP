FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt uvicorn

# Copy application code (only what the API needs)
COPY engine.py config.py api.py ./

# HF Spaces expects port 7860
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
