from example.settings import USER_AGENT_LIST
from example.settings import PROXIES
import random

class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua = random.choice(USER_AGENT_LIST)
        if ua:
            request.headers.setdefault('User-Agent', ua)
            #print(request.headers)

class RandomProxy(object):
    def process_request(self, request, spider):
        proxy = random.choice(PROXIES)
        request.meta['proxy'] = 'http://%s' % proxy
        #print(request.meta)
