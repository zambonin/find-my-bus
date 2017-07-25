# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exporters import JsonItemExporter


class FilePipeline(JsonItemExporter):
    def __init__(self):
        self.file = None
        self.exporter = None
        super().__init__(self.file)

    def open_spider(self, spider):
        self.file = open(spider.name + ".json", 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8',
                                         ensure_ascii=False, indent=2)
        self.exporter.start_exporting()

    def close_spider(self, _spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, _spider):
        self.exporter.export_item(item)
        return item
