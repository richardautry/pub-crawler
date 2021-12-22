from flask import Flask, request
from flask_pymongo import PyMongo
from tasks import make_celery
from scrapy.crawler import CrawlerProcess
from pub_crawler.pub_crawler.spiders.beer_spider import BeerSpider
import json
from typing import List, Any
from bson.objectid import ObjectId

app = Flask(__name__)
# TODO: (2021-10-26) Create the root login (or some other login) on MongoDB instance.
app.config.update(
    # TODO: Change this hardcoded ip for rabbitmq
    CELERY_BROKER_URL='pyamqp://external:example@172.31.95.23:5672//',
    CELERY_RESULT_BACKEND='rpc://',
    # TODO: Change this hardcoded ip
    MONGO_URI='mongodb://root:password@172.31.89.136:27017/myDatabase?authSource=admin'
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
    process = CrawlerProcess(settings={
        "BOT_NAME": "pub_crawler",
        "SPIDER_MODULES": ["pub_crawler.pub_crawler.spiders"],
        "NEWSPIDER_MODULE": "pub_crawler.pub_crawler.spiders",
        "ITEM_PIPELINES": {
            "pub_crawler.pub_crawler.pipelines.MongoDBPipeline": 300,
        },
        "MONGODB_SERVER": "mongo",
        "MONGODB_PORT": 27017,
        "MONGO_URI": f"mongodb://root:password@172.31.89.136:27017/myDatabase?authSource=admin",
        "MONGODB_DATABASE": "myDatabase",
        "MONGODB_COLLECTION": "beer",
    })
    process.crawl(BeerSpider, url=url)
    process.start()
    return

