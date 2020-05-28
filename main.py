#!/usr/bin/env python

from __future__ import print_function

from gevent import monkey
monkey.patch_all()


import io

import lxml.html
import requests
from lxml.cssselect import CSSSelector
import argparse
import sys
from video_functions import *
from pathlib import Path


from gevent.pool import Pool
from gevent import joinall
import requests
import argparse

# TODO clean code

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={youtube_id}'
YOUTUBE_COMMENTS_AJAX_URL_OLD = 'https://www.youtube.com/comment_ajax'
YOUTUBE_COMMENTS_AJAX_URL_NEW = 'https://www.youtube.com/comment_service_ajax'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


def find_value(html, key, num_chars=2, separator='"'):
    pos_begin = html.find(key) + len(key) + num_chars
    pos_end = html.find(separator, pos_begin)
    return html[pos_begin: pos_end]


def ajax_request(session, url, params=None, data=None, headers=None, retries=5, sleep=20):
    for _ in range(retries):
        response = session.post(url, params=params, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            return {}
        else:
            time.sleep(sleep)


def download_comments(youtube_id, sleep=.1):
    if 'liveStreamability' in requests.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id)).text:
        print('Live stream detected! Not all comments may be downloaded.')
        return download_comments_new_api(youtube_id, sleep)
    return download_comments_old_api(youtube_id, sleep)


def download_comments_new_api(youtube_id, sleep=1):
    # Use the new youtube API to download some comments
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    html = response.text
    session_token = find_value(html, 'XSRF_TOKEN', 3)

    data = json.loads(find_value(html, 'window["ytInitialData"] = ', 0, '\n').rstrip(';'))
    ncd = next(search_dict(data, 'nextContinuationData'))
    continuations = [(ncd['continuation'], ncd['clickTrackingParams'])]

    while continuations:
        continuation, itct = continuations.pop()
        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL_NEW,
                                params={'action_get_comments': 1,
                                        'pbj': 1,
                                        'ctoken': continuation,
                                        'continuation': continuation,
                                        'itct': itct},
                                data={'session_token': session_token},
                                headers={'X-YouTube-Client-Name': '1',
                                         'X-YouTube-Client-Version': '2.20200207.03.01'})

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        # Ordering matters. The newest continuations should go first.
        continuations = [(ncd['continuation'], ncd['clickTrackingParams'])
                         for ncd in search_dict(response, 'nextContinuationData')] + continuations

        for comment in search_dict(response, 'commentRenderer'):
            yield {'cid': comment['commentId'],
                   'text': ''.join([c['text'] for c in comment['contentText']['runs']]),
                   'time': comment['publishedTimeText']['runs'][0]['text'],
                   'author': comment.get('authorText', {}).get('simpleText', ''),
                   'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                   'photo': comment['authorThumbnail']['thumbnails'][-1]['url']}

        time.sleep(sleep)


def search_dict(partial, key):
    if isinstance(partial, dict):
        for k, v in partial.items():
            if k == key:
                yield v
            else:
                for o in search_dict(v, key):
                    yield o
    elif isinstance(partial, list):
        for i in partial:
            for o in search_dict(i, key):
                yield o


def download_comments_old_api(youtube_id, sleep=1):
    # Use the old youtube API to download all comments (does not work for live streams)
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    # Get Youtube page with initial comments
    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    html = response.text

    reply_cids = extract_reply_cids(html)

    ret_cids = []
    for comment in extract_comments(html):
        ret_cids.append(comment['cid'])
        yield comment

    page_token = find_value(html, 'data-token')
    session_token = find_value(html, 'XSRF_TOKEN', 3)

    first_iteration = True

    # Get remaining comments (the same as pressing the 'Show more' button)
    while page_token:
        data = {'video_id': youtube_id,
                'session_token': session_token}

        params = {'action_load_comments': 1,
                  'order_by_time': True,
                  'filter': youtube_id}

        if first_iteration:
            params['order_menu'] = True
        else:
            data['page_token'] = page_token

        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL_OLD, params, data)
        if not response:
            break

        page_token, html = response.get('page_token', None), response['html_content']

        reply_cids += extract_reply_cids(html)
        for comment in extract_comments(html):
            if comment['cid'] not in ret_cids:
                ret_cids.append(comment['cid'])
                yield comment

        first_iteration = False
        time.sleep(sleep)

    # Get replies (the same as pressing the 'View all X replies' link)
    for cid in reply_cids:
        data = {'comment_id': cid,
                'video_id': youtube_id,
                'can_reply': 1,
                'session_token': session_token}

        params = {'action_load_replies': 1,
                  'order_by_time': True,
                  'filter': youtube_id,
                  'tab': 'inbox'}

        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL_OLD, params, data)
        if not response:
            break

        html = response['html_content']

        for comment in extract_comments(html):
            if comment['cid'] not in ret_cids:
                ret_cids.append(comment['cid'])
                yield comment
        time.sleep(sleep)


