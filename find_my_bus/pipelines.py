# -*- coding: utf-8 -*-

"""pipelines.py

Models for scraped items with capabilities similar to a dictionary.

    * `scrapy.exporters.JsonItemExporter` handles exporting of data
        to a JSON object, possibly to be consumed by other systems.
"""

from scrapy.exporters import JsonItemExporter


class FilePipeline(JsonItemExporter):
    """
    Manages all items that shall be output to a file when scraping ends.
    """
    def __init__(self):
        self.file = None
        self.exporter = None
        super().__init__(self.file)

    def open_spider(self, spider):
        """
        Method called when the spider is opened. The exporter is created
        with some additional flags to ensure readability of the output.

        Args:
            spider (Spider): the spider which was opened.
        """
        self.file = open(spider.name + ".json", 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8',
                                         ensure_ascii=False, indent=2)
        self.exporter.start_exporting()

    def close_spider(self, _spider):
        """
        Method called when the spider is closed.

        Args:
            spider (Spider): the spider which was closed.
        """
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, _spider):
        """
        Method called for every item pipeline component.

        Args:
            item (Item): the item processed by the exporter.
            _spider (Spider): the active spider.

        Returns:
            An Item object to be handled further in the pipeline.
        """
        self.exporter.export_item(item)
        return item
