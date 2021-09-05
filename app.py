from flask import Flask, request
from tasks import make_celery
from scrapy.crawler import CrawlerProcess
from pub_crawler.pub_crawler.spiders.beer_spider import BeerSpider
from pub_crawler.pub_crawler import settings

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
    crawl.delay(request.json["url"])
    return {
        "url": request.json["url"],
        "msg": "Starting Crawl..."
    }


@celery.task()
def crawl(url: str):
    process = CrawlerProcess()
    process.crawl(BeerSpider, url=url)
    process.start()
    return

