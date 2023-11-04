import requests
from selenium import webdriver
import numpy
import pandas as pd
from bs4 import BeautifulSoup as bs
import os
import json
from datetime import datetime
from tqdm import tqdm
import time
import math

def toTime(n):
    n = int(n)
    min = math.floor(n / 60)
    sec = n - min * 60
    if min < 10:
        return '0' + str(min) + ":" + str(sec)
    else:
        return str(min) + ":" + str(sec)

def catch_data(uid, cookie, agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.61"):
  num_url = "https://api.bilibili.com/x/space/navnum?mid=" + uid
  res = requests.get(num_url, headers={"User-Agent": agent}, timeout = 5)
  data = json.loads(res.text)
  # print(data)
  nums = data['data']['video']
  retry_list = []
  pn = 0
  videos_data = []
  with tqdm(total = nums) as pbar:
      while pn * 30 < nums:
          pn += 1
          videos_url = "https://api.bilibili.com/x/space/wbi/arc/search?mid=" + uid + "&ps=30&tid=0&pn=" + str(pn) + "&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=9fce0c55bb4b3575eb0c816447308127&wts=1698247513"
          res = requests.get(videos_url, headers={"User-Agent": agent}, timeout = 5)
          data = json.loads(res.text)
      #     print(data)
          for v in data['data']['list']['vlist']:
              detail_url = "https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=" + str(v['aid']) + "&need_view=1&web_location=1315873&w_rid=569551646da0cb7bc2ba17dcb16fd691&wts=1698247513"
              res2 = requests.get(detail_url, headers={"User-Agent": agent, "Cookie": cookie}, timeout = 5)
              detail = json.loads(res2.text)
  #             print(detail)
              try:
                  detail = detail['data']['View']['stat']
              except KeyError:
                  pbar.update(1)
                  print("获取失败，将视频加入到重试列表中...")
                  retry_list.append(str(v['aid']))
                  time.sleep(120)
                  continue
              
              video_data = {
                  'AID': v['aid'],
                  '封面': v['pic'],
                  '标题': v['title'],
                  '时长': v['length'],
                  '发布时间': datetime.fromtimestamp(v['created']),
                  '播放': detail['view'],
                  '弹幕': detail['danmaku'],
                  '点赞': detail['like'],
                  '评论': detail['reply'],
                  '收藏': detail['favorite'],
                  '分享转发': detail['share'],
                  '投币': detail['coin'],
              }
              videos_data.append(video_data)
              pbar.update(1)
              time.sleep(1)
          time.sleep(1)
  with tqdm(total = len(retry_list)) as pbar:
      while not len(retry_list) == 0:
          aid = retry_list.pop(0)
          detail_url = "https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=" + aid + "&need_view=1&web_location=1315873&w_rid=569551646da0cb7bc2ba17dcb16fd691&wts=1698247513"
          res2 = requests.get(detail_url, headers={"User-Agent": agent, "Cookie": cookie}, timeout = 5)
          detail = json.loads(res2.text)
          try:
              detail = detail['data']['View']
          except KeyError:
              print("获取失败，将视频加入到重试列表中...")
              retry_list.append(aid)
              time.sleep(120)
              continue
              
          video_data = {
              'AID': aid,
              '封面': detail['pic'],
              '标题': detail['title'],
              '时长': toTime(int(detail['duration'])),
              '发布时间': datetime.fromtimestamp(detail['ctime']),
              '播放': detail['stat']['view'],
              '弹幕': detail['stat']['danmaku'],
              '点赞': detail['stat']['like'],
              '评论': detail['stat']['reply'],
              '收藏': detail['stat']['favorite'],
              '分享转发': detail['stat']['share'],
              '投币': detail['stat']['coin'],
          }
          videos_data.append(video_data)
          pbar.update(1)
          time.sleep(1)
  return video_data

if __name__ == "__main__":
  cookie = input("请输入Cookie: ")
  uid = input("请输入要抓取的UP主uid: ")
  video_data = catch_data(uid, cookie)
  df = pd.DataFrame(videos_data)
  df.to_excel("./data.xlsx")
  
