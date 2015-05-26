# -*- coding: utf-8 -*-
import scrapy
import string
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
		"""
		Aggregate the proper FormRequest objects, initiating the communication 
		with the website.

		Returns:
			A FormRequest object with the necessary form submission data.
		"""
		return Request(url=self.start_urls[0] % "/horarios", 
						callback=self.organize)

	def organize(self, response):
		"""
		Build the set of URLs that will be accessed later in accordance to the
		form data received.

		Parameters:
			response: the previous FormRequest object.

		Returns:
			Calls the initialized() method that kickstarts the crawling (refer
			to scrapy docs).
		"""
		source = Selector(response)
		links = source.xpath('//ul[contains(@class, "nav-custom1")]/li/a')

		for link in links:
			path = link.xpath('@href').extract()[0]
			self.urls.append(path)

		return self.initialized()

	def make_requests_from_url(self, url):
		"""
		Formalize, for each URL that was constructed earlier, a request to read
		its contents.

		Parameters:
			url: a single URL to be requested from.

		Returns:
			A Request object for each one of the URLs from the main class array.
		"""
		if len(self.urls):
			return Request(url % self.urls.pop(), callback=self.parse)

	def parse(self, response):
		"""
		Organize the contents from each URL through xpath manipulation.

		Parameters:
			response: the reply from the earlier request.

		Returns:
			A FindMyBusItem object that contains the pertinent information about
			each bus line, yielding it so it can begin the process again through
			make_requests_from_url().
		"""
		source = Selector(response)

		horario = source.xpath('//div[contains(@class, "horario")]')

		temp_nome = horario.xpath('./h1/a/text()').extract()[0].split(" - ")
		nome_onibus = [temp_nome[-1], " ".join(temp_nome[:-1]).upper()]
		
		conteudo = horario.xpath('./div')

		dados = [it for it in conteudo[0].xpath('.//text()') \
										.extract() if it != u' ']

		tempo_medio = dados[3].strip()[3:5] + " minutos"

		preco = {
			"card": dados[9].strip(),
			"money": dados[11].strip(),
		}

		modificacao = dados[5].strip()[0:]

		conj_horarios = []

		for linha in conteudo[1:len(conteudo)-1]: 
			horarios = []
			horarios.append(linha.xpath('./div')[0].xpath('./h4/text()').extract()[0])
			for linha in linha.xpath('./div'):
				lista_horarios = linha.xpath('./a/text()').extract()
				if len(lista_horarios) > 0:
					horarios.append(lista_horarios[0].strip()[:5])
			conj_horarios.append(horarios)

		it = horario.xpath('./ol/li/text()').extract()
		itinerario = [it, [i for i in it[::-1]]]

		for conj in itinerario:
			if not conj:
				conj.append("Itinerário indisponível.")

		item = FindMyBusItem(name=nome_onibus, price=preco, 
							company="Consórcio Fênix", schedule=conj_horarios,
							itinerary=itinerario, time=tempo_medio, 
							updated_at=modificacao)

		yield item
		yield self.make_requests_from_url(self.start_urls[0])