# -*- coding: utf-8 -*-
import scrapy
from find_my_bus.items import FindMyBusItem
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
    	if (len(self.urls)):
    		return Request(url % self.urls.pop())

    def parse(self, response):
        hxs = Selector(response, type='html')
       	horario = hxs.xpath('//div[contains(@class, "horario")]')

        titulo = horario.xpath('.//h1/a/text()').extract()[0]
        conteudo = horario.xpath('.//div')
        
        tmp = conteudo[0]
        dados = [i for i in tmp.xpath('.//text()').extract() if i != u' ']

        percurso = dados[3].strip()[0:5]
        tarifa = {
        	"cartao": dados[8].strip(),
        	"dinheiro": dados[10].strip(),
        }

        item = FindMyBusItem(nome=titulo)

        print dados
        print percurso
        print tarifa["cartao"]

        yield item
        yield self.make_requests_from_url(self.start_urls[0])
