import scrapy
import pprint
from urllib import parse
from typing import List


pp = pprint.PrettyPrinter(indent=4)


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
        yield scrapy.Request(self.url, self.parse)

    def parse(self, response):
        links = response.css("a").xpath("@href")
        yield from response.follow_all(links, self.parse_abv)

    def parse_abv(self, response):
        """
        Basic method for finding abv in all links
        :param response:
        :return:
        """
        def extract_name():
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
                matches = response.xpath("//text()").re(pattern)
                if len(matches) > 0:
                    return matches[0]
            return None

        def extract_style():
            style_spelling = ['style', 'beer style']

            # First attempt to retrieve style by key, val pair
            extracted_value = extract_value(style_spelling, [])
            if extracted_value:
                return extracted_value

            # Use style tags and regex if as last resort
            # TODO: Move tags and META type data to database
            style_tags = [
                'dark',
                'saison',
                'red',
                'wine',
                'red wine'
                'red ale',
                'flanders red',
                'barrel',
                'aged',
                'barrel aged',
                'russian',
                'imperial',
                'stout',
                'russian imperial stout',
                'imperial stout',
                'lager',
                'IPA',
                'india pale ale',
                'hazy',
                'pils',
                'pilsner',
                'gose',
                'porter',
                'baltic',
                'baltic porter',
                'bock',
                'style',
                'czech',
                'czech pilsner',
                'czech style pilsner',
                'oatmeal',
                'oatmeal stout'
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
                    counts_dict[text] -= len(text) / len(''.join(found_tags_dict[text]))

                return max(counts_dict, key=counts_dict.get)

            print("WARNING: No style tags found on page!")
            return None

        def extract_abv():
            abv_spelling = ['ABV', 'abv', 'alcohol by volume', 'ALCOHOL BY VOLUME', 'ALC. BY VOLUME']
            regex = [r'(?:ABV[: ~\xa0-]+)([0-9].*[0-9]*%)']
            return extract_value(abv_spelling, regex)

        # TODO:
        """
        5. Look at setting up data pipeline to mongodb instance
        6. Tests
        7. Traverse links gracefully around DNS errors
        8. Refactor `extract_style` to separate out functions by purpose
        9. Explore spider crashes on long crawls
        10. Change priority of style extraction: Should be 1. Return field, value 2. Get style by tags
        12. Work on spider as a service issues. How will this run? 
        """

        yield {
            'name': extract_name(),
            'style': extract_style(),
            'ABV': extract_abv(),
            'url': response.url
        }
