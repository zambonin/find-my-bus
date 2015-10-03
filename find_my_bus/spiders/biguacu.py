# -*- coding: utf-8 -*-
import requests
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.spiders.init import InitSpider
from find_my_bus.items import FindMyBusItem


class BiguacuSpider(InitSpider):
    name = "biguacu"
    allowed_domains = ["biguacutransportes.com.br"]
    start_urls = (
        'http://www.biguacutransportes.com.br/ajax/lineBus/searchGetLine',
        'http://www.biguacutransportes.com.br/ajax/lineBus/preview/?line=%s%s',
    )

    urls = []

    def init_request(self):
        """Requests the base URL from the domain.

        Initializes communication with the site by feeding it information such
        as form data and request type.

        Yields:
            A FormRequest object with the necessary form submission data.
        """
        for i in [1, 3]:
            # 1 for the main lines, 3 for the executive ones
            yield FormRequest(url=self.start_urls[0],
                              formdata={'company': str(i)},
                              callback=self.organize)

    def organize(self, response):
        """Constructs the list of URLs that will be scraped.

        Prepares the URLs for the scraping, appending the necessary information
        so every URL is valid.

        Args:
            response (FormRequest): the object that contains the information
                                    about every item that will be scraped.

        Returns:
            self.initialized(): specific method to Scrapy that starts the
                                crawling process.
        """
        source = Selector(response)
        links = [it.xpath('./td')[0].xpath('./text()')
                 for it in source.xpath('//tr')]

        detail = '&detail[]=1,2,3'
        for link in links:
            path = link.extract()[0]
            self.urls.append(self.start_urls[1] % (path, detail))

        return self.initialized()

    def make_requests_from_url(self, url=None):
        """Requests the content from a given URL.

        Generates requests if given a valid URL from anywhere in the class,
        converting it to a valid Request object.

        Args:
            url (str): a single URL to be requested from.

        Returns:
            A Request object generated from the URL passed as an argument.
        """
        if len(self.urls):
            return Request(self.urls.pop(), callback=self.parse_bus_info)

    def parse_map_info(self, line):
        """Organizes the contents for each URL.

        Organizes the contents from specific map URLs, searching
        for URLs that contain a certain combination of characters
        through regular expressions.

        Detailed breakdown of the expression used:
            http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+

                http          match the string literally
                [s]?          match the character inside brackets up to 1 time
                ://           match the string literally
                (?:           start of non-capturing group
                  [a-zA-Z0-9]   match any alphanumeric characters
                  |             or
                  [/_@.:~]      match one of the characters inside brackets
                )+            end of non-capturing group. it will be executed
                              until it finds no more matches

        Args:
            line (str): The ID for the bus line.

        Returns:
            A list of KML maps containing the routes for each bus line.
        """
        import re

        url = 'http://www.biguacutransportes.com.br/ajax/lineBus/map?idLine=%s'
        r = requests.get(url % line, params={'type': '2'})

        out = re.findall('http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+', r.text)
        routes = [x for x in out if "kml" in x]

        if len(routes) > 0:
            return routes

        return "Mapa não disponível."

    def parse_bus_info(self, response):
        """Organizes the contents from each URL.

        Looks over the source code of its argument and parses information using
        Xpath manipulation.

        Args:
            response (Request): Any valid response generated from an URL.

        Yields:
            item (FindMyBusItem): Contains information about a bus line.
            make_requests_from_url (Request): The next bus line on the list,
                                              maintaning the process until
                                              there are no more URLs.
        """
        source = Selector(response)
        cabecalho = source.xpath('//div/div')

        nome_onibus = cabecalho.xpath('//div')[0].xpath(
            '//span/text()')[3].extract().strip().split(" ", 1)

        preco = {
            "card": 0,
            "money": 0,
        }
        if (len(cabecalho.xpath('//div')[0].xpath('//span/text()')) > 12):
            preco["card"] = "R$ " + cabecalho.xpath(
                '//div')[0].xpath('//span/text()')[8].extract().strip()[:4]
            preco["money"] = "R$" + cabecalho.xpath(
                '//div')[0].xpath('//sapn/text()').extract()[0]
        else:
            unico = "R$" + cabecalho.xpath(
                '//div')[0].xpath('//span/text()')[6].extract()
            preco["card"] = unico
            preco["money"] = unico

        modificacao = cabecalho.xpath(
            '//div')[3].xpath('./text()').extract()[0].strip()
        tempo_medio = cabecalho.xpath(
            '//div')[6].xpath('./text()').extract()[0].strip()

        itinerario = source.xpath(
            '//div[@id="tabContent2"]').xpath('./div/div/ul')
        itinerarios = []
        for conj in [linha.xpath('./li/text()').extract()
                     for linha in itinerario]:
            itinerarios.append([rua.split("-")[1].strip() for rua in conj])

        conteudo = source.xpath(
            '//div[contains(@class, "tabContent")]').xpath('./div')
        conj_horarios = []
        for content in conteudo:
            dias = content.xpath('./div/ul/li/div/strong/text()').extract()
            partida = content.xpath('./div/div/strong/text()').extract()

            lugares_saida = []
            for saida in dias:
                if not partida:
                    lugares_saida.append(saida)
                else:
                    lugares_saida.append(saida + " - " + partida[0].strip())

            horarios = content.xpath('./div/ul/li')
            for saida, horario in zip(lugares_saida, horarios):
                lista_horas = horario.xpath(
                    './div/ul/li/div/a/text()').extract()
                if lista_horas is not None:
                    conj_horarios.append([saida] + lista_horas)

        for conj in itinerarios:
            if not conj:
                conj.append("Itinerário indisponível.")

        rota = self.parse_map_info(nome_onibus[0])

        item = FindMyBusItem(name=nome_onibus, price=preco,
                             company="Biguaçu Transportes",
                             schedule=conj_horarios, itinerary=itinerarios,
                             time=tempo_medio, updated_at=modificacao,
                             route=rota)

        yield item
        yield self.make_requests_from_url()
