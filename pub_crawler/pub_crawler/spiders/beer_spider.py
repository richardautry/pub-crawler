import scrapy
import pprint
from urllib import parse
from typing import List
from bs4 import BeautifulSoup
import re
from itertools import product


pp = pprint.PrettyPrinter(indent=4)


def get_additional_spellings(
    word: str, post_symbols: [List[str], None] = None
) -> List[str]:
    words = word.split(" ")

    spellings = [[word, word.upper(), word.title()] for word in words]

    if post_symbols:
        for spelling_list in spellings:
            spelling_list.extend([word + post_symbol for post_symbol in post_symbols])

    spellings_product = list(product(*spellings))

    return [" ".join(spelling_product) for spelling_product in spellings_product]


def remove_text_noise(text: str, remove_values: List[str] = None):
    """class="beer
    Returns the first trimmed line of any text blob
    :param text: Some string that may have multiple lines or white
    :param remove_values: Values that should be removed and not considered in the result
    :return:
    """
    if remove_values:
        for remove_value in remove_values:
            text = text.replace(remove_value, "")
    return text.strip().split("\n")[0].strip()


def parse_name_keywords_from_url(url: str) -> List[str]:
    """
    Parses out all name keywords from the end path of the url

    :param url: Standard formatted url string
    :return: List of all name keywords in the path
    """
    path = parse.urlparse(url).path
    if path[-1] == "/":
        path = path[: len(path) - 1]
    return path.split("/")[-1].split("-")


def extract_name(response: scrapy.http.TextResponse):
    name_parts = parse_name_keywords_from_url(response.url)
    class_names = ["h1", "h2"]

    for class_name in class_names:
        class_results = response.css(class_name)
        for class_result in class_results:
            class_text = class_result.xpath(".//text()").getall()
            for text in class_text:
                matches_found = [
                    name_part.upper() in text.upper() for name_part in name_parts
                ]
                if any(matches_found):
                    return text
    return None


def extract_style(response: scrapy.http.TextResponse):
    style_spelling = ["style", "beer style"]

    # First attempt to retrieve style by key, val pair
    extracted_value = extract_value(response, style_spelling, [])
    if extracted_value:
        return extracted_value

    # Use style tags and regex if as last resort
    # TODO: Move tags and META type data to database
    style_tags = [
        "dark",
        "saison",
        "red",
        "wine",
        "red wine" "red ale",
        "flanders red",
        "barrel",
        "aged",
        "barrel aged",
        "russian",
        "imperial",
        "stout",
        "russian imperial stout",
        "imperial stout",
        "lager",
        "IPA",
        "india pale ale",
        "hazy",
        "pils",
        "pilsner",
        "gose",
        "porter",
        "baltic",
        "baltic porter",
        "bock",
        "style",
        "czech",
        "czech pilsner",
        "czech style pilsner",
        "oatmeal",
        "oatmeal stout",
    ]

    matches = []
    found_tags_map = []

    # TODO: Why does this take so long to process and eventually die?
    for tag in style_tags:
        original_regex_tag = "(.*\\b{}).*"
        regex_tag = original_regex_tag.format(tag)
        for f in ["upper", "title"]:
            altered_regex = original_regex_tag.format(getattr(tag, f)())
            regex_tag += f"|{altered_regex}"

        # Add text that includes the given spellings of a style tag
        # matches.append(extract_value([], [regex_tag]))
        current_matches = response.xpath("//text()").re(regex_tag)
        if len(current_matches) > 0:
            for current_match in current_matches:
                if current_match and "jQuery" not in current_match:
                    matches.append(current_match)
                    # Add the found tags to the map to be used in the score function
                    found_tags_map.append((current_match, tag))

    # Collect counts of each
    counts_dict = {match: matches.count(match) for match in matches}

    if counts_dict:
        # Calculate score based on tags found and amount of extra text
        found_tags_dict = {}
        for text, tag in found_tags_map:
            found_tags_dict.setdefault(text, []).append(tag)

        for text in counts_dict.keys():
            counts_dict[text] -= len(text) / len("".join(found_tags_dict[text]))

        return max(counts_dict, key=counts_dict.get)

    print("WARNING: No style tags found on page!")
    return None


