# -*- coding: utf-8 -*-

# Scrapy settings for find_my_bus project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'find_my_bus'

SPIDER_MODULES = ['find_my_bus.spiders']
NEWSPIDER_MODULE = 'find_my_bus.spiders'

ITEM_PIPELINES = {
	'find_my_bus.pipelines.FilePipeline': 999,
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'find_my_bus (+http://www.yourdomain.com)'
