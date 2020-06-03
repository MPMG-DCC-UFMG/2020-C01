from __future__ import print_function
from builtins import str
import time
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage, MMSMessage
import sys
from PIL import Image
from webwhatsapi.helper import safe_str
from webwhatsapi.objects.contact import Contact
from django.utils.encoding import smart_str, smart_unicode
import datetime

import os


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
            message.save_media(path, force_download=True)


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
            chat_id = smart_str(message.chat_id['_serialized']) 
            if hasattr(message, 'caption'):
                msg_caption = smart_str(message.caption)
            #    print('caption', smart_str(message.caption))
            #print('client_url', message.client_url)
            f=open(path+"chat_" +  chat_id+ ".chat.log","a+")
            f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=user,  timestamp=message.timestamp, id=chat_id, filename=videoName, caption=msg_caption))
            f.close()
            #f=open(path+"safechat_" + chat_id + ".chat.log","a+")
            #f.write("[ {sender} | {timestamp} ] sent media chat_{id}\{filename} with caption '{caption}'\n".format(sender=message.sender.get_safe_name(), timestamp=message.timestamp, id=chat_id, filename=videoName, caption=msg_caption))
            #f.close()
            #if not os.path.exists(path+'chat_{id}'.format(  id = chat_id )):
            #           os.makedirs(path+'chat_{id}'.format(   id= chat_id ))
            message.save_media(path, force_download=True)



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
            user = smart_str(message.sender.get_safe_name())
            chat_id = smart_str(message.chat_id['_serialized']) 
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
            message.save_media(path, force_download=True)



def get_date_from_message(message):
    t = str(message)
    index = t.find(' at ') + 4
    index2 = index + 10
    date = t[index:index2]
    date = date.replace('-','_')
    return date



def get_group_from_message(message):
    t = str(message)
    index = t.find('Group chat -') + 12
    index2 = index + 10
    group = t[index:].split(':')[0]
    
    return group



def get_text_from_message(message, file_t):
        
        if hasattr(message, 'safe_content') and  not isinstance(message, MediaMessage)  and not isinstance(message, MMSMessage):
                print(message, file=file_t)
                print(smart_str(message.content), file=file_t)
                print(smart_str(message.sender.id), file=file_t)
        else:
                print(smart_str(message) , message.filename, file=file_t)
                print(smart_str(message.sender.id), file=file_t)
                            





def webCrawler():
    #os.system('export PATH=$PATH:/path/t-/geckodriver')
    profile_path = "/home/philipemelo/.mozilla/firefox/cqpmmu3p.whatsapp_health"
    driver = WhatsAPIDriver(loadstyles=True, profile=profile_path)
    #driver_executable_path="./geckodriver"
    #driver = WhatsAPIDriver( driver_executable_path="./geckodriver")

    #driver.firstrun()
    print("Waiting for QR")
    driver.wait_for_login()
    print("Bot started")


    files = {}
    caminho = "./media/"
    path = './media/'
    
    today = datetime.date.today()
    # dd/mm/YY
    d1 = today.strftime("%Y_%m_%d")
    print(("d1 =", d1))
    today_date = d1


    
    file_name = ""
    while True:
        file_name = "AllMessages_" + today_date+ ".txt" 
        file_t = open(caminho + file_name, 'a', 0)
        time.sleep(10)
        #try:
        msg_list = driver.get_unread(include_me=False, include_notifications=False, use_unread_count=False)
        if len(msg_list) == 0: continue
        
        for i in msg_list:
            print(i)
            if len(i.messages)>0:
                print(i.chat, file=file_t)
                for j in i.messages:
                    date = get_date_from_message(j)
                    if today_date != date:  #update day
                            today_date = date
                            file_t.close()
                            file_name = "AllMessages_" + today_date+ ".txt" 
                            file_t = open(caminho + file_name, 'a', 0)
                  
                    get_text_from_message(j, file_t)
                    get_image_from_message(j)
                    get_video_from_message(j)
                    get_audio_from_message(j)


        #except Exception, err:
         #   sys.stderr.write('ERROR: %sn' % str(err))
          #  if 'Message: Tried to run command without establishing a connection' in str(err):
           #     webCrawler()
                 
    file_t.close()

if __name__ == '__main__':
    webCrawler()








