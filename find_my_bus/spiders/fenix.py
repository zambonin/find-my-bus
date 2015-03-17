# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.contrib.spiders.init import InitSpider

class FenixSpider(InitSpider):
    name = "fenix"
    allowed_domains = ["consorciofenix.com.br"]
    start_urls = (
        'http://www.consorciofenix.com.br%s',
    )
    urls = []

    def init_request(self):
    	return Request(url=self.start_urls[0] % "/horarios/", callback=self.organize)

    def organize(self, response):
        hxs = Selector(response)    	
        links = hxs.xpath('//ul[contains(@class, "nav-custom1")]/li/a')

        for link in links:
        	path = link.xpath('@href').extract()[0]
        	self.urls.append(path)

        return self.initialized()

    def make_requests_from_url(self, url):
    	return Request(url % self.urls.pop())

    def parse(self, response):
        hxs = Selector(response, type='html')
        horario = hxs.xpath('//div[contains(@class, "horario")]')
        titulo = hxs.xpath('.//h1/a/text()').extract()[0]
        print titulo
        yield self.make_requests_from_url(self.start_urls[0])
