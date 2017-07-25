# -*- coding: utf-8 -*-

"""settings.py

Scrapy settings for this project.
"""

BOT_NAME = 'find_my_bus'

SPIDER_MODULES = ['find_my_bus.spiders']
NEWSPIDER_MODULE = 'find_my_bus.spiders'

ITEM_PIPELINES = {
    'find_my_bus.pipelines.FilePipeline': 999,
}
