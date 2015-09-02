# coding:utf-8

import re
import socket
import Queue
import threading
import sys
import datetime
import requests
import random
import time
from urlfilter import url_is_similar, url_is_repeat, url_contain_custom_focus
socket.setdefaulttimeout(3)


html = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
gzip = 'gzip, deflate, sdch'
chinese = 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4'
user_agent = ['Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
              'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16',
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
              'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
              'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
              ]

# 已经爬过的链接
crawledurl = []
# 不需要爬的链接
filterurl = ["javascript:void(0);", "#", "javascript:;", "javascript:window.scrollTo(0,0);"]
crawl_queue = Queue.Queue()

# 正则提取href
url_pat = re.compile(r'(?<=href=\").*?(?=\")', re.M)

def get_all_links(page, baseurl, focuskey = ()): 
    """获取整个页面的链接 向队列中加入新url"""
    for url in re.finditer(url_pat, page):
        url = url.group()
        if url in filterurl or url_is_repeat(url):#or url_is_similar(url):
            continue
        if not url_contain_custom_focus(url, focuskey): # 是否含特定域名
            continue
        if url.startswith("http"):
            crawl_queue.put(url)
        else:
            crawl_queue.put(baseurl[:-1]+url)

def write_log(error, url):
    """把错误信息写入日志"""
    ferror = open("log.txt", "a")
    ferror.write(error+" ")
    ferror.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+" ")
    ferror.write(url+'\n')
    ferror.close()

def random_agent(user_agent):
    """随机选择浏览器"""
    return random.choice(user_agent)

def check_link(url, focuskey):
    """分析链接是否异常 有异常记录到log 没异常获取页面链接"""
    crawledurl.append(url)
    try:
        response = requests.get(url, headers = {'Accept':html,'Accept-Encoding':gzip,
                'Accept-Language':chinese,'Cache-Control':'no-cache','Connection':'keep-alive',
                'User-Agent':random_agent(user_agent)},timeout = 3)
    except requests.exceptions.ConnectionError:
        write_log('ConnectionError', url)
    except requests.exceptions.HTTPError:
        write_log('HTTPError', url)
    except (requests.exceptions.Timeout, socket.timeout):
        write_log("Timeout", url)
    except requests.exceptions.TooManyRedirects:
        write_log('TooManyRedirects', url)
    except requests.exceptions.InvalidURL:
        write_log('InvalidURL', url)
    except:
        write_log('UnknownError', url)
    else:
        page = response.text
        get_all_links(page, url, focuskey) # url is base_url

class CrawlUrl(threading.Thread):
    def __init__(self, crawl_queue, focuskey):
        threading.Thread.__init__(self)
        self.crawl_queue = crawl_queue
        self.focuskey = focuskey

    def run(self):
        while True:
            url = self.crawl_queue.get()
            if url not in crawledurl:
                check_link(url, self.focuskey)
            self.crawl_queue.task_done()
            print "left {}, has {}".format(crawl_queue.qsize(), len(crawledurl))

def main():
    for i in range(10):
        crawlthread = CrawlUrl(crawl_queue, focuskey = [m.sohu.com'])
        crawlthread.setDaemon(True)
        crawlthread.start()

        url = "http://m.sohu.com/"
        crawl_queue.put(url)

    crawl_queue.join()

if __name__ == "__main__":
    main()

