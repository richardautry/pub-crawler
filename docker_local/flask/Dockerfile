FROM python:3.8-slim-buster

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

ENV CELERY_BROKER_URL='pyamqp://guest@rabbitmq://'
ENV MONGO_URI='mongodb://root:password@mongo:27017/myDatabase?authSource=admin'

# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0", "app:app"]
ENTRYPOINT ["./gunicorn.sh"]