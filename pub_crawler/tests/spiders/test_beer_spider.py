from pub_crawler.pub_crawler.spiders.beer_spider import *
from scrapy.http import TextResponse
import json
from collections import namedtuple
from pathlib import Path


Website = namedtuple("Website", ["url", "html_filename"])
with open(Path.joinpath(Path.cwd(), Path(__file__).parent, "data/websites.json")) as websites_file:
    website_data = json.load(websites_file)


for key, val in website_data.items():
    website_data[key] = Website(
        url=val["url"],
        html_filename=Path.joinpath(Path.cwd(), Path(__file__).parent, val["html_filename"])
    )


def test_parse_name_from_url():
    pass


def test_extract_name():
    stone_data: Website = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
    with open(stone_data.html_filename, "rb") as f:
        response = TextResponse(
            url=stone_data.url,
            body=f.read()
        )
    name = extract_name(response)
    assert name == "Stone Enjoy By 01.01.22 Unfiltered IPA"

    north_coast_data: Website = website_data["north_coast_brewing_pranqster_belgian_style_golden_ale"]
    with open(north_coast_data.html_filename, "rb") as f:
        response = TextResponse(
            url="https://northcoastbrewing.com/beers/year-round-beers/pranqster-belgian-style-golden-ale/",
            body=f.read()
        )
    name = extract_name(response)
    assert name == "PranQster"


def test_extract_style():
    stone_data: Website = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
    response = TextResponse(
        url=stone_data.url,
        body=open(stone_data.html_filename, "rb").read()
    )
    style = extract_style(response)
    assert style == "Double IPA"

    north_coast_data: Website = website_data["north_coast_brewing_pranqster_belgian_style_golden_ale"]
    response = TextResponse(
        url=north_coast_data.url,
        body=open(north_coast_data.html_filename, "rb").read()
    )
    style = extract_style(response)
    assert style == "Belgian Style Golden Ale"


def test_extract_abv():
    pass


def test_extract_value():
    pass
