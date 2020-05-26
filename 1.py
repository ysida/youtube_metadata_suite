#!/usr/bin/env python3
import argparse
import sys
import re
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import pickle
import json

# def save_obj(obj, name ):
#     with open('obj/'+ name + '.pkl', 'wb') as f:
#         pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    with open('obj/data.json', 'w') as fp:
        print(len(obj))
        json.dump(obj, fp)

# def load_obj(name ):
#     with open('obj/' + name + '.pkl', 'rb') as f:
#         return pickle.load(f)

"""
get channel videos
"""
def get_channel_videos(channel_id):
    print(channel_id)
    print(type(channel_id))
    SLEEP_TIME=1
    NUM_PAGE_DOWN=10
    PAGE_DOWN_INTERVAL=0.9
    browser = webdriver.Firefox(executable_path='./geckodriver')
    scrollable_url = "https://www.youtube.com/channel/{}/videos".format(channel_id)
    browser.get(scrollable_url)
    time.sleep(SLEEP_TIME)
    body_element = browser.find_element_by_tag_name("body")
    no_of_pagedowns = NUM_PAGE_DOWN
    while no_of_pagedowns:
        body_element.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAGE_DOWN_INTERVAL)
        no_of_pagedowns-=1

    
    result = browser.execute_script('return window["ytInitialData"]')

    a=result["contents"]
    b=a["twoColumnBrowseResultsRenderer"]
    c=b["tabs"]
    d=c[1]
    e=d["tabRenderer"]
    f=e["content"]
    g=f["sectionListRenderer"]
    h=g["contents"]
    h=h[0]
    i=h["itemSectionRenderer"]
    j=i["contents"]
    j=j[0]
    j=j["gridRenderer"]
    items=j["items"]
    print("there are {} videos.".format(len(items)))

    videos = {}

    for n in items:
        # print(m.keys())
        m=n["gridVideoRenderer"]
        id = m["videoId"]
        title = m["title"]["simpleText"]
        viewsCount = m["viewCountText"]["simpleText"]
        duration=m["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["text"]["simpleText"]

        videos[id]={}
        videos[id]["id"] = id
        videos[id]["title"] = title
        videos[id]["viewsCount"] = viewsCount
        videos[id]["duration"] = duration
        # pass
    
    print(len(videos))
    save_obj(videos,"videos")


    # l=k[105]

    # [105]["gridVideoRenderer"]["title"]["simpleText"]
    

    # m=result["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]["itemSectionRenderer"]["contents"][0]["gridRenderer"]["items"]
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
# parser.add_argument("-iv", "--video", help="video id", type=str)
# parser.add_argument("-ia", "--action", help="action", type=str)

# def message(m):
#     print()



# check arguments


# check valid channel
if args.channel is not None: 
    channel = args.channel
    m=(re.search("(youtube\.com/channel/)?(?P<channel_id>\w{24})", channel))
    try:
        channel_id=(m.group("channel_id"))
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

