from __future__ import print_function
from builtins import str
import time, random
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage, MMSMessage
from webwhatsapi.objects.message import NotificationMessage
from webwhatsapi.objects import message as MESSAGE
import sys
from PIL import Image
from webwhatsapi.helper import safe_str
from webwhatsapi.objects.contact import Contact
import calendar
import datetime
import hashlib
import os
import pathlib
import json
from pprint import pprint
from os import listdir
from os.path import isfile, join

import phonenumbers
from phonenumbers.phonenumberutil import (
    region_code_for_country_code,
    region_code_for_number,
)

import signal

all_files = dict()
all_files['image'] = dict()
all_files['video'] = dict()
all_files['audio'] = dict()

def smart_str(x):
    if isinstance(x, int) or isinstance(x, float):
        return str(x,"utf-8")
    return x


TIMEOUT = 45
def timeout(signum, frame):
    print('!!!!Error getting media!!!! ')
    raise Exception("Timeout Error!!")



def process_content(string):
    string = string.strip( )
    string = string.replace('\r','')
    string = string.replace('\n',' ')
    string = string.replace('\t',' ')
    try : string = smart_str(string)
    except : string = 'NoName'
    return string



def get_filename(message, filename):
    mediaID = message.id.split('.')[-1]
    filename = '%s_%s_%s.%s' %(message.type, filename.split('.')[0], mediaID, filename.split('.')[-1])
    return filename

def get_messages_by_group(driver):
    msg_list = driver.get_unread(include_me=False, include_notifications=False, use_unread_count=False)
    return msg_list


def get_image_from_message(message):
    path = '/data/image/'
    if message.type == 'image':
            #print smart_str(str(message))
            #pprint(vars(message)) 
            #exit()
            try:
                all_files['image'] [message.filename] += 1
                
            except KeyError as e:
                all_files['image'] [message.filename] = 1
            
            filename = get_filename(message, message.filename)
            #print 'FILENAME CHANGED', message.filename, '>>>>>>>', filename
            message.filename = filename
            if not os.path.isfile(path+filename) :
                message.save_media(path, force_download=True)
            return 1
    return 0


def get_video_from_message(message):
    path = '/data/video/'
    if message.type == 'video':
            try:
                all_files['video'] [message.filename] += 1
                
            except KeyError as e:
                all_files['video'] [message.filename] = 1
            
            filename = get_filename(message, message.filename)
            message.filename = filename
            if not os.path.isfile(path+filename) :
                message.save_media(path, force_download=True)
            return 1
    return 0




def get_audio_from_message(message):
    path = '/data/audio/'
    if message.type == 'audio':
            try:
                all_files['audio'] [message.filename] += 1
                
            except KeyError as e:
                all_files['audio'] [message.filename] = 1
            
            filename = get_filename(message, message.filename)
            message.filename = filename
            if not os.path.isfile(path+filename) :
                message.save_media(path, force_download=True)
            return 1
    return 0




def get_date_from_message(message):
    t = str(message)
    index = t.find(' at ') + 4
    index2 = index + 10
    date = t[index:index2]
    #date = date.replace('-','_')
    return date



def get_group_from_message(message):
    t = str(message)
    index = t.find('Group chat -') + 12
    index2 = index + 10
    group = t[index:].split(':')[0]
    return group




def convert_data_to_timestamp(time_message):
    time_obj = datetime.datetime.strptime(time_message, '%Y-%m-%d %H:%M:%S')
    time_insecond = calendar.timegm(time_obj.utctimetuple())
    return time_insecond

def convert_data_from_timestamp(time_message):
    time_obj = datetime.datetime.fromtimestamp(time_message)
    return time_obj

def get_load_notifications(path = '/data/notifications/'):
    messagesIDs = dict()
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for f in allfiles:
        ID = f.split('.')[0].split('@')[0]
        messagesIDs[ID] = set()
        with open(path+f, 'r') as fin:
            for line in fin:
                data = json.loads(line.strip())
                mid = data['message_id']
                messagesIDs[ID].add(mid)
                
    return messagesIDs
  
  
