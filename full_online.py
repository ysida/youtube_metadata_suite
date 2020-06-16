#!/usr/bin/env python3

import re
import requests
import bs4

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={youtube_id}'
video_id = "Wa1gX6xtPrc"

session = requests.Session()
session.headers['User-Agent'] = USER_AGENT
response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=video_id))
HTML = response.text

JSON = re.compile('window\["ytInitialData"\].*?({.*?});', re.DOTALL)
m = [x.groups() for x in (JSON.finditer(HTML))]
ytInitial = m[0][0]

DESCRIPTION = re.compile('"description":({.*?})', re.DOTALL)
n = [x.groups() for x in (DESCRIPTION.finditer(ytInitial))][0][0]

import logging
logging.basicConfig(filename='hi.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.DEBUG)

logging.info(n)
