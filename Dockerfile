FROM python:3.13.3

WORKDIR /app

COPY requirements.txt .
COPY .env .
RUN pip install -r requirements.txt