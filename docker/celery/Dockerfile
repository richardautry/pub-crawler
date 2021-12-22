FROM python:3.8-slim-buster

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

ENV BROKER_URL='amqp://external:example@172.31.95.23:5672//'

CMD ["python3", "-m", "celery", "-A", "app.celery", "worker"]