#!/usr/bin/env python3
import argparse
import sys
import re
import time
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import pickle
import json

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from models import *

from dotenv import load_dotenv
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# def save_obj(obj, name ):
#     with open('obj/'+ name + '.pkl', 'wb') as f:
#         pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def save_obj(obj, name):
    with open('obj/' + name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    with open('obj/data.json', 'w') as fp:
        print(len(obj))
        json.dump(obj, fp)


def get_sec(time_str):
    """Get Seconds from time."""
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    except:
        m, s = time_str.split(':')
        return int(m) * 60 + int(s)



# def load_obj(name ):
#     with open('obj/' + name + '.pkl', 'rb') as f:
#         return pickle.load(f)

"""
get channel videos
"""


def get_channel_videos(channel_id):
    print(channel_id)
    print(type(channel_id))
    SLEEP_TIME = 1
    NUM_PAGE_DOWN = 10
    PAGE_DOWN_INTERVAL = 0.9
    browser = webdriver.Firefox(executable_path='./geckodriver')
    scrollable_url = "https://www.youtube.com/channel/{}/videos".format(channel_id)
    browser.get(scrollable_url)
    time.sleep(SLEEP_TIME)
    body_element = browser.find_element_by_tag_name("body")

    result0 = browser.execute_script('return window["ytInitialData"]')
    i = 0
    while True:
        print("i is {}".format(i))
        body_element.send_keys(Keys.PAGE_DOWN)
        body_element.send_keys(Keys.PAGE_DOWN)
        body_element.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAGE_DOWN_INTERVAL)
        result = browser.execute_script('return window["ytInitialData"]')
        if result == result0:
            print("breaking..")
            break;
        else:
            result0 = result
            i = i + 1

    result = browser.execute_script('return window["ytInitialData"]')

    a = result["contents"]
    a = a["twoColumnBrowseResultsRenderer"]
    a = a["tabs"]
    a = a[1]
    a = a["tabRenderer"]
    a = a["content"]
    a = a["sectionListRenderer"]
    a = a["contents"]
    a = a[0]
    a = a["itemSectionRenderer"]
    a = a["contents"]
    a = a[0]
    a = a["gridRenderer"]
    video_items = a["items"]

    print("there are {} videos.".format(len(video_items)))

    # video_items = load_obj("videos")
    # print(video_items)
    # print(video_items.keys())
    # print(type(video_items))

    conn_string = os.getenv("SQLITE_PATH")
    engine = create_engine(conn_string)
    Base.metadata.create_all(engine)  # here we create all tables
    Session = sessionmaker(bind=engine)
    session = Session()

    videos = {}

    for n in video_items:
        # print(n.keys())
        # n=n[0]
        # print(n)
        m = n["gridVideoRenderer"]
        idd = m["videoId"]
        title = m["title"]["simpleText"]
        views = m["viewCountText"]["simpleText"]
        duration = m["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["text"]["simpleText"]

        # views = Integer("".join(views.split(",")))
        duration = get_sec(duration)

        # '9,385 views'
        m = re.search("(?P<views>[\d,]+)", views)
        views = m.group('views')
        views = int(views.replace(",", ""))

        video = Video(id=idd, title=title, duration=duration, views=views, channel=channel_id)
        session.merge(video)
        session.commit()

        # videos[id]={}
        # videos[id]["id"] = id
        # videos[id]["title"] = title
        # videos[id]["viewsCount"] = viewsCount
        # videos[id]["duration"] = duration
        # pass

    print(len(videos))
    save_obj(videos, "videos")

    # l=k[105]

    # [105]["gridVideoRenderer"]["title"]["simpleText"]

    # m=result["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]["itemSectionRenderer"]["contents"][0]["gridRenderer"]["video_items"]
    # print(len(m))
    # print(str(m))
    # print(len(m))

    # with open("file","w") as m:
    #     m.write(str(result))

    # d = json.loads(s)
    # print(type(d))
    # print(d)

    # with open("file","w") as m:
    #     m.write("hi")

    # post_elements = browser.find_elements_by_css_selector("ytd-grid-video-renderer.style-scope > div:nth-child(1) > ytd-thumbnail:nth-child(1) > a")
    # channel_videos = [a.get_attribute("href") for a in post_elements]
    # if not channel_videos:
    #     channel_videos = []
    # return channel_videos

# https://www.youtube.com/channel/UCa6eh7gCkpPo5XXUDfygQQA
# https://www.youtube.com/channel/UCOQ-WpDxp4P1pOJ4Kbc1i2w
# https://www.youtube.com/channel/UC1fLEeYICmo3O9cUsqIi7HA
# https://www.youtube.com/channel/UCa6eh7gCkpPo5XXUDfygQQA
# https://www.youtube.com/watch?v=qECG2_8xw_s
# https://www.youtube.com/watch?v=QW8AkqJ1CAA
# https://www.youtube.com/watch?v=Lqehvpe_djso
# https://www.youtube.com/watch?v=1YuN3POoNnQ

parser = argparse.ArgumentParser()

parser.add_argument("-c", "--channel", help="channel id", type=str)
parser.add_argument("-i", "--interactive", help="interactive mode", type=bool, default=False)
args = parser.parse_args()

# TODO add batch mode of interesting channels, use regex to grab unique channels

# parser.add_argument("-iv", "--video", help="video id", type=str)
# parser.add_argument("-ia", "--action", help="action", type=str)

# def message(m):
#     print()

# check arguments

# check valid channel
if args.channel is not None:
    channel = args.channel
    m = (re.search("(youtube\.com/channel/)?(?P<channel_id>\w{24})", channel))
    try:
        channel_id = (m.group("channel_id"))
        print("hi")
        print(channel_id)
    except:
        print("\nNo valid channel id was provided... Exiting.\n")
        sys.exit()

get_channel_videos(channel_id)

# # arguments normalization
# if args.video is None: 
#     args.video = ""


# if len(args.channel)==24:
#     print("24 true")
# else:
#     print("not 24")

# https://www.youtube.com/channel/UCa6eh7gCkpPo5XXUDfygQQA
# https://www.youtube.com/channel/UCOQ-WpDxp4P1pOJ4Kbc1i2w
# https://www.youtube.com/channel/UC1fLEeYICmo3O9cUsqIi7HA
