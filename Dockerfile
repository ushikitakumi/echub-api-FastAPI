FROM mcr.microsoft.com/playwright/python:v1.32.0-focal

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python -m playwright install

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
