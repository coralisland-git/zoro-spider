import scrapy
import json
import os
from scrapy.spiders import Spider
from scrapy.http import FormRequest
from scrapy.http import Request
from chainxy.items import ChainItem
from lxml import html
import usaddress
import pdb
import tokenize
import token
from StringIO import StringIO

class ZoroSpider(scrapy.Spider):
	name = 'zoro'
	domain = 'https://www.zoro.com'

	def start_requests(self):
		init_url = 'https://www.zoro.com/'
		yield scrapy.Request(url=init_url, callback=self.parse_kind) 
	
	def parse_kind(self, response):
		kind_list = response.xpath('//div[@class="category-level-0-box-group"]//a/@href').extract()
		for kind in kind_list[:-1]:
			kind = self.domain + kind
			yield scrapy.Request(url=kind, callback=self.parse_block)

	def parse_block(self, response):
		block_list  = response.xpath('//div[contains(@class, "col-extra-padding")]//h4[@class="header"]//a/@href').extract()
		for block in block_list:
			block = self.domain + block
			yield scrapy.Request(url=block , callback=self.parse_category)

	def parse_category(self, response):
		data = response.body.split('id="categories-facet" data-attributes="')[1].strip().split('"></span><span id="brands-facet"')[0].strip()
		data = data.replace('&quot;','').replace('amp;','')
		category_list = data.split('query:')
		for category in category_list[2:]:
			category = 'https://www.zoro.com/search?' + self.validate(category).split(' ')[0].strip()[:-1]
			yield scrapy.Request(url=category, callback=self.parse_product)
		
	def parse_product(self, response):
		try:
			category = self.validate(response.url.split('categoryl2')[1].split('&')[0]).replace('=','').replace('+', ' ')
			data = response.body.split('items: djangoList(')[1].strip().split('imageProductUrl:')[0].strip()[:-2]
			product_list = json.loads(data)
			for product in product_list:
				product = self.domain + product['url']
				yield scrapy.Request(url=product, callback=self.parse_page, meta={'category':category})

			pagenation = response.xpath('//a[@class="page-curl-btn next"]/@href').extract_first()
			if pagenation:
				pagenation = self.domain + pagenation
				yield scrapy.Request(url=pagenation, callback=self.parse_product)
		except:
			pass

	def parse_page(self, response):
		try:
			item = ChainItem()
			detail = response.xpath('//div[contains(@class, "tech-details")]//text()').extract()
			item['zoro'] = self.validate(response.xpath('//div[@id="brand-name"]//span[@itemprop="sku"]/text()').extract_first())
			item['mfr'] = self.validate(response.xpath('//div[@id="brand-name"]//span[@itemprop="mpn"]/text()').extract_first())
			item['brand'] = self.validate(response.xpath('//div[@id="brand-name"]//span[@itemprop="brand"]/text()').extract_first())
			item['name'] = self.validate(response.xpath('//h1[contains(@class, "productName")]//span[@itemprop="name"]/text()').extract_first())
			item['selling_price'] = self.validate(response.xpath('//span[@itemprop="price"]/text()').extract_first())
			item['image_link'] = self.validate(response.xpath('//div[@id="main-image"]//img[@itemprop="contentUrl"]/@src').extract_first())
			item['description'] = self.validate(response.xpath('//div[@class="panel-body"]//span[@itemprop="description"]/text()').extract_first())
			t_temp = ''
			tech_list = self.eliminate_space(response.xpath('//div[contains(@class, "tech-details")]//table//tr//text()').extract())
			cnt = 1
			for tech in tech_list[4:]:
				t_temp += self.validate(tech)
				if cnt % 2 == 0:
					t_temp += ', '
				cnt += 1
			item['tech_specs'] = t_temp.strip()[:-1]
			item['website_category'] = response.meta['category']
			item['status'] = self.validate(response.xpath('//div[@id="avl-in-stock-button"]//p//text()').extract_first())
			yield item
		except:
			pass

	def validate(self, item):
		try:
			return item.strip().replace('  ', '').replace('\r', '').replace('\n','')
		except:
			return ''

	def eliminate_space(self, items):
		tmp = []
		for item in items:
			if self.validate(item) != '':
				tmp.append(self.validate(item))
		return tmp

	def fixLazyJson (self, in_text):
		tokengen = tokenize.generate_tokens(StringIO(in_text).readline)
		result = []
		for tokid, tokval, _, _, _ in tokengen:
			if (tokid == token.NAME):
				if tokval not in ['true', 'false', 'null', '-Infinity', 'Infinity', 'NaN']:
					tokid = token.STRING
					tokval = u'"%s"' % tokval
			elif (tokid == token.STRING):
				if tokval.startswith ("'"):
					tokval = u'"%s"' % tokval[1:-1].replace ('"', '\\"')
			elif (tokid == token.OP) and ((tokval == '}') or (tokval == ']')):
				if (len(result) > 0) and (result[-1][1] == ','):
					result.pop()			
			elif (tokid == token.STRING):
				if tokval.startswith ("'"):
					tokval = u'"%s"' % tokval[1:-1].replace ('"', '\\"')
			result.append((tokid, tokval))

		return tokenize.untokenize(result)
