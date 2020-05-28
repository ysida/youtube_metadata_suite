#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import os
import time

from helper_functions import *
from models import *
import re
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


def get_channel_video_items(channel_id):
    """ get channel videos """
    print(channel_id)
    print(type(channel_id))
    browser = webdriver.Firefox(executable_path='./geckodriver')
    scrollable_url = "https://www.youtube.com/channel/{}/videos".format(channel_id)
    browser.get(scrollable_url)

    scroll_sleep_time_seconds = float(os.getenv("SCROLL_SLEEP_TIME_SECONDS"))
    time.sleep(scroll_sleep_time_seconds)

    body_element = browser.find_element_by_tag_name("body")

    result0 = browser.execute_script('return window["ytInitialData"]')
    i = 0
    while True:
        print("i is {}".format(i))

        for _ in range(3):
            body_element.send_keys(Keys.PAGE_DOWN)

        time.sleep(scroll_sleep_time_seconds)

        result = browser.execute_script('return window["ytInitialData"]')

        # TODO: better check
        if result == result0:
            print("breaking..")
            break

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
    return video_items


def fetch_save_video_items_return_video_id(video_items,channel_id):
    print("there are {} videos.".format(len(video_items)))
    save_obj(video_items, "video_items")

    conn_string = os.getenv("SQLITE_PATH")
    engine = create_engine(conn_string)
    Base.metadata.create_all(engine)  # here we create all tables
    session0 = sessionmaker(bind=engine)
    session = session0()

    videos_ids = []
    for n in video_items:
        m = n["gridVideoRenderer"]
        idd = m["videoId"]
        videos_ids.append(idd)
        title = m["title"]["simpleText"]
        views = m["viewCountText"]["simpleText"]
        duration = m["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["text"]["simpleText"]

        duration = get_sec(duration)

        m = re.search("(?P<views>[\d,]+)", views)
        views = m.group('views')
        views = int(views.replace(",", ""))

        video = Video(id=idd, title=title, duration=duration, views=views, channel=channel_id)
        session.merge(video)
        session.commit()

    return videos_ids
