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


all_files = dict()
all_files['image'] = dict()
all_files['video'] = dict()
all_files['audio'] = dict()

def get_messages_by_group(driver):

    msg_list = driver.get_unread(include_me=False, include_notifications=False, use_unread_count=False)
    return msg_list


def get_image_from_message(message):
    path = 'images/'
    if message.type == 'image':
            try:
                all_files['image'] [message.filename] += 1
                
            except KeyError as e:
                all_files['image'] [message.filename] = 1
            
            imageName = 'image_%s_%d.%s' %(message.filename.split('.')[0], all_files['image'][message.filename], message.filename.split('.')[-1])
            message.filename = imageName
            print('-- Download Image Media: %s\t Size:%s\tmime:%s'   %( str(message.filename), str(message.size), str(message.mime) )   )
            msg_caption=''
            user = smart_str(message.sender.get_safe_name())
            user = user.replace(' ', '').strip()
            user = user.split('@')[0]
            user = '+'+user
            user =  hashlib.md5(user).hexdigest()

            
            chat_id = smart_str(message.chat_id['_serialized']) 
            if hasattr(message, 'caption'):
                msg_caption = smart_str(message.caption)
            #    print('caption', smart_str(message.caption))
            #print('client_url', message.client_url)
            f=open(path+"chat_" +  chat_id+ ".chat.log","a+")
            f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=user, timestamp=message.timestamp, id=chat_id, filename=imageName, caption=msg_caption))
            f.close()
            #f=open(path+"safechat_" + chat_id + ".chat.log","a+")
            #f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=message.sender.get_safe_name(), timestamp=message.timestamp, id=chat_id, filename=imageName, caption=msg_caption))
            #f.close()
            #if not os.path.exists(path+'chat_{id}'.format(  id = chat_id )):
            #           os.makedirs(path+'chat_{id}'.format(   id= chat_id ))
            #message.save_media(path, force_download=True)
            return 1
    return 0


def get_video_from_message(message):
    path = 'videos/'
    if message.type == 'video':
            try:
                all_files['video'] [message.filename] += 1
                
            except KeyError as e:
                all_files['video'] [message.filename] = 1
            
            videoName = 'video_%s_%d.%s' %(message.filename.split('.')[0], all_files['video'][message.filename], message.filename.split('.')[-1])
            message.filename = videoName
            print('-- Download Video Media: %s\t Size:%s\tmime:%s'   %( str(message.filename), str(message.size), str(message.mime) )   )
            msg_caption=''
            user = smart_str(message.sender.get_safe_name())
            user = user.replace(' ', '').strip()
            user = user.split('@')[0]
            user = '+'+user
            user =  hashlib.md5(user).hexdigest()
            chat_id = smart_str(message.chat_id['_serialized']) 
            if hasattr(message, 'caption'):
                msg_caption = smart_str(message.caption)
            #    print('caption', smart_str(message.caption))
            #print('client_url', message.client_url)
            f=open(path+"chat_" +  chat_id+ ".chat.log","a+")
            f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=user, timestamp=message.timestamp, id=chat_id, filename=videoName, caption=msg_caption))
            f.close()
            #f=open(path+"safechat_" + chat_id + ".chat.log","a+")
            #f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=message.sender.get_safe_name(), timestamp=message.timestamp, id=chat_id, filename=videoName, caption=msg_caption))
            #f.close()
            #if not os.path.exists(path+'chat_{id}'.format(  id = chat_id )):
            #           os.makedirs(path+'chat_{id}'.format(   id= chat_id ))
            #message.save_media(path, force_download=True)
            return 1
    return 0




