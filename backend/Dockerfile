FROM python:3.9-slim

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "foodgram_backend.wsgi:application", "--bind", "0:8000"]


