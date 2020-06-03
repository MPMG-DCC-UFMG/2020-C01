from __future__ import print_function
import time
import sys
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



def main():
    
    path = 'Messages/groupID/'
    all_files = [f for f in listdir(path) if isfile(join(path, f))]
    chatDict     = dict() 
    users = dict()
    groups = dict()
    total_msg = 0
    print('>>>>>Counting messages for all %d groups' %( len(all_files) ))
    
    for gid in all_files:
        with open(path+gid, 'r') as fgroup:
            for line in fgroup.readlines():
                #false_31646370267-1557949156@g.us_3A541E6DB1C9D9BF3518	31646370267-1557949156	31628974007@c.us	2019-11-02	13:40:01	text	False	<NoFile>	Nog 30 over
                total_msg += 1
                tokens    = line.strip().split('\t')
                messageID = tokens[0]
                groupID   = tokens[1]
                user      = tokens[2]
                date      = tokens[3]
                time      = tokens[4]
                msg_type  = tokens[5]
                is_media  = tokens[6]
                filename  = tokens[7]
                try :text = tokens[8]
                except: text = '<empty>'
                
                try: users[user] += 1
                except: users[user] = 1
                
                try: groups[groupID] += 1
                except: groups[groupID] = 1
                
        
                try:    A = chatDict[groupID]
                except: chatDict[groupID] = dict()
                
                
                try:    A = chatDict[groupID][date]
                except: 
                    chatDict[groupID][date] = dict()
                    chatDict[groupID][date]['text']    = 0
                    chatDict[groupID][date]['image']  = 0
                    chatDict[groupID][date]['audio']  = 0
                    chatDict[groupID][date]['video']  = 0
                    chatDict[groupID][date]['sticker'] = 0
                    chatDict[groupID][date]['ptt'] = 0
                    chatDict[groupID][date]['others']  = 0
                
                try:    chatDict[groupID][date][msg_type] +=1
                except: chatDict[groupID][date]['others'] += 1
                
                
       
    
    print('>>>>> Total of all messages: %d' %( total_msg ))
        
    with open('Messages/msgs-per-grp-per-day.txt', 'w') as fmg:
        for group in list(chatDict.keys()):
            for day in list(chatDict[group].keys()):
                total = chatDict[group][day]['text'] + chatDict[group][day]['image'] + chatDict[group][day]['audio'] + chatDict[group][day]['video'] + chatDict[group][day]['sticker'] + chatDict[group][day]['ptt'] + chatDict[group][day]['others']
                finalstring = "%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d" %(group, day, total, chatDict[group][day]['text'], chatDict[group][day]['image'], (chatDict[group][day]['audio']+chatDict[group][day]['ptt']), chatDict[group][day]['video'], chatDict[group][day]['sticker'])
                #print finalstring

                print(finalstring, file=fmg)
    
        
        
    with open('Messages/msgs-per-user.txt', 'w') as fu:
        for u in sorted(users, key=users.get, reverse=True):
                finalstring = "%s\t%d" %(u, users[u])
                #print finalstring
                print(finalstring, file=fu)
    
        
        
    with open('Messages/total_msgs.txt', 'w') as fm:
        for g in sorted(groups, key=groups.get, reverse=True):
                finalstring = "%s\t%d" %(g, groups[g])
                #print finalstring
                print(finalstring, file=fm)
    
 
    

if __name__ == '__main__':
    main()






