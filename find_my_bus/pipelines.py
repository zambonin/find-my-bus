# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
from scrapy.contrib.exporter import BaseItemExporter

class FindMyBusPipeline(object):
    def process_item(self, item, spider):
        return item

class FilePipeline(BaseItemExporter):
	def open_spider(self, spider):
		self.list = []

	def close_spider(self, spider):
		with open('items.json', 'w') as fp:
			fp.write(json.dumps(self.list))

	def process_item(self, item, spider):
		tmp = dict(self._get_serialized_fields(item))
		self.list.append(tmp)
		return item
