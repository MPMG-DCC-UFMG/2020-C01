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
    
    
def get_load_notifications(path = 'data/notifications/'):
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
        

def save_notification_(message, gid, path='data/notifications/'):
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
        message_group_filename = 'data/groupID/%s.json'%(gid)
        with open(message_group_filename, 'a') as json_file:
            json.dump(item, json_file)
            print('', file=json_file)
        message_day_filename = file_name
        # Save message on file for all messages of the day
        with open(message_day_filename, 'a') as json_file:
            json.dump(item, json_file)
            print('', file=json_file)
        reference_mid_filename = 'data/mids/%s.txt' %(gid)
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


        pathlib.Path("/data/metadata").mkdir(parents=True, exist_ok=True)
        
        today_date = datetime.date.today().strftime("%Y_%m_%d")
        
        print('>>>>>>>>>>> Loading chat ids')
        #chats = driver.get_all_chat_ids()
        chats = driver.get_all_chats()
        count = 0
       
        for chat in (chats):
            #pprint(chat)
            group = dict()
            if not chat._js_obj['isGroup']: return
            _id = chat.id
            creator = _id.split('-')[0]
            timestamp = _id.split('-')[-1].split('@')[0]
            date = convert_data_from_timestamp(float(timestamp))
            str_date = date.strftime('%Y-%m-%d %H:%M:%S')
            try: name = smart_unicode(chat.name.strip().replace('\t',' '))
            except: name = str(_id)

            kind = chat._js_obj["kind"]
            
            participants = list()
            for member in  driver.group_get_participants(_id):
                user = dict()
                user['name'] = member.verified_name
                user['short_name'] = member.short_name 
                user['formatted_name '] = member.formatted_name  
                user['number'] = member.id
                user['isBusiness'] = member.is_business 
                user['profile_pic'] = member.profile_pic  
                user['profile_pic'] = member.profile_pic  
                participants.append(user)
            
            admins = list()
            #for member in  driver.group_get_admins(_id):
            #    admins.append(member)
            group['group_id'] = _id
            group['creator'] = creator
            group['kind'] = kind
            group['creation'] = dict()
            group['creation']['date'] = str_date
            group['creation']['timestamp'] = timestamp
            group['title'] = name
            group['members'] = participants
            group['admins'] = admins
            print(group)
    



if __name__ == '__main__':
        try:
            webCrawler( )
        #else:
        except Exception as e:
            error_time = str(datetime.datetime.now())
            error_msg  = str(e).strip()
            with open('/data/errors.txt', 'a') as ferror:
                print("%s >> Error:\t%s"   %(error_time, error_msg))
                print("%s >> Error:\t%s"   %(error_time, error_msg), file=ferror)

