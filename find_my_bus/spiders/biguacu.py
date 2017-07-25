# -*- coding: utf-8 -*-

"""biguacu.py

Spider tailored to a specific local business website, that needs to ignore
the AJAX-ridden website and use specific requests to get all the bus lines.

    * `scrapy.http.FormRequest` extends the base Request with functionality
        for dealing with HTML forms.
    * `scrapy.selector.Selector` is a wrapper over response to select certain
        parts of its content.
    * `scrapy.spiders.init.InitSpider` is a spider (class that defines how
        a certain site will be scraped) with initialization facilities.
"""

from re import findall
from urllib.request import urlopen

from find_my_bus.items import FindMyBusItem
from scrapy.http import FormRequest
from scrapy.selector import Selector
from scrapy.spiders.init import InitSpider


class BiguacuSpider(InitSpider):
    """Instantiates the Biguacu spider."""
    name = "biguacu"
    allowed_domains = ["biguacutransportes.com.br"]
    start_urls = []

    def init_request(self):
        """Requests the base URL from the domain.

        Initializes communication with the site by feeding it information such
        as form data and request type.

        Returns:
            A FormRequest object with the necessary form submission data.
        """
        # 1 for the main lines, 3 for the executive ones
        url = 'http://www.biguacutransportes.com.br/ajax/lineBus/searchGetLine'
        return [FormRequest(url=url, formdata={'company': str(i)},
                            callback=self.organize) for i in [1, 3]]

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
        url = 'http://www.biguacutransportes.com.br/ajax/lineBus/preview/'
        links = [it.xpath('./td')[0].xpath('./text()')
                 for it in source.xpath('//tr')]

        last = bool(len(self.start_urls))
        for link in links:
            path = link.extract()[0]
            self.start_urls.append(
                url + "?line={}{}".format(path, '&detail[]=1,2,3'))

        return self.initialized() if last else None

    def parse(self, response):
        """Organizes the contents from each URL.

        Looks over the source code of its argument and parses information using
        Xpath manipulation.

        Args:
            response (Request): Any valid response generated from an URL.

        Yields:
            FindMyBusItem: Contains information about a bus line.
        """
        def parse_map_info(line):
            """Organizes the contents for each URL.

            Organizes the contents from specific map URLs, searching
            for URLs that contain a certain combination of characters
            through regular expressions.

            Detailed breakdown of the expression used:
              http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+

                http          match the string literally
                [s]?          match `s` up to 1 time
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
                A list of KML maps containing the routes for each bus line,
                or an error message.
            """
            url = 'http://www.biguacutransportes.com.br/ajax/lineBus/map'
            pattern = 'http[s]?://(?:[a-zA-Z0-9]|[/_@.:~])+'
            unavailable = "Mapa não disponível."

            with urlopen(url + "?idLine={}&type=2".format(line)) as resp:
                matches = findall(pattern, str(resp.read()))
                return [m for m in matches if "kml" in m] or unavailable

        source = Selector(response)
        cabecalho = source.xpath('//div/div')

        nome_onibus = cabecalho.xpath('//div')[0].xpath(
            '//span/text()')[3].extract().strip().split(" ", 1)

        preco = {
            "card": 0,
            "money": 0,
        }
        if len(cabecalho.xpath('//div')[0].xpath('//span/text()')) > 12:
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

        yield FindMyBusItem(
            name=nome_onibus, price=preco, company="Biguaçu Transportes",
            schedule=conj_horarios, itinerary=itinerarios, time=tempo_medio,
            updated_at=modificacao, route=parse_map_info(nome_onibus[0])
        )
