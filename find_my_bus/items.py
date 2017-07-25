# -*- coding: utf-8 -*-

"""items.py

Models for scraped items with capabilities similar to a dictionary.

    * `scrapy.Field` specifies metadata for each field. None are needed
        for this kind of scraper.
    * `scrapy.Item` aggregates data to define a common output format.
"""

from scrapy import Field, Item

class FindMyBusItem(Item):
    """
    Custom container that collects scraped data pertinent to a bus line.
    """
    name, price, company, schedule, itinerary, \
        time, updated_at, route = (Field(),) * 8
