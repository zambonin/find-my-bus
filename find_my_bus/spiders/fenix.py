# -*- coding: utf-8 -*-

"""fenix.py

Spider tailored to a specific local business website that scrapes a page
with all the bus lines and, then, those pages to get the data.

    * `scrapy.http.Request` represents an HTTP request, usually generated in
        the spider and executed by the downloader, thus generating a Response.
    * `scrapy.selector.Selector` is a wrapper over response to select certain
        parts of its content.
    * `scrapy.spiders.init.InitSpider` is a spider (class that defines how
        a certain site will be scraped) with initialization facilities.
"""

from datetime import timedelta

from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spiders.init import InitSpider

from find_my_bus.items import FindMyBusItem


class FenixSpider(InitSpider):
    """Instantiates the Fenix spider."""
    name = "fenix"
    allowed_domains = ["consorciofenix.com.br"]
    start_urls = []

    def init_request(self):
        """Requests the base URL from the domain.

        Initializes communication with the site by feeding it information such
        as form data and request type.

        Returns:
            A FormRequest object with the necessary form submission data.
        """
        return Request(url='http://www.consorciofenix.com.br/horarios',
                       callback=self.organize)

    def organize(self, response):
        """Constructs the list of URLs that will be scraped.

        Prepares the URLs for the scraping, appending the necessary information
        so every URL is valid.

        Args:
            response (FormRequest): The object that contains the information
                                    about every item that will be scraped.

        Returns:
            self.initialized(): Specific method to Scrapy that starts the
                                crawling process.
        """
        source = Selector(response)
        links = source.xpath('//ul[contains(@class, "nav-custom1")]/li/a')

        for link in links:
            path = link.xpath('@href').extract()[0]
            self.start_urls.append("http://www.consorciofenix.com.br/" + path)

        return self.initialized()

    def parse(self, response):
        """Organizes the contents from each URL.

        Looks over the source code of its argument and parses information using
        Xpath manipulation.

        Args:
            response (Request): Any valid response generated from an URL.

        Yields:
            FindMyBusItem: Contains information about a bus line.
        """
        source = Selector(response)

        xpaths = {
            'code_name':
                source.xpath('//div[contains(@class, "horario")]/h1/a/text()'),
            'timetable':
                source.xpath('//div[contains(@class, "horario")]/div'),
            'itinerary':
                source.xpath('//div[contains(@class, "horario")]/ol/li/text()'),
            'price':
                source.xpath('//div[contains(@class, "tarifa")]/text()'),
            'time_date':
                source.xpath('//div[contains(@class, "col-sm-4")]/text()'),
            'route':
                source.xpath('//div[contains(@class, "mapac")]/img/@src'),
        }

        cod, name = xpaths['code_name'].extract()[0].split(" - ", 1)
        itinerary = xpaths['itinerary'].extract()

        price = {}
        price['card'], price['money'] = \
            map(str.strip, xpaths['price'].extract()[2:5:2])

        timetable = {}
        for section in xpaths['timetable'][3:-1]:
            horarios = ["".join(line.xpath('.//text()').extract()).strip()
                        for line in section.xpath('./div')]
            try:
                timetable[horarios.pop(0)] = horarios
            except IndexError:
                pass    # lines that only operate throughout the school year

        time, last_mod = map(str.strip, xpaths['time_date'].extract()[3:6:2])
        try:
            time = str(timedelta(minutes=int(
                time[time.find(':') + 1:time.find('a')])))
        except ValueError:
            time = "Não disponível."

        try:
            route = self.allowed_domains[0] + xpaths['route'].extract()[0]
        except IndexError:
            route = "Não disponível."

        yield {
            cod : FindMyBusItem(
                name=name, price=price, company="Consórcio Fênix",
                schedule=timetable, itinerary=itinerary,
                time=time, updated_at=last_mod, route=route)
        }
