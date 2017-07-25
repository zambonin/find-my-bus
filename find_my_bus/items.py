# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item

class FindMyBusItem(Item):
    name, price, company, schedule, itinerary, \
        time, updated_at, route = (Field(),) * 8
