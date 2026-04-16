FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt uvicorn

# Pre-download NLTK data for sentence tokenization (claim decomposition)
RUN python -c "import nltk; nltk.download('punkt_tab', quiet=True)"

# Copy application code (only what the API needs)
COPY engine.py config.py api.py ./

# Pass at runtime: docker run -e GROQ_API_KEY=... image
# Without it, the API runs in offline mode (mock LLM responses)
ENV GROQ_API_KEY=""

# HF Spaces expects port 7860
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