def get_audio_from_message(message):
    path = 'audios/'
    if message.type == 'audio':
            try:
                all_files['audio'] [message.filename] += 1
                
            except KeyError as e:
                all_files['audio'] [message.filename] = 1
            
            audioName = 'audio_%s_%d.%s' %(message.filename.split('.')[0], all_files['audio'][message.filename], message.filename.split('.')[-1])
            message.filename = audioName
            print('-- Download Audio Media: %s\t Size:%s\tmime:%s'   %( str(message.filename), str(message.size), str(message.mime) )   )
            msg_caption=''
            chat_id = smart_str(message.chat_id['_serialized']) 
            user = smart_str(message.sender.get_safe_name())
            user = user.replace(' ', '').strip()
            user = user.split('@')[0]
            user = '+'+user
            user =  hashlib.md5(user).hexdigest()
            if hasattr(message, 'caption'):
                msg_caption = smart_str(message.caption)
            #    print('caption', smart_str(message.caption))
            #print('client_url', message.client_url)
            f=open(path+"chat_" +  chat_id+ ".chat.log","a+")
            f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=user, timestamp=message.timestamp, id=chat_id, filename=audioName, caption=msg_caption))
            f.close()
            #f=open(path+"safechat_" + chat_id + ".chat.log","a+")
            #f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=message.sender.get_safe_name(), timestamp=message.timestamp, id=chat_id, filename=audioName, caption=msg_caption))
            #f.close()
            #if not os.path.exists(path+'chat_{id}'.format(  id = chat_id )):
            #            os.makedirs(path+'chat_{id}'.format(   id= chat_id ))
            #message.save_media(path, force_download=True)
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
                print(smart_str(message), file=file_t)
                print(smart_str(msg_id), file=file_t)
                print(smart_str(chatID), file=file_t)
                print(message.filename, file=file_t)
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



def load_earlier_messages_till(drive, current_date):
    files = {}
    msg_path = "./Messages/groupID/"
    today_date = datetime.date.today().strftime("%Y_%m_%d")
    print(("d1 =", today_date))

    file_name = "AllMessages_" + today_date+ ".txt" 
    file_t = open(msg_path + file_name, 'a', 0)
    test_date = '2019-08-24 00:00:00'
    time_period = convert_data_to_timestamp(test_date)
    current_date = datetime.datetime.fromtimestamp(time_period)
    print('Get All Chats Groups')
    chats = driver.get_all_chats()
    for chat in chats:
        
        print('>>>>>Loading messages from', chat)
        chat.load_earlier_messages_till(current_date)
        messages = chat.get_messages()
        for j in messages:
            #print i
            #if len(i.messages)>0:
            #    print >> file_t, i.chat
            #    for j in i.messages:
                    try: 
                        date = get_date_from_message(j)
                    except: 
                        continue
                    if today_date != date:  #update day
                            today_date = date
                            file_t.close()
                            file_name = "AllMessages_" + today_date+ ".txt" 
                            file_t = open(msg_path + file_name, 'a', 0)
                  
                    get_text_from_message(j, file_t, chat, j.id)
                    get_image_from_message(j)
                    get_video_from_message(j)
                    get_audio_from_message(j)


        #except Exception, err:
         #   sys.stderr.write('ERROR: %sn' % str(err))
          #  if 'Message: Tried to run command without establishing a connection' in str(err):
           #     webCrawler()
                 
    file_t.close()

def get_load_messages(path = 'Messages/groupID/'):
    messagesIDs = dict()
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for f in allfiles:
        ID = f.split('.')[0].split('@')[0]
        messagesIDs[ID] = list()
        with open(path+f, 'r') as fin:
            for line in fin:
                messagesIDs[ID].append(line.strip().split('\t')[0])
    return messagesIDs
    
    
