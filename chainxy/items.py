# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class ChainItem(Item):
    zoro = Field()
    mfr = Field()
    brand = Field()
    name = Field()
    selling_price = Field()
    description = Field()
    tech_specs = Field()
    image_link = Field()
    website_category = Field()
    status = Field()