def get_load_messages(path = '/data/mids/'):
    messagesIDs = dict()
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for f in allfiles:
        ID = f.split('.')[0].split('@')[0]
        messagesIDs[ID] = dict()
        messagesIDs[ID]['messages'] = set()
        maxDate = '2000-01-01'
        with open(path+f, 'r') as fin:
            for line in fin:
                tokens = line.strip().split('\t')
                date = tokens[2].split(' ')[0]
                if date >= maxDate: maxDate = date
                messagesIDs[ID]['messages'].add(tokens[0])
        messagesIDs[ID]['date'] = date
    return messagesIDs
    
    
def get_load_notifications(path = '/data/notifications/'):
    messagesIDs = dict()
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for f in allfiles:
        ID = f.split('.')[0].split('@')[0]
        messagesIDs[ID] = set()
        with open(path+f, 'r') as fin:
            for line in fin:
                data = json.loads(line.strip())
                mid = data['message_id']
                messagesIDs[ID].add(mid)
                
    return messagesIDs
    

def isNotification(messageID):
    if messageID.find('true') < 0: return False
    else: return True
        

def save_notification_(message, gid, path='/data/notifications/'):
    if(isinstance(message, NotificationMessage) ):
        #print 'NOTIFICATION', message
        readable = {
                        'call_log': {
                            'miss': "Missed Call",
                        },
                        'e2e_notification': {
                            'encrypt': "Messages now Encrypted"
                        },
                        'gp2': {
                            'invite': "Joined an invite link",
                            'create': "Created group",
                            'add': "Added to group",
                            'remove': "Removed from group",
                            'leave': "Left the group",
                            'description': "Changed the group description. Click to view."
                        }
        }
        msgtype = message.type
        msgtype = message._js_obj['type']
        subtype = message._js_obj['subtype']
        timestamp = message._js_obj['timestamp']
        name = message._js_obj['chat']['contact']['name']
        name = process_content(name)
        own_phones = ['5531900000000']
        date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        
        try:sender_user = message._js_obj['sender']['id']['user']
        except: sender_user = 'No_sender'
        
        try:from_user = message._js_obj['from']['user']
        except: from_user = 'No_user'    
        
        try: alert   = readable[message.type][message.subtype]
        except KeyError as e: alert = 'Other'
        
        notification = dict()
        notification['message_id'] = str(message.id)
        notification['group_id'] = gid
        notification['type'] = msgtype
        notification['subtype'] = msgtype
        notification['timestamp'] = timestamp
        notification['date'] = date
        notification['sender'] = sender_user
        notification['contact_name'] = name
        notification['from'] = from_user
      
        if message._js_obj['recipients']:
            for item in message._js_obj['recipients']:
                try:recipient_user = item['user']
                except: recipient_user = 'No_user'    
                notification['recipient'] = recipient_user
                finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(
                str(message.id), gid, msgtype, subtype, timestamp, date, name, sender_user, recipient_user, from_user )
                print(finalstring)
                filename = '%s%s.json'%(path, gid)
                with open(filename, 'a') as json_file:
                    json.dump(notification, json_file)
                    print('', file=json_file)
        
        else:
            try:recipient_user = message._js_obj['recipients'][0]['user']
            except: recipient_user = 'No_user'    
            notification['recipient'] = recipient_user
            finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(
            str(message.id), gid, msgtype, subtype, timestamp, date, name, sender_user, recipient_user, from_user )
            print(finalstring)
            filename = '%s%s.json'%(path, gid)
            with open(filename, 'a') as json_file:
                json.dump(notification, json_file)
                print('', file=json_file)
           
        return notification  


