# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class FindMyBusItem(scrapy.Item):
	# define the fields for your item here like:
	# name = scrapy.Field()
	
	nome = scrapy.Field()
	preco = scrapy.Field()
	empresa = scrapy.Field()
	horarios = scrapy.Field()
	itinerario = scrapy.Field()
	tempo_medio = scrapy.Field()
	modificacao = scrapy.Field()