def get_groups_metadata(driver):
    titles = dict()
    with open('/home/philmelo/philipe/whatsapp/titles.txt', 'r') as ft:
        for line in ft.readlines():
            try:
                tks   = line.strip().split('\t')
                link  = tks[0]
                week  = tks[1]
                title = smart_unicode(tks[2].strip())
                if len(title) <= 2: continue
                titles[title] = dict()
                titles[title]['title'] = title
                titles[title]['link']  = link
                titles[title]['week']  = week
            except : continue
           
    chats = driver.get_all_chats()
    with open('all_chats_id.txt', 'w') as fchat:
        for chat in chats:
            #try:
                if not chat._js_obj['isGroup']: continue
                _id = chat.id
                creator = _id.split('-')[0]
                creator = hashlib.md5(creator).hexdigest()
                timestamp = _id.split('-')[-1].split('@')[0]
                date = convert_data_from_timestamp(float(timestamp))
                try: name = smart_unicode(chat.name.strip().replace('\t',' '))
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
        notification_file = 'Messages/notifications/' + gid + '.txt'
        noti_file   = 'Messages/all_notifications.txt'
        banned_file = 'Messages/banned.txt'
        finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(gid, msgtype, subtype, timestamp, date, name, sender_user, from_user )
        with open(notification_file, 'a') as fnot:         
            with open(noti_file, 'a') as fn:         
                print(finalstring)
                print(finalstring, file=fnot)
                print(finalstring, file=fn)
        
        if subtype == 'remove' and from_user in our_phones:
            with open(banned_file, 'a') as fb:
                print(finalstring, file=fb)


def save_message(message, msg_id_path, chatID, msg_id, file_t):
        
        #pprint(vars(message))
        #print 'TYPE', type(message)
        #print 'ATT', dir(message)
        #print 'VARS', (vars(object))
        if not message.sender: return
        sender = message.sender.id
        sender = sender.replace(' ', '').strip()
        sender = sender.split('@')[0]
        sender = '+'+sender
        sender =  hashlib.md5(sender).hexdigest()

        
        mid = smart_unicode(msg_id)
        gid = smart_unicode(chatID)
        mid_filename = msg_id_path+gid+'.txt'
        name = get_group_from_message(message)

        try : 
            content = message.content
            content = smart_str(content)
            content = content.replace('\t', ' ')
            content = content.replace('\r', '')
            content = smart_unicode(content.replace('\n', ' '))
        except: content = '<NoContent>'
        
        t = str(message)
        index = t.find(' at ') + 4
        index2 = index + 19
        date = str(t[index:index2])
        date = smart_unicode(date.replace(' ','\t').strip())
        
        filename = '<NoFile>'
        mediatype = 'text'
        MediaMessage = False
        if isinstance(message,  MESSAGE.MediaMessage) or isinstance(message,  MESSAGE.MMSMessage):
            MediaMessage = True
            mediatype = smart_str(message.type)
            try: 
                filename = smart_unicode(message.filename)
                content = '<'+filename+'>'
            except: filename = '<NoFile>'
    
    
        with open(mid_filename, 'a') as fmid:
            messageLine = '%s\t%s\t%s\t%s\t%s\t%r\t%s\t%s' %(mid, gid, smart_str(sender), smart_str(date), mediatype, MediaMessage, smart_str(filename), smart_str(content))
            print(messageLine, file=fmid)
            print(messageLine, file=file_t)
            print(messageLine)
            