def extract_comments(html):
    tree = lxml.html.fromstring(html)
    item_sel = CSSSelector('.comment-item')
    text_sel = CSSSelector('.comment-text-content')
    time_sel = CSSSelector('.time')
    author_sel = CSSSelector('.user-name')
    vote_sel = CSSSelector('.like-count.off')
    photo_sel = CSSSelector('.user-photo')

    for item in item_sel(tree):
        yield {'cid': item.get('data-cid'),
               'text': text_sel(item)[0].text_content(),
               'time': time_sel(item)[0].text_content().strip(),
               'author': author_sel(item)[0].text_content(),
               'votes': vote_sel(item)[0].text_content() if len(vote_sel(item)) > 0 else 0,
               'photo': photo_sel(item)[0].get('src')}


def extract_reply_cids(html):
    tree = lxml.html.fromstring(html)
    sel = CSSSelector('.comment-replies-header > .load-comments')
    return [i.get('data-cid') for i in sel(tree)]


def parse_args():
    ''' Create the arguments '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--connections", default=10, type=int,
                        help="Set how many concurrent connections to use")
    return parser.parse_args()


# def concurrency(urls):
#     ''' Open all the greenlet threads '''
#     args = parse_args()
#     pool = Pool(args.connections)
#     jobs = [pool.spawn(make_request, url) for url in urls]
#     return joinall(jobs)


def download_video_comments(video_id, channel_id):
    output = "output/{}/{}.json".format(channel_id, video_id)
    print('Downloading Youtube comments for video:', video_id)
    count = 0
    print('hi1')
    with io.open(output, 'w', encoding='utf8') as fp:
        print('hi2')
        sys.stdout.write('Downloaded %d comment(s)\r' % count)
        print('hi3')
        sys.stdout.flush()
        print('hi4')
        for comment in download_comments(video_id):
            print('hi5')
            comment_json = json.dumps(comment, ensure_ascii=False)
            print('hi6')
            print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json,
                  file=fp)
            print('hi7')
            count += 1
            print('hi8')
            sys.stdout.write('Downloaded %d comment(s)\r' % count)
            print('hi9')
            sys.stdout.flush()
            print('hi10')
            # if limit and count >= limit:
            #     break
    print('\nDone!')
    pass


def main(argv):
    parser = argparse.ArgumentParser(add_help=False,
                                     description=('Download Youtube comments without using the Youtube API'))
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    parser.add_argument('--channelid', '-c', help='ID of Youtube channel for which to download the comments')
    parser.add_argument("-n", "--connections", default=10, type=int,help="Set how many concurrent connections to use")

    # parser.add_argument('--youtubeid', '-y', help='ID of Youtube video for which to download the comments')
    # parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')
    # parser.add_argument('--limit', '-l', type=int, help='Limit the number of comments')

    # add channel, remove output
    # output is to be database automatically

    try:
        args = parser.parse_args(argv)
        channel_id = args.channelid

        # if not youtube_id or not channelid:
        if not channel_id:
            parser.print_usage()
            raise ValueError('you need to specify a Youtube Video ID or a Youtube Channel ID')

        if channel_id:
            # get videos
            video_items = get_channel_video_items(channel_id)
            video_ids = fetch_save_video_items_return_video_id(video_items, channel_id)
            Path("./output/{}".format(channel_id)).mkdir(parents=True, exist_ok=True)

            pool = Pool(args.connections)
            jobs = [pool.spawn(download_video_comments, video_id, channel_id) for video_id in video_ids]
            joinall(jobs)

            # for i, youtube_id in enumerate(video_ids):
            #     print("iteration {}".format(i))
            # save as json
            # save in sqlite

    except Exception as e:
        print('Error:', str(e))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
