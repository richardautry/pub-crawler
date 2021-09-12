from flask import Flask, request
from flask_pymongo import PyMongo
from tasks import make_celery
from scrapy.crawler import CrawlerProcess
from pub_crawler.pub_crawler.spiders.beer_spider import BeerSpider
import json
from typing import List, Any
from bson.objectid import ObjectId

app = Flask(__name__)
print(app.name)
app.config.update(
    CELERY_BROKER_URL='pyamqp://guest@localhost://',
    CELERY_RESULT_BACKEND='rpc://',
    MONGO_URI='mongodb://localhost:27017/myDatabase'
)
mongo = PyMongo(app)
celery = make_celery(app)


def stringify(obj: Any, serialize_types: List[type]):
    """
    Takes a list of object or dictionary of objects and converts all non-serializable items
    into strings.
    :param obj:
    :param serialize_types: obj:
    :return:
    """
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = stringify(item, serialize_types)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            obj[key] = stringify(val, serialize_types)

    if type(obj) in serialize_types:
        obj = str(obj)
    return obj


@app.route("/get-data", methods=["POST"])
def get_data():
    assert request.method == "POST"
    crawl.delay(request.json["url"])
    return {
        "url": request.json["url"],
        "msg": "Starting Crawl..."
    }


@app.route("/")
def home_page():
    online_users = mongo.db.posts.find({"author": "Mike"})
    return json.dumps(stringify(list(online_users), [ObjectId]))


@celery.task()
def crawl(url: str):
    process = CrawlerProcess()
    process.crawl(BeerSpider, url=url)
    process.start()
    return

