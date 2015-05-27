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
        'http://www.biguacutransportes.com.br/ajax/lineBus/preview/?line=%s\
        &company=1&detail%%5B%%5D=1&detail%%5B%%5D=2&detail%%5B%%5D=3'
    )
    urls = []

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
            self.urls.append(self.start_urls[1] % path)

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
            return Request(self.urls.pop(), callback=self.parse)

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

        item = FindMyBusItem(name=nome_onibus, price=preco, 
                            company="Biguaçu Transportes", 
                            schedule=conj_horarios, itinerary=itinerarios, 
                            time=tempo_medio, updated_at=modificacao)

        yield item
        yield self.make_requests_from_url(self.start_urls[0])
