# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.contrib.spiders.init import InitSpider

from find_my_bus.items import FindMyBusItem

class FenixSpider(InitSpider):
    name = "biguacu"
    allowed_domains = ["biguacutransportes.com.br"]
    start_urls = (
    	'http://www.biguacutransportes.com.br/ajax/lineBus/searchGetLine',
    )
    urls = []

    def init_request(self):
    	return Request(url=self.start_urls[0], method='POST', callback=self.parse)
    
    def parse(self, response):
        # return FormRequest.from_response(response, formdata={'company':'0'}, callback=self.organize)
        yield FormRequest(url=self.start_urls[0], formdata={'company':'1'}, callback=self.organize)

    def organize(self, response):
        hxs = Selector(response)
        links = hxs.xpath('//div')
        
    	for link in links:
    		path = link.extract()[0]
    		self.urls.append(path)

    	print links
    	return self.initialized()