def save_message(message, group_name, msg_id_path, chatID, msg_id, file_name):
        
        if not message.sender: return
        item = dict()
        sender = message.sender.id
        sender = sender.replace(' ', '').strip()
        sender = sender.split('@')[0]
        sender = ('+'+sender)

        try:    phone = phonenumbers.parse(sender)
        except: phone = phonenumbers.parse('+'+sender)
        country_code =  phone.country_code
        country =       region_code_for_country_code(country_code)
        
        mid = smart_str(msg_id)
        gid = smart_str(chatID)
        mid_filename = msg_id_path+gid+'.txt'
        name = get_group_from_message(message)

        try : 
            content = message.content
            content = smart_str(content)
            content = smart_str(content.replace('\n', ' '))
        except: content = '<NoContent>'
        
        t = str(message)
        index = t.find(' at ') + 4
        index2 = index + 19
        date = str(t[index:index2])
        date = smart_str(date.replace(' ','\t').strip())
        
        filename = '<NoFile>'
        mediatype = 'text'
        MediaMessage = False
        if isinstance(message,  MESSAGE.MediaMessage) or isinstance(message,  MESSAGE.MMSMessage):
            MediaMessage = True
            mediatype = smart_str(message.type)
            try: 
                filename = get_filename(message, message.filename)
                content = '<'+filename+'>'
            except: filename = '<NoFile>'
            if hasattr(message, 'caption'):
                content = smart_str(message.caption)
                
        phash    = '<PHASH>'    
        checksum = '<CHECKSUM>'    
        item['message_id']   = mid
        item['group_id']     = gid
        item['group_name']   = group_name
        item['group_name']   = group_name
        item['country']      = country
        item['sender']       = smart_str(sender)
        item['date']         = smart_str(date)
        item['type']         = mediatype
        item['file']         = smart_str(filename)
        item['content']      = smart_str(content)
        if mediatype == 'video' or mediatype == 'image' or mediatype =='audio':
            item['checksum'] = checksum
        if mediatype == 'image': 
            item['phash'] = phash
        
        messageLine = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%r\t%s\t%s' %(mid, gid, group_name, country, smart_str(sender), smart_str(date), mediatype, checksum, smart_str(filename), process_content(content))
        print(messageLine)
        
        # Save message on group ID file
        message_group_filename = '/data/groupID/%s.json'%(gid)
        with open(message_group_filename, 'a') as json_file:
            json.dump(item, json_file)
            print('', file=json_file)
        message_day_filename = file_name
        # Save message on file for all messages of the day
        with open(message_day_filename, 'a') as json_file:
            json.dump(item, json_file)
            print('', file=json_file)
        reference_mid_filename = '/data/mids/%s.txt' %(gid)
        #Save mid reference for future checks
        with open(reference_mid_filename, 'a') as fmid:
            messageLine = '%s\t%s\t%s' %(mid, gid, smart_str(date))
            print(messageLine, file=fmid)
        
        return item
            
            

