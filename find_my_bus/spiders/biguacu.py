# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.contrib.spiders.init import InitSpider
from pprint import pprint

from find_my_bus.items import FindMyBusItem

class BiguacuSpider(InitSpider):
    name = "biguacu"
    allowed_domains = ["biguacutransportes.com.br"]
    start_urls = (
        'http://www.biguacutransportes.com.br/ajax/lineBus/searchGetLine',
        'http://www.biguacutransportes.com.br/ajax/lineBus/preview/?line=%s&detail%%5B%%5D=1&detail%%5B%%5D=2&detail%%5B%%5D=3',
        'http://www.biguacutransportes.com.br/ajax/lineBus/map?idLine=%s&type=2'
    )

    bus_info, map_info, maps = [], [], []

    def init_request(self):
        """
        Aggregate the proper FormRequest objects, initiating the communication 
        with the website.

        Returns:
            A FormRequest object with the necessary form submission data.
        """
        for i in [1, 3]:
            # 1 for the main lines, 3 for the executive ones
            yield FormRequest(url=self.start_urls[0], 
                            formdata={'company': str(i)}, 
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
        links = [it.xpath('./td')[0].xpath('./text()') 
                for it in source.xpath('//tr')]

        for link in links:
            path = link.extract()[0]
            self.bus_info.append(self.start_urls[1] % path)
            self.map_info.append(self.start_urls[2] % path)

        return self.initialized()

    def make_requests_from_url(self, url=None):
        """
        Formalize, for each URL that was constructed earlier, a request to read 
        its contents.

        Parameters:
            url: a single URL to be requested from.

        Returns:
            A Request object for each one of the URLs from the main class array.
        """
        if len(self.map_info):
            return Request(self.map_info.pop(), callback=self.parse_map_info)
        elif len(self.bus_info):
            return Request(self.bus_info.pop(), callback=self.parse_bus_info)

    def parse_map_info(self, response):
        """
        Organize the contents from specific map URLs through xpath manipulation,
        searching for URLs that contain a specific combination of characters
        through regular expressions.

        Detailed breakdown of the expression used:
            http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+

                http            match the string literally
                [s]?            match the character inside brackets up to 1 time
                ://             match the string literally
                (?:             start of non-capturing group
                    [a-zA-Z0-9]     match any alphanumeric characters
                    |               or
                    [/_@.:~]        match one of the characters inside brackets
                )+              end of non-capturing group. it will be executed
                                until it finds no more matches

        Parameters:
            response: the reply from the earlier request.

        Returns:
            A FindMyBusItem object that contains the pertinent information about
            each bus line, yielding it so it can begin the process again through
            make_requests_from_url().
        """
        import re

        source = Selector(response)
        kml_js = source.xpath('//script/text()').extract()

        out = re.findall('http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+', str(kml_js))
        routes = [x for x in out if "kml" in x]

        if len(routes) > 0:
            self.maps.append(routes)

        return self.make_requests_from_url()

    def parse_bus_info(self, response):
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
        cabecalho = source.xpath('//div/div')

        preco = {
            "card": 0,
            "money": 0,
        }

        nome_onibus = cabecalho.xpath('//div')[0].xpath('//span/text()')[3].extract().strip().split(" ", 1)
        if (len(cabecalho.xpath('//div')[0].xpath('//span/text()')) > 12):
            preco["card"] = "R$ " + cabecalho.xpath('//div')[0].xpath('//span/text()')[8].extract().strip()[:4]
            preco["money"] = "R$" + cabecalho.xpath('//div')[0].xpath('//sapn/text()').extract()[0]
        else:
            unico = "R$" + cabecalho.xpath('//div')[0].xpath('//span/text()')[6].extract()
            preco["card"] = unico
            preco["money"] = unico

        modificacao = cabecalho.xpath('//div')[3].xpath('./text()').extract()[0].strip()
        tempo_medio = cabecalho.xpath('//div')[6].xpath('./text()').extract()[0].strip()

        itinerario = source.xpath('//div[@id="tabContent2"]').xpath('./div/div/ul')
        itinerarios = []
        for conj in [linha.xpath('./li/text()').extract() for linha in itinerario]:
            itinerarios.append([rua.split("-")[1].strip() for rua in conj])
        
        conteudo = source.xpath('//div[contains(@class, "tabContent")]').xpath('./div')
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
                lista_horas = horario.xpath('./div/ul/li/div/a/text()').extract()
                if lista_horas is not None:
                    conj_horarios.append([saida] + lista_horas)

        for conj in itinerarios:
            if not conj:
                conj.append("Itinerário indisponível.")

        for each_map in self.maps:
            if nome_onibus[0] in each_map[0]:
                rota = each_map
                break
            else:
                rota = ["Mapa não disponível."]

        item = FindMyBusItem(name=nome_onibus, price=preco, 
                            company="Biguaçu Transportes", 
                            schedule=conj_horarios, itinerary=itinerarios, 
                            time=tempo_medio, updated_at=modificacao,
                            route=rota)

        yield item
        yield self.make_requests_from_url(self.start_urls[0])
