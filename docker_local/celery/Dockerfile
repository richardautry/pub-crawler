FROM python:3.8-slim-buster

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

ENV BROKER_URL='amqp://guest@rabbitmq://'
ENV CELERY_BROKER_URL='pyamqp://guest@rabbitmq://'
ENV MONGO_URI='mongodb://root:password@mongo:27017/myDatabase?authSource=admin'

CMD ["python3", "-m", "celery", "-A", "app.celery", "worker"]