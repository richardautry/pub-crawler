import scrapy
from urllib import parse
from typing import List


def parse_name_from_url(url: str):
    path = parse.urlparse(url).path
    if path[-1] == '/':
        path = path[:len(path) - 1]
    return path.split('/')[-1].split('-')


class BeerSpider(scrapy.Spider):
    name = "beer"

    def __init__(self, url, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.url = url

    def start_requests(self):
        # url = "https://northcoastbrewing.com/beers/"
        yield scrapy.Request(self.url, self.parse)

    def parse(self, response):
        # TODO: Try re-based search on elements with beer name for abv and get all text
        # for link in response.css("a").xpath("@href").getall():
        #     yield {
        #         "href": link.css("href").get()
        #     }
        links = response.css("a").xpath("@href")
        yield from response.follow_all(links, self.parse_abv)

    def parse_abv(self, response):
        """
        Basic method for finding abv in all links
        :param response:
        :return:
        """
        def extract_name():
            # TODO: Add check against name in url (parse url ie. 'http://.../red-seal-ale/' -> ['red', 'seal', 'ale']
            name_parts = parse_name_from_url(response.url)
            class_names = ["h1", "h2"]

            for class_name in class_names:
                class_results = response.css(class_name)
                for class_result in class_results:
                    class_text = class_result.xpath(".//text()").getall()
                    for text in class_text:
                        matches_found = [name_part.upper() in text.upper() for name_part in name_parts]

                        # TODO: This method works decently well, but it completely fails with URLs and names such as the following:
                        # https://northcoastbrewing.com/beers/year-round-beers/pranqster-belgian-style-golden-ale/>
                        # i.e. NAME: Pranqster, STYLE: Belgian..., URL PATH: 'pranqster-belgian...'
                        if any(matches_found):
                            return text
            return None

        def extract_value(field_spelling: List[str], regex: List[str]) -> [str, None]:
            """
            Given a list of spelling options, attempt to extract the value to the expected field name
            :param field_spelling: List of spelling options for a field name i.e. ['ABV', 'Alcohol by Volume', ...]
            :param regex
            :return:
            """
            # Common symbols that come after the field name
            post_symbols = [':']

            # Change spelling to upper for comparison
            transformed_spelling = [spelling.upper() for spelling in field_spelling]

            # Add Title Spelling
            title_spelling = [spelling.title() for spelling in transformed_spelling]
            transformed_spelling.extend(title_spelling)

            # Combine with symbols for optional spellings
            additional_spellings = [spelling + symbol for spelling in transformed_spelling for symbol in post_symbols]
            transformed_spelling.extend(additional_spellings)

            # Search by field-value pair (field_name -> parent -> value (as child))
            for spelling in transformed_spelling:
                abv_selectors = response.xpath(f"//*[text()='{spelling}']")
                if len(abv_selectors) > 0:
                    abv_parents = abv_selectors[0].xpath(".//..")
                    if len(abv_parents) > 0:
                        style_text = abv_parents[0].xpath('.//text()').getall()
                        for text in style_text:
                            stripped_text = text.strip()
                            if stripped_text and stripped_text.upper() not in transformed_spelling:
                                return stripped_text

            # Search by regex
            for pattern in regex:
                matches = response.xpath(f"//text()").re(pattern)
                if len(matches) > 0:
                    return matches[0]
            return None

        def extract_style():
            # TODO: Generalize this function to take spellings and return
            style_spelling = ['style', 'beer style']
            return extract_value(style_spelling, [])

        def extract_abv():
            abv_spelling = ['ABV', 'abv', 'alcohol by volume', 'ALCOHOL BY VOLUME', 'ALC. BY VOLUME']
            regex = [r'(?:ABV[: ~\xa0-]+)([0-9].*[0-9]*%)']
            return extract_value(abv_spelling, regex)

        # TODO:
        """
        3. Store data in json format temporarily for POC
        4. Explore other brewery sites and see what gets saved/missed
        5. Look at setting up data pipeline to mongodb instance
        6. Tests
        7. Traverse links gracefully around DNS errors
        8. Add `tags` for Style to regex in unstructured text with no "Style" indicator/field_name
        """

        yield {
            'name': extract_name(),
            'style': extract_style(),
            'ABV': extract_abv()
        }