def extract_abv(response: scrapy.http.TextResponse):
    abv_spelling = [
        "ABV",
        "abv",
        "alcohol by volume",
        "ALCOHOL BY VOLUME",
        "ALC. BY VOLUME",
    ]
    regex = [r"(?:ABV[: ~\xa0-]+)([0-9].*[0-9]*%)"]
    return extract_value(response, abv_spelling, regex)


def extract_value(
    response: scrapy.http.TextResponse,
    field_spelling: List[str],
    regex: List[str] = None,
) -> [str, None]:
    """
    Given a list of spelling options, attempt to extract the value to the expected field name

    :param response: A TextResponse object
    :param field_spelling: List of spelling options for a field name i.e. ['ABV', 'Alcohol by Volume', ...]
    :param regex
    :return:
    """
    # Common symbols that come after the field name
    post_symbols = [":"]

    # Change spelling to upper for comparison
    transformed_spelling = [spelling.upper() for spelling in field_spelling]

    # Add Title Spelling
    title_spelling = [spelling.title() for spelling in transformed_spelling]
    transformed_spelling.extend(title_spelling)

    # Combine with symbols for optional spellings
    additional_spellings = [
        spelling + symbol
        for spelling in transformed_spelling
        for symbol in post_symbols
    ]
    transformed_spelling.extend(additional_spellings)

    # Search by field-value pair (field_name -> parent -> value (as child))
    for spelling in transformed_spelling:
        abv_selectors = response.xpath(f"//*[text()='{spelling}']")
        if len(abv_selectors) > 0:
            abv_parents = abv_selectors[0].xpath(".//..")
            if len(abv_parents) > 0:
                style_text = abv_parents[0].xpath(".//text()").getall()
                for text in style_text:
                    stripped_text = text.strip()
                    if (
                        stripped_text
                        and stripped_text.upper() not in transformed_spelling
                    ):
                        return stripped_text

    # Search by regex
    if regex:
        for pattern in regex:
            matches = response.xpath("//text()").re(pattern)
            if len(matches) > 0:
                return matches[0]
    return None


def correct_elements_exist(div):
    name = div.find_all(class_=re.compile("beer-title"))

    style_spellings = "|".join(["style", "beer style", "beer-style"])
    style = div.find_all(class_=re.compile("beer-style"))
    abv = div.find_all(class_=re.compile("abv"))

    few_elements_found = (0 < len(elements) < 5 for elements in [abv, name, style])
    return all(few_elements_found)


class BeerSpider(scrapy.Spider):
    name = "beer"

    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url

    def start_requests(self):
        yield scrapy.Request(self.url, self.parse)

    def parse(self, response):
        links = response.css("a").xpath("@href")
        yield from response.follow_all(links, self.parse_abv)

    @staticmethod
    def parse_abv(response):
        """
        Basic method for finding abv in all links
        :param response:
        :return:
        """
        # TODO:
        """
        6. Tests
        7. Traverse links gracefully around DNS errors
        8. Refactor `extract_style` to separate out functions by purpose
        9. Explore spider crashes on long crawls
        10. Change priority of style extraction: Should be 1. Return field, value 2. Get style by tags
        """
        response_soup = BeautifulSoup(response.text, "html.parser")
        candidates = response_soup.find_all(correct_elements_exist)
        data = []
        for candidate in candidates:
            d = {
                "name": remove_text_noise(
                    candidate.find(class_=re.compile("name")).text,
                    remove_values=["name", "title"]
                ),
                "style": remove_text_noise(
                    candidate.find(class_=re.compile("beer-style")).text,
                    remove_values=["style", "Style", "Beer Style"]
                ),
                "abv": remove_text_noise(
                    candidate.find(class_=re.compile("abv")).text,
                    remove_values=["abv", "ABV"]
                ),
            }
            if d not in data:
                data.append(d)
                yield d

        # yield {
        #     'name': extract_name(response),
        #     'style': extract_style(response),
        #     'ABV': extract_abv(response),
        #     'url': response.url
        # }
