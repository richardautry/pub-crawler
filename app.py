from flask import Flask, request
from tasks import make_celery

app = Flask(__name__)
print(app.name)
app.config.update(
    CELERY_BROKER_URL='pyamqp://guest@localhost://',
    CELERY_RESULT_BACKEND='rpc://'
)
celery = make_celery(app)


@app.route("/get-data", methods=["POST"])
def get_data():
    assert request.method == "POST"
    return {
        "url": request.json["url"],
        "result": add_together.delay(23, 42).wait()
    }


@celery.task()
def add_together(a, b):
    return a + b

