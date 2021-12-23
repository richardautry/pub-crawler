FROM python:3.8-slim-buster

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

ENV CELERY_BROKER_URL='pyamqp://external:example@172.31.95.23:5672//'
ENV MONGO_URI='mongodb://root:password@172.31.89.136:27017/myDatabase?authSource=admin'

# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0", "app:app"]
ENTRYPOINT ["./gunicorn.sh"]