def webCrawler(load, min_date, max_date, profile_path = "/data/firefox_cache"):
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
    driver = WhatsAPIDriver(loadstyles=True, profile=profile_path, client="remote", command_executor=os.environ["SELENIUM"])

    try:
        print("Waiting for QR")
        driver.wait_for_login()
        print("Saving session")
        driver.save_firefox_profile(remove_old=False)
        print("Bot started")


        pathlib.Path("/data/text").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/image").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/audio").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/video").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/groupID").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/notifications").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/mids").mkdir(parents=True, exist_ok=True)

        files = {}
        today_date = datetime.date.today().strftime("%Y_%m_%d")
        today_date = 'test'
        date_format = "%Y-%m-%d"
                
        
        # print('>>>>>>>>>>> Getting Groups Metadata')
        # #get_groups_metadata(driver)
        msg_id_path  = '/data/groupID/'
        
        print('>>>>>>>>>>> Loading previous saved Messages')
        messagesID      = get_load_messages( )
        notificationsID = get_load_notifications( )

        
        all_messages = list()
        file_name = "/data/AllMessages_" + today_date+ ".txt"  
        start_date = min_date
        
        reverse = True
        reverse_messages = False
       
        print('>>>>>>>>>>>>Getting Groups Messages...', end=' ')
        chats = driver.get_all_chats()
        #chats = driver.get_all_chat_ids()
        count = 0
        all_chats = list(chats)
        
        print(' DONE! %d chats loaded!' %(len(all_chats)))
        random.shuffle(all_chats) 
        
        for chat in (all_chats):
            #pprint(vars(chat)) 
            if not chat._js_obj['isGroup']: continue
            
            #PRINT CHAT INFORMATION
            gid = chat.id
            gid = gid.split('@')[0]
            s_name = process_content(chat.name)
            members  = chat._js_obj['groupMetadata']['participants']
            creator   = gid.split('-')[0]
            timestamp = gid.split('-')[-1]
            date = convert_data_from_timestamp(float(timestamp))
            str_date = date.strftime('%Y-%m-%d %H:%M:%S')
            try: msgids = messagesID[gid]
            except KeyError as e: 
                messagesID[gid] = dict()
                messagesID[gid]['messages'] = set()
                messagesID[gid]['date'] = '2000-01-01'
            
            chat_print = "<Group chat - {name}: {id}, {participants} participants - at {time}!!>".format( name=s_name.encode('utf-8'), id=gid,  participants=len(members), time=str_date)
            print('>>>>>Loading messages from', chat_print)

            #PROCESS PREVIOUS LOADED MESSAGES ID AND LAST DATE    
            if messagesID[gid]['date'] > max_date: continue
            if messagesID[gid]['date'] > min_date:
                start_date = messagesID[gid]['date']
                #start_date = min_date
                till_date = datetime.datetime.strptime(start_date, date_format)
            else:
                start_date = min_date
                till_date = datetime.datetime.strptime(start_date, date_format)
            

            # LOAD MESSAGES FROM WHATSAPP SINCE MIN_DATE
            #messages = chat.load_all_earlier_messages()
            messages = chat.load_earlier_messages_till(till_date)
            messages = driver.get_all_message_ids_in_chat(chat, include_notifications=True)
            
            local_messages = list()
            print('>>>>>Total messages %d' %( len(messages) ))
            for mid in messages : 
                local_messages.append([mid, gid])
                all_messages.append([mid, gid])
            count +=1
            
            for msg in local_messages:
                count +=1
                gid = msg[1].split('@')[0]
                mid = msg[0]
                
                 
                if isNotification(mid):
                    if gid not in notificationsID.keys(): notificationsID[gid] = set()
                    if mid.strip() in notificationsID[gid]: continue
                    j = driver.get_message_by_id(mid)
                    save_notification_(j, gid,  path='/data/notifications/')
               
                else:
                    if mid.strip() in messagesID[gid]['messages']:
                        print('Message: %d >>> %s from %s was CHECKED' %(count, mid, gid))
                        continue
                    else:
                        try:
                            j = driver.get_message_by_id(mid)
                        except Exception as e:
                            print('Error getting a message >>', e)
                            continue
                        if not j : continue
                        #print 'Message: ', count, gid, mid
                    
                    try:    date = get_date_from_message(j)
                    except: continue
                    
                    if date > max_date: break
                    if date < start_date: continue
                    if today_date != date:  #update day
                            today_date = date
                            file_name = "/data/text/AllMessages_" + today_date+ ".txt"
                    save_message(j, s_name, msg_id_path, gid, mid, file_name)
                    
                    
                    try:
                        get_image_from_message(j)
                    except Exception as ei: print('!!!!Error getting image!!!! ', ei)
                        
                    try:
                        get_video_from_message(j)
                    except Exception as ev: print('!!!!Error getting video!!!! ', ev)
                    
                    try:
                        get_audio_from_message(j)
                    except Exception as ea: print('!!!!Error getting audio!!!! ', ea)
        
        driver.close()
    except Exception as e:
        print(e)
        driver.close()
        raise Exception(e)
    



if __name__ == '__main__':
    while True:
        #if True:
        try:
            load = True
            try:
                min_date  = (sys.argv[1])
                max_date = (sys.argv[2])
            except:
                min_date = '2020-05-26'
                max_date = '2020-05-27'
            date_format = "%Y-%m-%d"
            till_date = datetime.datetime.strptime(min_date, date_format)
            webCrawler(load, min_date, max_date)
        #else:
        except Exception as e:
            error_time = str(datetime.datetime.now())
            error_msg  = str(e).strip()
            with open('/data/errors.txt', 'a') as ferror:
                print("%s >> Error:\t%s"   %(error_time, error_msg))
                print("%s >> Error:\t%s"   %(error_time, error_msg), file=ferror)
            time.sleep(1500) 

