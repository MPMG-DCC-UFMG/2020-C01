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
from django.utils.encoding import smart_str, smart_unicode
import calendar
import datetime
import hashlib
import os
from pprint import pprint
from os import listdir
from os.path import isfile, join



import phonenumbers
from phonenumbers.phonenumberutil import (
    region_code_for_country_code,
    region_code_for_number,
)


def get_messages_by_group(driver):

    msg_list = driver.get_unread(include_me=False, include_notifications=False, use_unread_count=False)
    return msg_list


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
        
        if hasattr(message, 'safe_content') and  not isinstance(message, MESSAGE.MediaMessage)  and not isinstance(message, MESSAGE.MMSMessage):
            print(smart_str(message), file=file_t)
            print(smart_str(msg_id), file=file_t) 
            print(smart_str(chatID), file=file_t) 
            print(smart_str(message.content), file=file_t)
            print(smart_str(message.sender.id), file=file_t)
            return message.content
        else:
            try:
                print(smart_str(message), file=file_t)
                print(smart_str(msg_id), file=file_t)
                print(smart_str(chatID), file=file_t)
                print(message.filename, file=file_t)
                print(smart_str(message.sender.id), file=file_t)
            except:  
                print(smart_str(message), file=file_t)
                print(smart_str(msg_id), file=file_t)               
                print(smart_str(chatID), file=file_t)           
                print('<NoFile>', file=file_t) 
                print(smart_str(message.sender.id), file=file_t)
            return message


def convert_data_to_timestamp(time_message):
    time_obj = datetime.datetime.strptime(time_message, '%Y-%m-%d %H:%M:%S')
    time_insecond = calendar.timegm(time_obj.utctimetuple())
    return time_insecond

def convert_data_from_timestamp(time_message):
    time_obj = datetime.datetime.fromtimestamp(time_message)
    return time_obj



def get_load_messages(path = 'Messages/groupID/'):
    messagesIDs = dict()
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for f in allfiles:
        ID = f.split('.')[0].split('@')[0]
        messagesIDs[ID] = list()
        with open(path+f, 'r') as fin:
            for line in fin.readlines():
                messagesIDs[ID].append(line.strip().split('\t')[0])
    return messagesIDs
    
    


def load_saved_notifications(filename = 'Messages/all_notifications.txt'):
    messagesIDs = dict()
    with open(filename, 'r') as fin:
        for line in fin:
            ID = line.strip().split('\t')[0]
            messagesIDs[ID] = line.strip()
    return messagesIDs
    
    


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
        our_phones = ['553180211923', '553182806187', '553182806192', '553184046231', '553185945162']
        date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        
        notification_file = 'Messages/notifications/' + gid + '.txt'
        noti_file   = 'Messages/all_notifications.txt'
        banned_file = 'Messages/banned.txt'

        try:sender_user = message._js_obj['sender']['id']['user']
        except: sender_user = 'No_sender'
        
        
        try:from_user = message._js_obj['from']['user']
        except: from_user = 'No_user'    
        
        try: alert   = readable[message.type][message.subtype]
        except KeyError as e: alert = 'Other'
        

        
        if message._js_obj['recipients']:
            for item in message._js_obj['recipients']:
                try:recipient_user = item['user']
                except: recipient_user = 'No_user'    
                
                finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(
                str(message.id), gid, msgtype, subtype, timestamp, date, name, sender_user, recipient_user, from_user )
                with open(notification_file, 'a') as fnot:         
                    with open(noti_file, 'a') as fn:         
                        print(finalstring)
                        print(finalstring, file=fnot)
                        print(finalstring, file=fn)
                
                if subtype == 'remove' and recipient_user in our_phones:
                    with open(banned_file, 'a') as fb:
                        print(finalstring, file=fb)
        else:
            try:recipient_user = message._js_obj['recipients'][0]['user']
            except: recipient_user = 'No_user'    
            
            finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(
            str(message.id), gid, msgtype, subtype, timestamp, date, name, sender_user, recipient_user, from_user )
            with open(notification_file, 'a') as fnot:         
                with open(noti_file, 'a') as fn:         
                    print(finalstring)
                    print(finalstring, file=fnot)
                    print(finalstring, file=fn)
            
            if subtype == 'remove' and recipient_user in our_phones:
                    with open(banned_file, 'a') as fb:
                        print(finalstring, file=fb)
        
        
