import scrapy
import pprint
from urllib import parse
from typing import List
from bs4 import BeautifulSoup
import re
from itertools import product
from scrapy_splash import SplashRequest


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
    name = div.find_all(class_=re.compile("beer-title|beer-name"))

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
        # TODO: Change back to original to parse all resulting links
        # yield SplashRequest(self.url, self.parse)
        yield SplashRequest(self.url, self.parse_abv)

    def parse(self, response):
        links = response.css("a").xpath("@href")
        for link in links:
            # yield from response.follow_all(links, self.parse_abv)
            yield SplashRequest(response.urljoin(link.get()), self.parse_abv)

    def parse_abv(self, response):
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
        self.logger.info("Parse function called on %s", response.url)
        response_soup = BeautifulSoup(response.body, "html.parser")

        # TODO:
        """
        There is some disconnect here between the return from splash (which should be `response.body`
        and what beautiful soup expects. bs4 does not seem to be able to parse out anything 
        from the resulting render.
        """
        names = response_soup.find_all(class_=re.compile("beer-title|beer-name"))
        names_text = [name.text for name in names]
        self.logger.info("%s: all names: %s", response.url, names_text)
        self.logger.info(response.text[:100])
        self.logger.info(response.body[:100])
        """
        Issues found in logs here, response.text is a string. reponse.body is bstring
        celery_1    | [2022-03-01 03:03:23,509: INFO/ForkPoolWorker-8] <!DOCTYPE html><html xmlns:og="http://opengraphprotocol.org/schema/" xmlns:fb="http://www.facebook.c
        celery_1    | [2022-03-01 03:03:23,509: WARNING/ForkPoolWorker-8] 2022-03-01 03:03:23 [beer] INFO: <!DOCTYPE html><html xmlns:og="http://opengraphprotocol.org/schema/" xmlns:fb="http://www.facebook.c
        celery_1    | 
        celery_1    | [2022-03-01 03:03:23,510: INFO/ForkPoolWorker-8] b'<!DOCTYPE html><html xmlns:og="http://opengraphprotocol.org/schema/" xmlns:fb="http://www.facebook.c'
        celery_1    | [2022-03-01 03:03:23,510: WARNING/ForkPoolWorker-8] 2022-03-01 03:03:23 [beer] INFO: b'<!DOCTYPE html><html xmlns:og="http://opengraphprotocol.org/schema/" xmlns:fb="http://www.facebook.c'
        """
        # self.logger.info("%s: response_soup: %s", response.url, response_soup.text)

        # TODO: No candidates because javascript is not loading untappd data
        # Docs say I may need to use Splash to make this work...
        # https://docs.scrapy.org/en/latest/topics/dynamic-content.html
        # https://github.com/scrapinghub/splash
        # https://github.com/scrapy-plugins/scrapy-splash
        candidates = response_soup.find_all(correct_elements_exist)
        self.logger.info("CANDIDATES: %s", candidates)
        data = []

        # TODO:
        """
        Biggest issue here is that the beer stats are somewhat standard (Style, ABV, IBUs)
        But the beer name is a complete wildcard, it could be a header, labeled in a list, or using "beer title" class
        
        """
        for candidate in candidates:
            d = {
                "name": remove_text_noise(
                    candidate.find(class_=re.compile("beer-title|beer-name")).text,
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
                self.logger.info("YIELDING %s", d)
                yield d

        # These functions are too expensive and hold up the spider for a significant time
        # Do not use unless substantially refactored for performance
        # if len(data) == 0:
        #     yield {
        #         'name': extract_name(response),
        #         'style': extract_style(response),
        #         'abv': extract_abv(response),
        #     }
