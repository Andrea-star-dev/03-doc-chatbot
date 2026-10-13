FROM python:3.11-slim

RUN addgroup --system app && adduser --system --ingroup app --uid 10001 app

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/data && chown -R app:app /app

ENV DOC_CHATBOT_DATA_DIR=/app/data
EXPOSE 8000

USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
