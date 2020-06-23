# -*- coding: utf-8 -*-
__author__ = "Philipe Melo"
__email__ = "philipe@dcc.ufmg.br"


import json
import gzip
import pytz
import traceback
import psycopg2
from unicodedata import normalize

import imagehash
import hash_functions as HASH

import sys
import os
import  re
import time
import hashlib
import imagehash
import imghdr
from PIL import Image    
from os import listdir
from os.path import isfile, join

from importlib import import_module
from django.utils.encoding import smart_str, smart_unicode
from datetime import date as DATE
from datetime import timedelta
from datetime import datetime


def jaccard_similarity(x,y):
    try: 
        intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
        union_cardinality = len(set.union(*[set(x), set(y)]))
        return intersection_cardinality/float(union_cardinality)
    except ZeroDivisionError:
        return 0

def compare_texts(text1, text2):
    if text1 is None or text2 is None: return 0.0
    bow_text1 = text1.split()
    bow_text2 = text2.split()
    score = jaccard_similarity(text1, text2)
    return score


def convert_messages_to_json(messages, media, date):

    filename = './jsons_%ss/all_%s_%s.json' %(media, media, date)
    with open(filename, 'w') as json_file:
        msg_json = json.dumps(messages, json_file)

  
def get_date_filename(date):
    return 'AllMessages_%s.txt' %(date)



def process_data(media, media_paths, method, hash_methods, dates, output='default'):
    medias = dict()
    hashes = dict()
    
    medias = load_files_list(media, hash_methods)
    #for k in hashes.keys(): print k, hashes[k]
    #for k in medias.keys(): print k, medias[k]
      
    messages = dict()
    for date in dates:
        for path in media_paths:
            json_filename=get_date_filename(date)
            if not isfile(path+json_filename): continue
            with open(path+json_filename, 'r') as fdata:
                for line in fdata:
                    message = json.loads(line.strip())
                    
                    kind    = message['type']
                    msgID   = message['message_id']
                    
                    if media == kind and isMedia.lower() == 'true':
                        filename = message['file']
                        hash     = message['hash']
                    
                        try: A = hashes[hash]
                        except KeyError as e:
                            hashes[hash] = dict()
                            hashes[hash]['hash'] = hash
                            hashes[hash]['checksum'] = message['checksum']
                            if 'phash' in messages.keys():  hashes[hash]['phash'] = message['phash']
                            hashes[hash]['first_share'] = message['date']
                            hashes[hash]['total'] = 0
                            hashes[hash]['total_groups'] = 0
                            hashes[hash]['total_users'] = 0
                            hashes[hash]['groups_shared'] = set()
                            hashes[hash]['users_shared'] = set()
                            hashes[hash]['messages'] = list()
                        
                        #ADD MESSAGE TO HASH
                        if message['date'] < hashes[hash]['first_share']: hashes[hash]['first_share'] = message['date']
                        hashes[hash]['total'] += 1
                        hashes[hash]['groups_shared'].add(messages['group_name'])
                        hashes[hash]['users_shared'].add(messages['sender'])
                        hashes[hash]['messages'].append(message)
                        hashes[hash]['total_groups'] = len(hashes[hash]['groups_shared'])
                        hashes[hash]['total_users']  = len(hashes[hash]['users_shared'])
                        
    
    if output == 'default':
        output = 'merged_data_%s-%s_%s-%s.json' (%media, method, dates[0], dates[-1])
    filename = output
    with open(filename, 'w') as json_file:
        #js = json.dumps(messages)
        json.dump(messages, json_file, ensure_ascii=False, indent=4)
    
    return messages
    

    
    
def get_days_list(start_date, end_date):

    formatter = '%Y-%m-%d'
    
    date1 = datetime.strptime(start_date, formatter)
    date2 = datetime.strptime(end_date, formatter)
    delta = date2 - date1       # as timedelta

    dates_list = list()
    for i in range(delta.days + 1):
        day = date1 + timedelta(days=i)
        date_string = day.strftime(formatter)
        dates_list.append(date_string)

    return dates_list

    
    
def main():
    in_media  = (sys.argv[1])
    method = (sys.argv[2])
    start_date = (sys.argv[3])
    today = DATE.today().strftime('%Y-%m-%d')
    try:    end_date = (sys.argv[3])
    except: end_date = today
    
    
    dates = get_days_list(start_date, end_date)
    print 'Getting JSONS for days:', dates
    
    mediapath = list()
    mediapath.append('/data/text/')

             
    print('Grouping %s hashes of %s from %s to %s' %(method, in_media, start_date, end_date))
    if in_media == 'images':
        media = 'image'
        #hash_methods = ['phash', 'checksum', 'pdq', 'ahash',  'dhash', 'whash-haar', 'whash-db4']
        hash_methods = ['checksum', 'phash']
        messages = process_data_day(media, mediapath, method, hash_methods, dates)
    elif in_media == 'videos':
        media = 'video'
        hash_methods = ['checksum']
        messages = process_data_day(media, mediapath, method, hash_methods, dates)
    elif in_media == 'audios':
        media = 'audio'
        hash_methods = ['checksum']
        messages = process_data_day(media, mediapath, method, hash_methods, dates)
    elif in_media == 'texts':
        media = 'text'
        hash_methods = ['checksum']
        messages = process_data_day(media, mediapath, method, hash_methods, dates)
    elif in_media == 'urls':
        media = 'url'
        hash_methods = ['checksum']
        messages = process_url_day(media, mediapath, method, hash_methods, dates)
    else:
        media = 'image'
    #convert_messages_to_json(messages, media, date)
       
if __name__ == "__main__":
    main()
    exit()
