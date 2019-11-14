import subprocess
import sys
import traceback
from urllib.parse import urlparse

import scrapy
from scrapy_redis.spiders import RedisSpider
from threading import Thread
from time import sleep
from example.items import ExampleItem
import re
import os, os.path
import errno
import textract
# Need to manually pip install patool, patoolib need 7zip tool installed
from pyunpack import Archive
import shutil


class Util(object):
    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    '''
        For the given path, get the List of all files in the directory tree 
    '''
    def get_list_of_files(self, dir_path):
        # create a list of file and sub directories
        # names in the given directory
        list_of_file = os.listdir(dir_path)
        all_files = list()
        # Iterate over all the entries
        for entry in list_of_file:
            # Create full path
            full_path = os.path.join(dir_path, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(full_path):
                all_files = all_files + self.get_list_of_files(full_path)
            else:
                all_files.append(full_path)
        return all_files

    def get_file_extension(self, file_path):
        return os.path.splitext(file_path)[1]

    def getUrlExtension(self, url):
        return os.path.splitext(urlparse(url).path)[1]

    def unzipFileIfNeeded(self, file_path, zipped_file_extensions):
        for fe in zipped_file_extensions:
            if self.get_file_extension(file_path) == fe:
                try:
                    Archive(file_path).extractall(os.path.dirname(file_path))
                    # Succeeded
                    return 0
                except Exception as e:
                    print("type error: " + str(e))
                    print(traceback.format_exc())
                    # Can not unzip
                    return 2
        # Don't need unzip
        return 1

    # content is bytes
    def hasFilterKeywords(self, content, filter_keywords):
        flag = True
        for keywords in filter_keywords:
            flag = True
            for keyword in keywords:
                if bytes(keyword, 'utf-8') not in content:
                    flag = False
                    break
            if flag is True:
                return flag
        return flag

    # content is string
    def hasFilterKeywordsInString(self, content, filter_keywords):
        flag = True
        for keywords in filter_keywords:
            flag = True
            for keyword in keywords:
                print(keyword)
                if keyword not in content:
                    flag = False
                    break
            print(flag)
            if flag is True:
                return flag
        return flag


class SiafSpider(RedisSpider):
    """Spider that reads urls from redis queue (myspider:start_urls)."""
    name = 'siafspider_redis'
    redis_key = 'siafspider:start_urls'
    # Store all parserd url, unique
    redis_all_urls = 'siafspider:all_urls'
    # Filter all url in below domain, then store in start_urls
    redis_filter_domains = ['org', 'gov']
    # Found the keywords in html and no html text, should satisfy all keywords of any list of listoflists
    redis_filter_keywords = [['养老', '医疗', '住房', '工伤', '失业', '生育'],
                             ['缴费基数上下限']]
    # Store the html content in redis key
    redis_filter_html = 'siafspider:htmls'
    # Store the downloaded texts which contains keywords set
    debug_dir = 'c:/download/'
    # No html file extension list
    nohtml_file_extension = ['.doc', '.docx', '.xls', '.xlsx', '.pptx', '.pdf',
                             '.png', '.jpg', '.jpeg', '.gif', '.tif', '.tiff',
                             '.zip', '.rar', '.7z']
    # Folder need to be processed
    debug_nohtml_cache_dir = 'c:/download/nohtml_cache/'
    # File can not be processed size - 1M
    debug_nohtml_file_upper_size = 1024*1024
    # Folder can not be processed
    debug_nohtml_no_handle_dir = 'c:/download/nohtml_nohandle/'
    # Need to unzip if file extensions in the list
    debug_zipped_file_extensions = ['.zip', '.rar', '.7z']
    # When parsing html, which section need to be selected depends on domain extension
    redis_parser_rules = {'sipspf.org.cn': 'td[width="80%"]'}
    util = Util()
    no_html_processor = 0

    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        domain = kwargs.pop('domain', '')
        self.allowed_domains = filter(None, domain.split(','))
        super(SiafSpider, self).__init__(*args, **kwargs)

        # Init no html processor
        if self.no_html_processor == 0:
            self.no_html_processor = NoHtmlProcessingThread(self.debug_dir, self.debug_nohtml_cache_dir,
                                                            self.redis_filter_keywords,
                                                            self.debug_zipped_file_extensions,
                                                            self.debug_nohtml_no_handle_dir,
                                                            self.debug_nohtml_file_upper_size)
            self.no_html_processor.start()

    def parse(self, response):
        l = ExampleItem()
        # Judge whether it's a not html file
        if self.isNoHtmlFile(response) is True:
            # Treat it like not html
            self.saveItToFile(self.debug_nohtml_cache_dir, response)
        else:
            # Treat it like html
            # According to the rules to judge whether it has the keywords, then save the file in directory
            if self.htmlParseRulesSelector(response) is True:
                self.saveItToFile(self.debug_dir, response)
            l['name'] = response.css('title::text').get()
            self.get_urls_store_redis(response)

        l['url'] = response.url
        yield l

    def get_urls_store_redis(self, response):
        for url in response.css('a::attr(href)').getall():
            if url is not None:
                full_url = response.urljoin(url)
                # if defined domain in url
                domain_foreach = re.sub(r'(.*://)?([^/?]+).*', '\g<1>\g<2>', full_url)
                for domain_keyword in self.redis_filter_domains:
                    if domain_keyword in domain_foreach.lower():
                        # if url is new
                        r = self.server.sismember(self.redis_all_urls, full_url)
                        if r == 0:
                            self.server.rpush(self.redis_key, full_url)
                            self.server.sadd(self.redis_all_urls, full_url)

    def htmlParseRulesSelector(self, response):
        for rule in self.redis_parser_rules.keys():
            if rule in response.url:
                return self.util.hasFilterKeywordsInString(response.css(self.redis_parser_rules[rule]).get(),
                                                           self.redis_filter_keywords)
        return self.util.hasFilterKeywords(response.body, self.redis_filter_keywords)

    def saveItToFile(self, dir_path, response):
        self.util.mkdir_p(dir_path)
        file_name = dir_path + response.url.replace(":", ".").replace("/", "_")
        # print('file_name')
        # print (file_name)
        with open(file_name, 'wb') as out_file:
            out_file.write(response.body)

    def isNoHtmlFile(self, response):
        nohtml_flag = False
        for fe in self.nohtml_file_extension:
            if self.util.getUrlExtension(response.url) == fe:
                nohtml_flag = True
                break
        return nohtml_flag

    def __del__(self):
        if self.no_html_processor != 0:
            self.no_html_processor.stop()


class NoHtmlProcessingThread(Thread):
    run_flag = True
    util = Util()

    def __init__(self, debug_dir, debug_nohtml_cache_dir, filter_keywords, debug_zipped_file_extensions,
                 debug_nohtml_no_handle_dir, debug_nohtml_file_upper_size):
        Thread.__init__(self)
        self.debug_dir = debug_dir
        self.debug_nohtml_cache_dir = debug_nohtml_cache_dir
        self.filter_keywords = filter_keywords
        self.debug_zipped_file_extensions = debug_zipped_file_extensions
        self.debug_nohtml_no_handle_dir = debug_nohtml_no_handle_dir
        self.debug_nohtml_file_upper_size = debug_nohtml_file_upper_size

    def stop(self):
        print('NoHtmlProcessingThread stopped')
        self.run_flag = False

    def process_no_html(self, file_path):
        image_file_extension = ['.png', '.jpg', '.jpeg', '.gif', '.tif', '.tiff']
        for fe in image_file_extension:
            if self.util.get_file_extension(file_path) == fe:
                return textract.process(file_path, language='chi_sim')
        """
            Need to use subprocess to parse doc file using antiword (only can detect english for can not pass parameters
             to textract.process function )
        """
        if self.util.get_file_extension(file_path) == '.doc':
            return subprocess.check_output(['antiword', '-m', 'utf-8.txt', file_path])
        return textract.process(file_path)

    def run(self):
        print('NoHtmlProcessingThread start')
        while self.run_flag:
            self.util.mkdir_p(self.debug_nohtml_cache_dir)
            all_files = self.util.get_list_of_files(self.debug_nohtml_cache_dir)
            for file in all_files:
                # unzip file
                rr = self.util.unzipFileIfNeeded(file, self.debug_zipped_file_extensions)
                if rr == 0:
                    os.remove(file)
                elif rr == 1:
                    self.util.mkdir_p(self.debug_nohtml_no_handle_dir)
                    try:
                        # if file size less than 1M
                        if os.stat(file).st_size < self.debug_nohtml_file_upper_size:
                            text = self.process_no_html(file)
                            if self.util.hasFilterKeywords(text, self.filter_keywords) is True:
                                shutil.move(file, self.debug_dir)
                            else:
                                os.remove(file)
                        else:
                            shutil.move(file, self.debug_nohtml_no_handle_dir)
                    except Exception as e:
                        print("type error: " + str(e))
                        print(traceback.format_exc())
                        shutil.move(file, self.debug_nohtml_no_handle_dir)
                else:
                    shutil.move(file, self.debug_nohtml_no_handle_dir)
            sleep(0.1)
