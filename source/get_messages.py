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



def get_text_from_message(message, file_t, chatID, msg_id):
        
        user = smart_str(message.sender.id)
        user = user.replace(' ', '').strip()
        user = user.split('@')[0]
        user = '+'+user
        user =  hashlib.md5(user).hexdigest()
        if hasattr(message, 'safe_content') and  not isinstance(message, MESSAGE.MediaMessage)  and not isinstance(message, MESSAGE.MMSMessage):
            print(smart_str(message), file=file_t)
            print(smart_str(msg_id), file=file_t) 
            print(smart_str(chatID), file=file_t) 
            print(smart_str(message.content), file=file_t)
            print(smart_str(user), file=file_t)
            return message.content
        else:
            try:
                filename = get_filename(message, message.filename)
                print(smart_str(message), file=file_t)
                print(smart_str(msg_id), file=file_t)
                print(smart_str(chatID), file=file_t)
                print(filename, file=file_t)
                print(smart_str(user), file=file_t)
            except:  
                print(smart_str(message), file=file_t)
                print(smart_str(msg_id), file=file_t)               
                print(smart_str(chatID), file=file_t)           
                print('<NoFile>', file=file_t) 
                print(smart_str(user), file=file_t)
            return message


def convert_data_to_timestamp(time_message):
    time_obj = datetime.datetime.strptime(time_message, '%Y-%m-%d %H:%M:%S')
    time_insecond = calendar.timegm(time_obj.utctimetuple())
    return time_insecond

def convert_data_from_timestamp(time_message):
    time_obj = datetime.datetime.fromtimestamp(time_message)
    return time_obj


def get_load_messages(path = '/data/groupID/'):
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
                date = tokens[5].split(' ')[0]
                if date >= maxDate: maxDate = date
                messagesIDs[ID]['messages'].add(tokens[0])
        messagesIDs[ID]['date'] = date
    return messagesIDs
    
    
def get_groups_metadata(driver):
    titles = dict()
    with open('/data/titles.txt', 'r') as ft:
        for line in ft.readlines():
            try:
                tks   = line.strip().split('\t')
                link  = tks[0]
                week  = tks[1]
                title = smart_str(tks[2].strip())
                if len(title) <= 2: continue
                titles[title] = dict()
                titles[title]['title'] = title
                titles[title]['link']  = link
                titles[title]['week']  = week
            except : continue
           
    chats = driver.get_all_chats()
    with open('/data/all_chats_id.txt', 'w') as fchat:
        for chat in chats:
            #try:
                if not chat._js_obj['isGroup']: continue
                _id = chat.id
                creator = _id.split('-')[0]
                creator = hashlib.md5(creator).hexdigest()
                timestamp = _id.split('-')[-1].split('@')[0]
                date = convert_data_from_timestamp(float(timestamp))
                try: name = smart_str(chat.name.strip().replace('\t',' '))
                except: name = str(_id)
                
                if name in list(titles.keys()): 
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>',name)
                try: 
                    group = titles[name]
                    title = titles[name]['title']
                    link = titles[name]['link']
                    week = titles[name]['week']
                except:
                    title = name
                    link = 'LinkNotFound'
                    week = 'WeekNotFound'
                participants = driver.group_get_participants(_id)
                plist = list()
                clist = list()
                for p in participants:
                    pn = p.id.split('@')[0]
                    try:    phone = phonenumbers.parse(pn)
                    except: phone = phonenumbers.parse('+'+pn)
                    country =  phone.country_code
                    userID = hashlib.md5(pn).hexdigest() 
                    plist.append(userID)
                    clist.append(country)
                final_string = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(link, week, _id, creator, timestamp, date, title, clist, plist)
                print(smart_str(final_string))
                print(smart_str(final_string), file=fchat)
            #except:    continue


def get_notification_type(message, gid):
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
        name = smart_str( message._js_obj['chat']['contact']['name'])
        name = name.replace('\t',' ')
        name = name.replace('\n',' ')
        name = name.replace('\r','')
        
        date = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        
        try:sender_user = message._js_obj['sender']['id']['user']
        except: sender_user = 'No_sender'
        
        
        try:from_user = message._js_obj['from']['user']
        except: from_user = 'No_user'    
        
        try: alert   = readable[message.type][message.subtype]
        except KeyError as e: alert = 'Other'
        #if subtype == 'remove':
            #pprint(vars(message)) 
        
        our_phones = ['491705423146', '491705933848']
        notification_file = '/data/notifications/' + gid + '.txt'
        noti_file   = '/data/all_notifications.txt'
        banned_file = '/data/banned.txt'
        finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(gid, msgtype, subtype, timestamp, date, name, sender_user, from_user )
        with open(notification_file, 'a') as fnot:         
            with open(noti_file, 'a') as fn:         
                print(finalstring)
                print(finalstring, file=fnot)
                print(finalstring, file=fn)
        
        if subtype == 'remove' and from_user in our_phones:
            with open(banned_file, 'a') as fb:
                print(finalstring, file=fb)


