# -*- coding: utf-8 -*-
# pylint: disable=W0511,R0201,R0914

"""biguacu.py

Spider tailored to a specific local business website, that needs to ignore
the AJAX-ridden website and use specific requests to get all the bus lines.

    * `scrapy.http.FormRequest` extends the base Request with functionality
        for dealing with HTML forms.
    * `scrapy.selector.Selector` is a wrapper over response to select certain
        parts of its content.
    * `scrapy.spiders.init.InitSpider` is a spider (class that defines how
        a certain site will be scraped) with initialization facilities.
"""

from __future__ import absolute_import
from datetime import timedelta
from re import findall
from urllib.request import urlopen

from scrapy.http import FormRequest
from scrapy.selector import Selector
from scrapy.spiders.init import InitSpider

from find_my_bus.items import FindMyBusItem


class BiguacuSpider(InitSpider):
    """Instantiates the Biguacu spider."""

    name = "biguacu"
    allowed_domains = ["biguacutransportes.com.br"]
    start_urls = []

    def init_request(self):
        """Requests the base URL from the domain.

        Initializes communication with the site by feeding it information such
        as form data and request type.

        Returns:
            A FormRequest object with the necessary form submission data.
        """
        # 1 for the main lines, 3 for the executive ones
        url = "http://www.biguacutransportes.com.br/ajax/lineBus/searchGetLine"
        return [
            FormRequest(
                url=url, formdata={"company": str(i)}, callback=self.organize
            )
            for i in [1, 3]
        ]

    def organize(self, response):
        """Constructs the list of URLs that will be scraped.

        Prepares the URLs for the scraping, appending the necessary information
        so every URL is valid.

        Args:
            response (FormRequest): the object that contains the information
                                    about every item that will be scraped.

        Returns:
            self.initialized(): specific method to Scrapy that starts the
                                crawling process.
        """
        url = "http://www.biguacutransportes.com.br/ajax/lineBus/preview/"
        links = [
            it.xpath("./td")[0].xpath("./text()")
            for it in Selector(response).xpath("//tr")
        ]

        # doesn't return self.initialized() if it isn't the last callback
        last = bool(len(self.start_urls))

        for link in links:
            self.start_urls.append(
                url + "?line={}&detail[]=1,2,3".format(link.extract()[0])
            )

        return self.initialized() if last else None

    def parse(self, response):
        """Organizes the contents from each URL.

        Looks over the source code of its argument and parses information using
        Xpath manipulation.

        Args:
            response (Request): Any valid response generated from an URL.

        Yields:
            FindMyBusItem: Contains information about a bus line.
        """

        def parse_map_info(line):
            """Organizes the contents for each URL.

            Organizes the contents from specific map URLs, searching
            for URLs that contain a certain combination of characters
            through regular expressions.

            Detailed breakdown of the expression used:
              http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+

                http          match the string literally
                [s]?          match `s` up to 1 time
                ://           match the string literally
                (?:           start of non-capturing group
                  [a-zA-Z0-9]   match any alphanumeric characters
                  |             or
                  [/_@.:~]      match one of the characters inside brackets
                )+            end of non-capturing group. it will be executed
                              until it finds no more matches

            Args:
                line (str): The ID for the bus line.

            Returns:
                A list of KML maps containing the routes for each bus line,
                or an error message.
            """
            url = "http://www.biguacutransportes.com.br/ajax/lineBus/map"
            pattern = "http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+"

            with urlopen(url + "?idLine={}&type=2".format(line)) as resp:
                matches = findall(pattern, str(resp.read()))
                return [m for m in matches if "kml" in m] or "Não disponível."

        source = Selector(response)

        xpaths = {
            "header": source.xpath(
                '//div/div[contains(@class, "cabecalho-linha")]/div//text()'
            ),
            "route": source.xpath('//div[@id="tabContent2"]/div/div/ul'),
            "timetable": source.xpath(
                '//div[contains(@class, "tabContent")]/div'
            ),
        }

        header = list(map(str.strip, xpaths["header"].extract()))
        last_mod, cod, name, avgtime = (
            header[3],
            *header[6].split(" ", 1),
            header[8],
        )

        # positive lookahead assertion and hack to prevent IndexError
        avgtime = str(
            timedelta(
                hours=int((findall(r"\d+(?=h | h)", avgtime) + [0])[0]),
                minutes=int((findall(r"\d+(?=m| m)", avgtime) + [0])[0]),
            )
        )

        price = {}
        if "s" in header[9]:
            price["card"] = "R$ " + header[12][:4]
            price["money"] = "R$ " + header[16]
        else:
            price["card"] = price["money"] = "R$ " + header[10]

        itinerary = []
        for conj in xpaths["route"]:
            route = (
                list(
                    map(
                        lambda x: x.split("-")[1].strip(),
                        conj.xpath("./li/text()").extract(),
                    )
                )
                or "Não disponível."
            )
            itinerary.append(route)

        timetable = {}
        for table in xpaths["timetable"]:
            start = table.xpath("./div/div/strong/text()").extract()[0]
            timetable[start] = {}

            days = table.xpath("./div/ul/li/div/strong/text()").extract()
            # TODO extract markers (wheelchair-enabled bus, different route)
            times = [
                hour.xpath("./div/ul/li/div/a/text()").extract()
                for hour in table.xpath("./div/ul/li")
            ]

            for day, time in zip(days, times):
                timetable[start][day] = time

        yield {
            cod: FindMyBusItem(
                name=name,
                price=price,
                company="Biguaçu Transportes",
                schedule=timetable,
                itinerary=itinerary,
                time=avgtime,
                updated_at=last_mod,
                route=parse_map_info(cod),
            )
        }
