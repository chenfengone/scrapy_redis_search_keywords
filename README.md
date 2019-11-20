# scrapy_redis_search_keywords
Folk from scrapy redis and create a spider to search keywords from all websites

# Test Env
1. This example only tested at Windows 7 and 10, 64 bits  
2. It need [textract](https://github.com/deanmalmgren/textract) installed at OS, you can refer this [link](https://blog.csdn.net/chenfengone/article/details/103037914) to know how to install it.

# How to run
1. use below redis command to push one start url, below is one example:
  lpush 'siafspider:start_urls' http://rsj.nanjing.gov.cn/
2. Run command line tool and call start.bat to run the APP
