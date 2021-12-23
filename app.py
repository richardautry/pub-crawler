from flask import Flask, request
from flask_pymongo import PyMongo
from tasks import make_celery
from scrapy.crawler import CrawlerProcess
from pub_crawler.pub_crawler.spiders.beer_spider import BeerSpider
import json
from typing import List, Any
from bson.objectid import ObjectId
from os import getenv
from pydantic import BaseModel, parse_obj_as

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=getenv('CELERY_BROKER_URL'),
    CELERY_RESULT_BACKEND='rpc://',
    MONGO_URI=getenv('MONGO_URI')
)
mongo = PyMongo(app)
celery = make_celery(app)


class Beer(BaseModel):
    _id: ObjectId
    name: str
    style: str
    ABV: str
    url: str


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


@app.route("/crawl", methods=["POST"])
def crawl():
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


@app.route("/data", methods=["GET"])
def get_data():
    # TODO: Get DB/Validation to a point where we can use Pydantic. Right now it invalidates loosely defined data
    data = mongo.db.scrapy_items.find()
    # beers = [Beer(**beer_data) for beer_data in data]
    return json.dumps(stringify(list(data), [ObjectId]), indent=4)
    # return json.dumps([beer.dict() for beer in beers])


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
        "MONGO_URI": app.config.MONGO_URI,
        "MONGODB_DATABASE": "myDatabase",
        "MONGODB_COLLECTION": "beer",
    })
    process.crawl(BeerSpider, url=url)
    process.start()
    return

