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

        titulo = horario.xpath('./h1/a/text()').extract()[0]
        conteudo = horario.xpath('./div')
        
        tmp = conteudo[0]
        dados = [i for i in tmp.xpath('.//text()').extract() if i != u' ']

        percurso = dados[3].strip()[:5]
        tarifa = {
        	"cartao": dados[8].strip(),
        	"dinheiro": dados[10].strip(),
        }

        conj_horarios = {}

        for i in conteudo[1:]:
        	linhas = i.xpath('./div')
        	nome = linhas[0].xpath('./h4/text()').extract()[0]
        	horarios = []
        	for j in linhas[1:]:
        		horarios.append(j.xpath('./a/text()').extract()[0].strip()[:5])
        	conj_horarios[nome] = horarios

        itinerario = horario.xpath('./ol/li/text()').extract()

        #item = FindMyBusItem(nome=titulo, preco=tarifa,
         empresa="Consórcio Fênix", horarios=conj_horarios, 
         itinerario=itinerario)

	item = FindMyBuyItem(itinerario=itinerario, horarios=conj_horarios, empresa="Consórcio Fênix", preco=tarifa, nome=titulo)
        yield item
        yield self.make_requests_from_url(self.start_urls[0])
