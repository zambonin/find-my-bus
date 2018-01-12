# -*- coding: utf-8 -*-

"""pipelines.py

Models for scraped items with capabilities similar to a dictionary.
"""

from json import dump

class FilePipeline(object):
    """
    Manages all items that shall be output to a file when scraping ends.
    """
    def __init__(self):
        self.file = None
        self.temp = {}

    def open_spider(self, spider):
        """
        Method called when the spider is opened. The exporter is created
        with some additional flags to ensure readability of the output.

        Args:
            spider (Spider): the spider which was opened.
        """
        self.file = open(spider.name + ".json", 'w', encoding='utf-8')

    def close_spider(self, _spider):
        """
        Method called when the spider is closed.

        Args:
            spider (Spider): the spider which was closed.
        """
        dump(self.temp, self.file, indent=2, ensure_ascii=False)
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
        key, value = next(iter(item.items()))
        self.temp.update({key : dict(value)})
        return item