def webCrawler(load, min_date, max_date, profile_path):
    
    #os.system('export PATH=$PATH:/home/philmelo/philipe/geckodriver/64')
    driver_executable_path="/home/philmelo/philipe/geckodriver/64/geckodriver"
    driver = WhatsAPIDriver(loadstyles=True, profile=profile_path, executable_path=driver_executable_path)
    #driver = WhatsAPIDriver()
    #driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=os.environ["SELENIUM"])
    #driver_executable_path="./geckodriver"
    #driver = WhatsAPIDriver( driver_executable_path="./geckodriver")

    #driver.firstrun()
    print("Waiting for QR")
    driver.wait_for_login()
    print("Bot started")
    files = {}
    today_date = datetime.date.today().strftime("%Y_%m_%d")
    today_date = 'test'
    
    #print '>>>>>>>>>>> Getting Groups Metadata'
    #get_groups_metadata(driver)
    msg_id_path  = 'Messages/groupID/'
    messagesID   = get_load_messages(msg_id_path)
    all_messages = list()
    file_name = "AllMessages_" + today_date+ ".txt"  
    file_t = open(file_name, 'a', 0) 
    
    reverse = True
    reverse_messages = False
    if load:
        print('>>>>>>>>>>>>Getting Groups Messages...', end=' ')
        chats = driver.get_all_chats()
        count = 0
        #if reverse: chats = reversed(chats)
        print(' DONE! %d chats loaded!' %(len(chats)))
        
        all_chats = list(chats)
        random.shuffle(all_chats) 
        for chat in (all_chats):
            #pprint(vars(chat)) 
            #if count >= 2: break
            if not chat._js_obj['isGroup']: continue
            gid = chat.id
            s_name = smart_str(chat.name)
            members  = chat._js_obj['groupMetadata']['participants']
            creator   = gid.split('-')[0]
            timestamp = gid.split('-')[-1].split('@')[0]
            date = convert_data_from_timestamp(float(timestamp))
            try : name = smart_unicode(chat.name.strip().replace('\t',' '))
            except : name = 'NoName'
            
            chat_print = "<Group chat - {name}: {id}, {participants} participants>".format( name=s_name, id=gid,  participants=len(members) )
            print('>>>>>Loading messages ID from', chat_print)
            #messages = chat.load_all_earlier_messages()
            messages = chat.load_earlier_messages_till(min_date)
            #messages = chat.get_messages()
            #messages = driver.get_all_messages_in_chat(chat)
            messages = driver.get_all_message_ids_in_chat(chat, include_notifications=True)
            
            if reverse_messages: messages = reversed(messages)
            local_messages = list()
            print('>>>>>Total messages %d' %( len(messages) ))
            with open('all_msg_ids.txt', 'a') as fo:
                for mid in messages : 
                    local_messages.append([mid, gid])
                    all_messages.append([mid, gid])
                    print('%s\t%s' %(mid, gid), file=fo)
            count +=1
            
            for msg in local_messages:
                count +=1
                gid = msg[1].split('@')[0]
                mid = msg[0]
                try: msgids = messagesID[gid]
                except KeyError as e: messagesID[gid] = list()
                
                if mid.strip() in messagesID[gid]:
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
                #print smart_str(str(j))
                
                #get_notification_type(message, gid)
                try:    date = get_date_from_message(j)
                except: continue
                
                if date > max_date: break
                if today_date != date:  #update day
                        today_date = date
                        file_t.close()
                        file_name = "Messages/text/AllMessages_" + today_date+ ".txt" 
                        file_t = open(file_name, 'a', 0)
                #text = get_text_from_message(j, file_t, gid, mid)        
                save_message(j, msg_id_path, gid, mid, file_t)
                
        
       
            
    else: 
        with open('all_msg_ids.txt', 'r') as fi:
            for line in fi.readlines():
                m = line.strip().split('\t')
                all_messages.append([m[0], m[1]])

    

if __name__ == '__main__':

    while True:
        #if True:
        try:
            load = True
            reload(sys)  
            sys.setdefaultencoding('utf8')
            min_date = '2019-12-13'
            max_date = '2019-12-26'
            date_format = "%Y-%m-%d"
            till_date = datetime.datetime.strptime(min_date, date_format)
            if len(sys.argv) > 1:
                profile_path =  sys.argv[1]
            else:
                #profile_path = "/home/philmelo/.mozilla/firefox/75uzhgbs.MPI_Anna"
                profile_path = '/home/philipemelo/.mozilla/firefox/cqpmmu3p.whatsapp_health'
            webCrawler(load, till_date, max_date, profile_path)
        #else:
        except Exception as e:
            error_time = str(datetime.datetime.now())
            error_msg  = str(e).strip()
            with open('errors.txt', 'a') as ferror:
                print("%s >> Error:\t%s"   %(error_time, error_msg))
                print("%s >> Error:\t%s"   %(error_time, error_msg), file=ferror)
            time.sleep(60) 








