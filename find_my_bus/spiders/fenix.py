# -*- coding: utf-8 -*-

"""fenix.py

Spider tailored to a specific local business website that scrapes a page
with all the bus lines and, then, those pages to get the data.

    * `scrapy.http.Request` represents an HTTP request, usually generated in
        the spider and executed by the downloader, thus generating a Response.
    * `scrapy.selector.Selector` is a wrapper over response to select certain
        parts of its content.
    * `scrapy.spiders.init.InitSpider` is a spider (class that defines how
        a certain site will be scraped) with initialization facilities.
"""

from find_my_bus.items import FindMyBusItem
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spiders.init import InitSpider


class FenixSpider(InitSpider):
    """Instantiates the Fenix spider."""
    name = "fenix"
    allowed_domains = ["consorciofenix.com.br"]
    start_urls = []

    def init_request(self):
        """Requests the base URL from the domain.

        Initializes communication with the site by feeding it information such
        as form data and request type.

        Returns:
            A FormRequest object with the necessary form submission data.
        """
        return Request(url='http://www.consorciofenix.com.br/horarios',
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
            self.start_urls.append("http://www.consorciofenix.com.br/" + path)

        return self.initialized()

    def parse(self, response):
        """Organizes the contents from each URL.

        Looks over the source code of its argument and parses information using
        Xpath manipulation.

        Args:
            response (Request): Any valid response generated from an URL.

        Yields:
            FindMyBusItem: Contains information about a bus line.
        """
        source = Selector(response)

        horario = source.xpath('//div[contains(@class, "horario")]')

        temp_nome = horario.xpath('./h1/a/text()').extract()[0].split(" - ")
        nome_onibus = [temp_nome[-1], " ".join(temp_nome[:-1]).upper()]

        conteudo = horario.xpath('./div')

        dados = [it for it in conteudo[0].xpath('.//text()').extract()
                 if it != u' ']

        minutos = dados[3].strip()[3:5]
        if minutos.isdigit():
            if int(minutos) > 60:
                tempo_medio = "{}h {}min".format(
                    int(minutos) // 60, int(minutos) % 60)
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

        for linha in conteudo[4:len(conteudo) - 1]:
            saida = linha.xpath('./div')[0].xpath(
                './h4/text()').extract()[0].split(" - ")
            horarios = []
            horarios.append(saida[0] + " - " + saida[1])
            for hor in linha.xpath('./div'):
                try:
                    horarios.append(hor.xpath('./a/text()').extract()[0])
                except IndexError:
                    pass
            conj_horarios.append(horarios)

        itin = horario.xpath('./ol/li/text()').extract()

        for conj in itin:
            if not conj:
                conj.append("Itinerário indisponível.")

        if source.xpath('//div[contains(@class, "mapac")]/img/@src').extract():
            map_url = "http://www.consorciofenix.com.br/r/w/mapas/1000x1000/"
            rota = map_url + nome_onibus[1].split(" ")[0] + ".jpg"
        else:
            rota = "Mapa não disponível."

        yield FindMyBusItem(
            name=nome_onibus, price=preco, company="Consórcio Fênix",
            schedule=conj_horarios, itinerary=itin, time=tempo_medio,
            updated_at=modificacao, route=rota
        )
