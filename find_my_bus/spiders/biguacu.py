# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.contrib.spiders.init import InitSpider

from find_my_bus.items import FindMyBusItem

class BiguacuSpider(InitSpider):
	name = "biguacu"
	allowed_domains = ["biguacutransportes.com.br"]
	start_urls = (
		'http://www.biguacutransportes.com.br/ajax/lineBus/searchGetLine',
		'http://www.biguacutransportes.com.br/ajax/lineBus/preview/?line=%s&company=0&detail%%5B%%5D=1&detail%%5B%%5D=2&detail%%5B%%5D=3'
	)
	urls = []

	def init_request(self):
		return FormRequest(url=self.start_urls[0], formdata={'company':'1'}, callback=self.organize)

	def organize(self, response):
		hxs = Selector(response)
		links = [_.xpath('./td')[0].xpath('./text()') for _ in hxs.xpath('//tr')]
		
		for link in links:
			path = link.extract()[0]
			self.urls.append(self.start_urls[1] % path)

		# print self.urls
		return self.initialized()

	def make_requests_from_url(self, url):
		return Request(self.urls.pop(), callback=self.parse)

	def parse(self, response):
		hxs = Selector(response)
		cabecalho = hxs.xpath('//div/div')
		
		modificacao = cabecalho.xpath('//div')[3].xpath('./text()').extract()[0].strip()
		tempo_medio = cabecalho.xpath('//div')[6].xpath('./text()').extract()[0].strip()
		nome_onibus = cabecalho.xpath('//div')[0].xpath('//span/text()')[3].extract()
		preco = "R$" + cabecalho.xpath('//div')[0].xpath('//span/text()')[6].extract()

		# conj = hxs.xpath('//li/div')[0].xpath('./text()').extract()
		# conj = hxs.xpath('//strong')[1].extract()
		# horarios = hxs.xpath('//a/text()').extract()

		# item = FindMyBusItem(nome=nome_onibus, preco=preco, empresa="Biguaçu Transportes",
		# 	horarios=horarios, itinerario=itinerario, tempo_medio=tempo_medio, modificacao=modificacao)

		# yield item
		# yield self.make_requests_from_url(self.start_urls[0])