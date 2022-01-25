from pub_crawler.pub_crawler.spiders.beer_spider import *
from scrapy.http import TextResponse
import json
from collections import namedtuple
from pathlib import Path
from typing import Dict


# Helper functions for unpacking website test data
Website = namedtuple("Website", ["url", "html_filename"])
with open(Path.joinpath(Path.cwd(), Path(__file__).parent, "data/websites.json")) as websites_file:
    website_json = json.load(websites_file)


website_data: Dict[str, Website] = {}
for key, val in website_json.items():
    website_data[key] = Website(
        url=val["url"],
        html_filename=Path.joinpath(Path.cwd(), Path(__file__).parent, val["html_filename"])
    )


def get_response(website: Website):
    """Returns a TextResponse object which is expected """
    with open(website.html_filename, "rb") as f:
        response = TextResponse(
            url=website.url,
            body=f.read()
        )
    return response


STONE_ENJOY_010122_DATA = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
STONE_IPA_DATA = website_data["stonebrewing_stone_ipa"]
NORTH_COAST_PRANQSTER_DATA = website_data["north_coast_brewing_pranqster_belgian_style_golden_ale"]
ARDENT_BREWING_MENU_DATA = website_data["ardent_brewing_menu"]


# Tests
def test_get_additional_spellings():
    """Tests the `get_additional_spellings` function"""
    word = "double ipa"
    expected_spellings = ["Double IPA", "DOUBLE IPA", "double ipa"]
    actual_spellings = get_additional_spellings(word=word)
    for spelling in expected_spellings:
        assert spelling in actual_spellings


def test_parse_name_keywords_from_url():
    """Tests the `parse_name_keywords_from_url` function"""
    keywords = parse_name_keywords_from_url(STONE_ENJOY_010122_DATA.url)
    expected_keywords = ["stone", "enjoy", "010122", "unfiltered", "ipa"]
    assert all((keyword in expected_keywords for keyword in keywords))


def test_extract_name():
    """Tests the `extract_name` function"""
    stone_data: Website = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
    response = get_response(stone_data)
    name = extract_name(response)
    assert name == "Stone Enjoy By 01.01.22 Unfiltered IPA"

    north_coast_data: Website = website_data["north_coast_brewing_pranqster_belgian_style_golden_ale"]
    response = get_response(north_coast_data)
    name = extract_name(response)
    assert name == "PranQster"

    response = get_response(STONE_IPA_DATA)
    name = extract_name(response)
    assert name == "Stone IPA"

    response = get_response(ARDENT_BREWING_MENU_DATA)
    name = extract_name(response)
    assert name == "Altbier"


def test_extract_style():
    stone_data: Website = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
    response = get_response(stone_data)
    style = extract_style(response)
    assert style == "Double IPA"

    north_coast_data: Website = website_data["north_coast_brewing_pranqster_belgian_style_golden_ale"]
    response = get_response(north_coast_data)
    style = extract_style(response)
    assert style == "Belgian Style Golden Ale"

    response = get_response(STONE_IPA_DATA)
    style = extract_style(response)
    assert style == "IPA"


def test_extract_abv():
    stone_data: Website = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
    response = get_response(stone_data)
    abv = extract_abv(response)
    assert abv == "9.4%"

    north_data: Website = website_data["north_coast_brewing_pranqster_belgian_style_golden_ale"]
    response = get_response(north_data)
    abv = extract_abv(response)
    assert abv == "7.6%"

    response = get_response(STONE_IPA_DATA)
    abv = extract_abv(response)
    assert abv == "6.9%"


def test_extract_value():
    """Tests the `extract_value` function"""
    response = get_response(STONE_ENJOY_010122_DATA)
    value = extract_value(
        response=response,
        field_spelling=["availability", "Availability", "AVAILABILITY"]
    )
    assert value == "CA & RVA"