def webCrawler(load, profile_path, min_date, max_date):
    
    #profile_path = '/home/philipemelo/.mozilla/firefox/rsmycekh.politics_01'
    driver_executable_path="~/Whatsapp/MPI/joined-groups/get_messages/geckodriver"
    os.system('export PATH=$PATH:~/Whatsapp/MPI/joined-groups/get_messages/geckodriver')
    driver = WhatsAPIDriver(loadstyles=True, profile=profile_path)
    
    print("Waiting for QR")
    driver.wait_for_login()
    print("Get Message started")
    files = {}
    today_date = datetime.date.today().strftime("%Y_%m_%d")
    today_date = 'test'
    date_format = "%Y-%m-%d"
    till_date = datetime.datetime.strptime(min_date, date_format)
    
    
    
    #print '>>>>>>>>>>> Getting Groups Metadata'
    #get_groups_metadata(driver)
    msg_id_path  = 'Messages/groupID/'
    messagesID   = get_load_messages(msg_id_path)
    all_messages = list()

    notificationsID = load_saved_notifications(filename = 'Messages/all_notifications.txt')
    
    if load:
        print('>>>>>>>>>>>>Getting Groups Messages')
        chats = driver.get_all_chat_ids()
        all_chats = list(chats)
        random.shuffle(all_chats)
        
        print('>>>>>>>>>>>>All chats loaded')
        #for chatID in reversed(chats):
        for chatID in list(all_chats):
            print('>>>>>Starts chat ', chatID)
            try: chat = driver.get_chat_from_id(chatID)
            except Exception as e:
                print(e)
                continue
                
            #print  chat
            if chat._js_obj['isGroup']:
                #print  '>>>>> '
                gid = chat.id
                creator   = gid.split('-')[0]
                timestamp = gid.split('-')[-1].split('@')[0]
                #date = convert_data_from_timestamp(float(timestamp))
                try : name = smart_unicode(chat.name.strip().replace('\t',' '))
                except : name = 'NoName'
                
                messages = chat.load_earlier_messages_till(till_date)
                messages = driver.get_all_message_ids_in_chat(chat, include_me=True, include_notifications=True)
                
                local_messages = list()
                print('>>>>>Total messages %d' %( len(messages) ))
                #for mid in reversed(messages) : 
                #    local_messages.append([mid, gid])
                #    all_messages.append([mid, gid])
                #count +=1
                count = 0
                for msg in reversed(messages):
                    #if count > 10: break
                    mid = msg
                    try: 
                        A=notificationsID[mid]
                        #print '>>>> NOTIFICATION %s CHECKED ALREADY' %(mid)
                        print('%s' %(A))
                    except:
                        count +=1
                        
                        if mid.find('true') < 0: continue 
                        gid = gid.split('@')[0]
                        try: AA = messagesID[gid]
                        except KeyError as e: messagesID[gid] = list()
                        
                        try:
                            message = driver.get_message_by_id(mid)
                            if not message: continue
                            
                        except Exception as e:
                            print('Error getting a message >>', e)
                            continue
                        
                        get_notification_type(message, gid)
                        
                    #try:
                    #except:
                    #    
                    #    pprint(vars(message))
    return False
                    

if __name__ == '__main__':
    
    p01 = '/home/philipe/.mozilla/firefox/twye9k7d.politics_01'
    p02 = '/home/philipe/.mozilla/firefox/oa1mosu5.politics_02'
    p03 = '/home/philipe/.mozilla/firefox/ytq5uk74.politics_03'
    health = '/home/philipe/.mozilla/firefox/18x22dze.health'
    load = True
    while load:
        #try:
        if True:
            reload(sys)  
            sys.setdefaultencoding('utf8')
            min_date = '2018-01-01'
            max_date = '2020-03-09'
            date_format = "%Y-%m-%d"
            till_date = datetime.datetime.strptime(min_date, date_format)
            load = webCrawler(load, p01, min_date, max_date)
        #except Exception as e:
        else:  
            error_time = str(datetime.datetime.now())
            error_msg  = str(e).strip()
            with open('errors_notifications.txt', 'a') as ferror:
                print("%s >> Error:\t%s"   %(error_time, error_msg))
                print("%s >> Error:\t%s"   %(error_time, error_msg), file=ferror)
            time.sleep(60) 


    