def save_message(message, group_name, msg_id_path, chatID, msg_id, file_t):
        
        #pprint(vars(message))
        #print 'TYPE', type(message)
        #print 'ATT', dir(message)
        #print 'VARS', (vars(object))
        if not message.sender: return
        sender = message.sender.id
        sender = sender.replace(' ', '').strip()
        sender = sender.split('@')[0]
        sender = ('+'+sender)
        #sender =  hashlib.md5(sender).hexdigest()

        try:    phone = phonenumbers.parse(sender)
        except: phone = phonenumbers.parse('+'+sender)
        country =  phone.country_code
        
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
            
    
        with open(mid_filename, 'a') as fmid:
            messageLine = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%r\t%s\t%s' %(mid, gid, group_name, country, smart_str(sender), smart_str(date), mediatype, MediaMessage, smart_str(filename), process_content(content))
            print(messageLine, file=fmid)
            print(messageLine, file=file_t)
            print(messageLine)
            
            

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
        pathlib.Path("/data/groupID").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/audio").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/video").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/notifications").mkdir(parents=True, exist_ok=True)

        files = {}
        today_date = datetime.date.today().strftime("%Y_%m_%d")
        today_date = 'test'
        date_format = "%Y-%m-%d"
                
        
        # print('>>>>>>>>>>> Getting Groups Metadata')
        # #get_groups_metadata(driver)
        msg_id_path  = '/data/groupID/'
        # messagesID   = get_load_messages(msg_id_path)
        all_messages = list()
        file_name = "/data/AllMessages_" + today_date+ ".txt"  
        file_t = open(file_name, 'a') 
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
        #if reverse: chats = reversed(all_chats)
        
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
            
            chat_print = "<Group chat - {name}: {id}, {participants} participants - at {time}!!>".format( name=s_name, id=gid,  participants=len(members), time=str_date)
            print('>>>>>Loading messages from', chat_print)
        
            start_date = min_date
            till_date = datetime.datetime.strptime(start_date, date_format)
            

            # LOAD MESSAGES FROM WHATSAPP SINCE MIN_DATE
            #messages = chat.load_all_earlier_messages()
            messages = chat.load_earlier_messages_till(till_date)
            #messages = chat.get_messages()
            #messages = driver.get_all_messages_in_chat(chat)
            messages = driver.get_all_message_ids_in_chat(chat, include_notifications=True)
            
            local_messages = list()
            print('>>>>>Total messages %d' %( len(messages) ))
            with open('/data/all_msg_ids.txt', 'a') as fo:
                for mid in messages : 
                    local_messages.append([mid, gid])
                    all_messages.append([mid, gid])
                    print('%s\t%s' %(mid, gid), file=fo)
            count +=1
            
            for msg in local_messages:
                count +=1
                gid = msg[1].split('@')[0]
                mid = msg[0]
               
                
                try:
                    j = driver.get_message_by_id(mid)
                except Exception as e:
                    print('Error getting a message >>', e)
                    continue
                if not j : continue
                #print 'Message: ', count, gid, mid
                
                #get_notification_type(message, gid)
                try:    date = get_date_from_message(j)
                except: continue
                
                if date > max_date: break
                if date < start_date: continue
                if today_date != date:  #update day
                        today_date = date
                        file_t.close()
                        file_name = "/data/text/AllMessages_" + today_date+ ".txt"
                        file_t = open(file_name, 'a')
                #text = get_text_from_message(j, file_t, gid, mid)        
                save_message(j, s_name, msg_id_path, gid, mid, file_t)
                
                
                try:
                    #signal.signal(signal.SIGALRM, timeout)    
                    #signal.alarm(TIMEOUT)
                    get_image_from_message(j)
                    #signal.signal(signal.SIGALRM, signal.SIG_IGN)
                    #signal.alarm(0) 
                except Exception as ei: print('!!!!Error getting image!!!! ', ei)
                    
                try:
                    #signal.signal(signal.SIGALRM, timeout)
                    #signal.alarm(TIMEOUT)    
                    get_video_from_message(j)
                    #signal.alarm(0)  
                    #signal.signal(signal.SIGALRM, signal.SIG_IGN)
                except Exception as ev: print('!!!!Error getting video!!!! ', ev)
                
                try:
                    #signal.signal(signal.SIGALRM, timeout)
                    #signal.alarm(TIMEOUT)
                    get_audio_from_message(j)
                    #signal.alarm(0) 
                    #signal.signal(signal.SIGALRM, signal.SIG_IGN)
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
                min_date = '2020-05-20'
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

