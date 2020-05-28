#!/usr/bin/env python3
import json
import pickle

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
