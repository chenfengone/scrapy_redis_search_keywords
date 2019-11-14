# Scrapy settings for example project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
SPIDER_MODULES = ['example.spiders']
NEWSPIDER_MODULE = 'example.spiders'

# use for anti crawl for some website-http://hrss.wuxi.gov.cn/
#USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
# use for random choice use agent another strategy to anti-crawl
USER_AGENT_LIST = [
    'MSIE (MSIE 6.0; X11; Linux; i686) Opera 7.23',
    'Opera/9.20 (Macintosh; Intel Mac OS X; U; en)',
    'Opera/9.0 (Macintosh; PPC Mac OS X; U; en)',
    'iTunes/9.0.3 (Macintosh; U; Intel Mac OS X 10_6_2; en-ca)',
    'Mozilla/4.76 [en_jp] (X11; U; SunOS 5.8 sun4u)',
    'iTunes/4.2 (Macintosh; U; PPC Mac OS X 10.2)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0) Gecko/20100101 Firefox/5.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:9.0) Gecko/20100101 Firefox/9.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20120813 Firefox/16.0',
    'Mozilla/4.77 [en] (X11; I; IRIX;64 6.5 IP30)',
    'Mozilla/4.8 [en] (X11; U; SunOS; 5.7 sun4u)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
    ]

# use for anti crawl (outside of china) for some website-http://hrss.wuxi.gov.cn/
# if you are in china, you can also use this for some website will block the access if you use crawler
# you can get the http proxy from below web site
# http://proxy-list.org/english/search.php?search=CN&country=CN&type=any&port=any&ssl=any
PROXIES = [
    '218.60.8.99:3129',
    '119.23.79.199:3128',
    '101.4.136.34:80',
    '39.106.223.134:80',
    '47.107.80.181:8000',
    '47.98.241.70:1080'
]

DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
SCHEDULER_PERSIST = True
SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderPriorityQueue"
#SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderQueue"
#SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderStack"

ITEM_PIPELINES = {
    'example.pipelines.ExamplePipeline': 300,
    'scrapy_redis.pipelines.RedisPipeline': 400,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'example.middlewares.RandomProxy': 542,
    'example.middlewares.RandomUserAgentMiddleware': 543,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

LOG_LEVEL = 'DEBUG'

# redis服务器ip以及端口
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Introduce an artifical delay to make use of parallelism. to speed up the
# crawl.
DOWNLOAD_DELAY = 1
