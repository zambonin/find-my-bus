# -*- coding: utf-8 -*-
import scrapy
import string
from find_my_bus.items import FindMyBusItem
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spiders.init import InitSpider

class FenixSpider(InitSpider):
	name = "fenix"
	allowed_domains = ["consorciofenix.com.br"]
	start_urls = (
		'http://www.consorciofenix.com.br/%s',
	)

	urls = []

	def init_request(self):
		"""Requests the base URL from the domain.

		Initializes communication with the site by feeding it information such
		as form data and request type.

		Returns:
			A FormRequest object with the necessary form submission data.
		"""
		return Request(url=self.start_urls[0] % "horarios", 
						callback=self.organize)

	def organize(self, response):
		"""Constructs the list of URLs that will be scraped.

		Prepares the URLs for the scraping, appending the necessary information
		so every URL is valid.

		Args:
			response (FormRequest): The object that contains the information
									about every item that will be scraped.

		Returns:
			self.initialized(): Specific method to Scrapy that starts the
								crawling process.
		"""
		source = Selector(response)
		links = source.xpath('//ul[contains(@class, "nav-custom1")]/li/a')

		for link in links:
			path = link.xpath('@href').extract()[0]
			self.urls.append(path)

		return self.initialized()

	def make_requests_from_url(self, url):
		"""Requests the content from a given URL.

		Generates requests if given a valid URL from anywhere in the class,
		converting it to a valid Request object.

		Args:
			url (str): A single URL to be requested from.

		Returns:
			A Request object generated from the URL passed as an argument.
		"""
		if len(self.urls):
			return Request(url % self.urls.pop(), callback=self.parse)

	def parse(self, response):
		"""Organizes the contents from each URL.

		Looks over the source code of its argument and parses information using
		Xpath manipulation.

		Args:
			response (Request): Any valid response generated from an URL.

		Yields:
			item (FindMyBusItem): Contains information about a bus line.
			make_requests_from_url (Request): The next bus line on the list, 
											  maintaning the process until there
											  are no more URLs.
		"""
		source = Selector(response)

		horario = source.xpath('//div[contains(@class, "horario")]')

		temp_nome = horario.xpath('./h1/a/text()').extract()[0].split(" - ")
		nome_onibus = [temp_nome[-1], " ".join(temp_nome[:-1]).upper()]
		
		conteudo = horario.xpath('./div')

		dados = [it for it in conteudo[0].xpath('.//text()').extract() if it != u' ']

		minutos = dados[3].strip()[3:5]
		if minutos.isdigit():
			if (int(minutos) / 60 > 0):
				tempo_medio = str(int(minutos) / 60) + "h " \
							+ str(int(minutos) % 60) + "min"
			else:
				tempo_medio = minutos + " minutos"
		else:
			tempo_medio = "Não disponível."

		preco = {
			"card": dados[9].strip(),
			"money": dados[11].strip(),
		}

		modificacao = dados[5].strip()[0:]

		conj_horarios = []

		for linha in conteudo[1:len(conteudo)-1]: 
			saida = linha.xpath('./div')[0].xpath('./h4/text()').extract()[0].split(" - ")
			horarios = []
			horarios.append(saida[0] + " - " + saida[1])
			for linha in linha.xpath('./div'):
				lista_horarios = linha.xpath('./a/text()').extract()
				if len(lista_horarios) > 0:
					horarios.append(lista_horarios[0].strip()[:5])
			conj_horarios.append(horarios)

		it = horario.xpath('./ol/li/text()').extract()

		for conj in it:
			if not conj:
				conj.append("Itinerário indisponível.")

		if source.xpath('//div[contains(@class, "mapac")]/img/@src').extract():
			map_url = "http://www.consorciofenix.com.br/r/w/mapas/1000x1000/"
			rota = map_url + nome_onibus[0] + ".jpg"
		else:
			rota = "Mapa não disponível."

		item = FindMyBusItem(name=nome_onibus, price=preco, 
							company="Consórcio Fênix", schedule=conj_horarios,
							itinerary=it, time=tempo_medio, 
							updated_at=modificacao, route=rota)

		yield item
		yield self.make_requests_from_url(self.start_urls[0])
