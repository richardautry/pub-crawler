from pub_crawler.pub_crawler.spiders.beer_spider import *
from scrapy.http import TextResponse
import json
from collections import namedtuple
from pathlib import Path
from typing import Dict


# Helper functions for unpacking website test data
Website = namedtuple("Website", ["url", "html_filename"])
with open(
    Path.joinpath(Path.cwd(), Path(__file__).parent, "data/websites.json")
) as websites_file:
    website_json = json.load(websites_file)


website_data: Dict[str, Website] = {}
for key, val in website_json.items():
    website_data[key] = Website(
        url=val["url"],
        html_filename=Path.joinpath(
            Path.cwd(), Path(__file__).parent, val["html_filename"]
        ),
    )


def get_response(website: Website):
    """Returns a TextResponse object which is expected"""
    with open(website.html_filename, "rb") as f:
        response = TextResponse(url=website.url, body=f.read())
    return response


STONE_ENJOY_010122_DATA = website_data["stonebrewing_stone_enjoy_010122_ufiltered_ipa"]
STONE_IPA_DATA = website_data["stonebrewing_stone_ipa"]
NORTH_COAST_PRANQSTER_DATA = website_data[
    "north_coast_brewing_pranqster_belgian_style_golden_ale"
]
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

    north_coast_data: Website = website_data[
        "north_coast_brewing_pranqster_belgian_style_golden_ale"
    ]
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

    north_coast_data: Website = website_data[
        "north_coast_brewing_pranqster_belgian_style_golden_ale"
    ]
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

    north_data: Website = website_data[
        "north_coast_brewing_pranqster_belgian_style_golden_ale"
    ]
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
        field_spelling=["availability", "Availability", "AVAILABILITY"],
    )
    assert value == "CA & RVA"


def test_parse_abv_ardent():
    """
    Given website data a response object
    When the response is parsed
    Then it should yield 1 or more dictionaries with 'name', 'style' and 'abv'
    :return:
    """
    response = get_response(ARDENT_BREWING_MENU_DATA)
    value_gen = BeerSpider.parse_abv(response)

    expected_data = {
        "Altbier": {"name": "Altbier", "style": "Altbier", "abv": "5% ABV"},
        "Highpoint DIPA": {
            "name": "Highpoint DIPA",
            "style": "IPA - Imperial / Double",
            "abv": "8% ABV",
        },
        "Pomegranate Gose With Ginger & Mint": {
            "name": "Pomegranate Gose With Ginger & Mint",
            "style": "Sour - Fruited Gose",
            "abv": "4.5% ABV",
        },
        "Helles Lager": {
            "name": "Helles Lager",
            "style": "Lager - Helles",
            "abv": "4.5% ABV",
        },
        "Double Dry Hopped IPA": {
            "name": "Double Dry Hopped IPA",
            "style": "IPA - American",
            "abv": "6.8% ABV",
        },
        "Spiced Cranberry Gose": {
            "name": "Spiced Cranberry Gose",
            "style": "Sour - Fruited Gose",
            "abv": "4.5% ABV",
        },
        "Stronger Than Hate": {
            "name": "Stronger Than Hate",
            "style": "Stout - Imperial / Double Milk",
            "abv": "10% ABV",
        },
        "ESB": {
            "name": "ESB",
            "style": "Extra Special / Strong Bitter",
            "abv": "5.5% ABV",
        },
        "Summit DIPA": {
            "name": "Summit DIPA",
            "style": "IPA - Imperial / Double New England / Hazy",
            "abv": "8% ABV",
        },
        "Ardent Pilsner": {
            "name": "Ardent Pilsner",
            "style": "Pilsner - German",
            "abv": "5% ABV",
        },
        "Ardent IPA": {
            "name": "Ardent IPA",
            "style": "IPA - American",
            "abv": "6.8% ABV",
        },
        "Leigh Street DIPA": {
            "name": "Leigh Street DIPA",
            "style": "IPA - Imperial / Double",
            "abv": "8% ABV",
        },
        "Saison": {
            "name": "Saison",
            "style": "Farmhouse Ale - Saison",
            "abv": "6.7% ABV",
        },
        "Orchard Potluck: Dabinett": {
            "name": "Orchard Potluck: Dabinett",
            "style": "Cider - Traditional / Apfelwein",
            "abv": "8% ABV",
        },
        "Dark Rye": {
            "name": "Dark Rye",
            "style": "Stout - Imperial / Double",
            "abv": "9.8% ABV",
        },
        "Franconian Lager": {
            "name": "Franconian Lager",
            "style": "Lager - Munich Dunkel",
            "abv": "5.2% ABV",
        },
        "Cucumber Lemon Gose": {
            "name": "Cucumber Lemon Gose",
            "style": "Sour - Fruited Gose",
            "abv": "4.5% ABV",
        },
        "IPA X": {
            "name": "IPA X",
            "style": "IPA - New England / Hazy",
            "abv": "7.1% ABV",
        },
    }

    value_names = [data["name"] for data in list(value_gen)]

    assert (
        value_names[0] == "Altbier"
    ), "The first beer on Ardent's menu should be 'Altbier'. If not, the menu may be loading from the web."

    for expected_beer_name in list(expected_data.keys()):
        assert (
            expected_beer_name in value_names
        ), f"{expected_beer_name} not found in the Ardent beer menu. All expected beers should be present."
        for data in list(value_gen):
            if data["name"] == expected_beer_name:
                assert (
                    data == expected_data[expected_beer_name]
                ), "The extracted beer data does not match expected"


def test_parse_abv_stone_ipa():
    response = get_response(STONE_IPA_DATA)
    scraped_data = list(BeerSpider.parse_abv(response))

    expected_data = {
        "Stone IPA": {
            "abv": "6.9%",
            "name": "Stone IPA",
            "style": "IPA"
        }
    }

    value_names = [data["name"] for data in scraped_data]

    # assert value_names[0] == "Stone IPA"

    for expected_beer_name in list(expected_data.keys()):
        assert(
            expected_beer_name in value_names
        ), f"{expected_beer_name} not found on the Stone IPA site."
        for data in scraped_data:
            if data["name"] == expected_beer_name:
                assert (
                    data == expected_data[expected_beer_name]
                ), "The extracted beer data does not match expected"
