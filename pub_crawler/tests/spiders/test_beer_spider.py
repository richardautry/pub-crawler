from pub_crawler.pub_crawler.spiders.beer_spider import *
from scrapy.http import TextResponse


def test_extract_name():
    with open("./html/stonebrewing_stone_enjoy_010122_ufiltered_ipa.html", "rb") as f:
        response = TextResponse(
            url="https://www.stonebrewing.com/beer/stone-enjoy-ipa-series/stone-enjoy-010122-unfiltered-ipa",
            body=f.read()
        )

    name = extract_name(response)
    assert name == "Stone Enjoy By 01.01.22 Unfiltered IPA"
