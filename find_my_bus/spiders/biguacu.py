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

		return self.initialized()

	def make_requests_from_url(self, url):
		if(len(self.urls)):
			return Request(self.urls.pop(), callback=self.parse)

	def parse(self, response):
		hxs = Selector(response)
		cabecalho = hxs.xpath('//div/div')
		
		nome_onibus = cabecalho.xpath('//div')[0].xpath('//span/text()')[3].extract()
		preco = "R$"+ cabecalho.xpath('//div')[0].xpath('//span/text()')[6].extract()
		modificacao = cabecalho.xpath('//div')[3].xpath('./text()').extract()[0].strip()
		tempo_medio = cabecalho.xpath('//div')[6].xpath('./text()').extract()[0].strip()

		conteudo = hxs.xpath('//div[contains(@class, "tabContent")]').xpath('./div')
		conj_horarios = {}

		itinerario = hxs.xpath('//div[@id="tabContent2"]').xpath('./div/div/ul')

		itinerarios = []
		for a in [i.xpath('./li/text()').extract() for i in itinerario]:
			itinerarios.append([b.split("-")[1].strip() for b in a])
	
		for i in conteudo[0:]:
			dias = i.xpath('./div/ul/li/div/strong/text()').extract()
			partida = i.xpath('./div/div/strong/text()').extract()
			time = i.xpath('./div/ul/li')

			keys = []

			for k in dias:
				if not partida:
					keys.append(k)
				else:
					keys.append(k + " - " + partida[0])

			for j in time[0:]:
				for m in range(0, len(keys)):
					conj_horarios[keys[m]] = j.xpath('./div/ul/li/div/a/text()').extract()
		
		item = FindMyBusItem(nome=nome_onibus, preco=preco, empresa="Biguaçu Transportes",
			horarios=conj_horarios, itinerario=itinerarios, tempo_medio=tempo_medio, modificacao=modificacao)

		yield item
		yield self.make_requests_from_url(self.start_urls[0])
