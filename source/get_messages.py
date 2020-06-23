from __future__ import print_function

from builtins import str
from os import listdir
from os.path import isfile, join
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import NotificationMessage
from webwhatsapi.objects import message as MESSAGE

import time
import random
import datetime
import os
import pathlib
import argparse
import json
import phonenumbers


def smart_str(x):
    if isinstance(x, int) or isinstance(x, float):
        return str(x, "utf-8")
    return x


def convert_data_from_timestamp(time_message):
    time_obj = datetime.datetime.fromtimestamp(time_message)
    return time_obj


class WhatsappCollector():

    def __init__(self, args):
        args_dict = vars(args)

        if args.json:
            with open(args.json) as json_file:
                json_args = json.load(json_file)
                args_dict.update(json_args)

        self.collection_mode = args_dict["collection_mode"]
        self.start_date = args_dict["start_date"]
        self.end_date = args_dict["end_date"]
        self.group_blacklist = args_dict["group_blacklist"]
        self.user_blacklist = args_dict["user_blacklist"]
        self.collect_messages = args_dict["collect_messages"]
        self.collect_audios = args_dict["collect_audios"]
        self.collect_videos = args_dict["collect_videos"]
        self.collect_images = args_dict["collect_images"]
        self.process_audio_hashes = args_dict["process_audio_hashes"]
        self.process_image_hashes = args_dict["process_image_hashes"]
        self.process_video_hashes = args_dict["process_video_hashes"]

    def _process_content(self, string):
        string = string.strip()
        string = string.replace('\r', '')
        string = string.replace('\n', ' ')
        string = string.replace('\t', ' ')
        string = smart_str(string)

        return string

    def _get_filename(self, message, filename):
        mediaID = message.id.split('.')[-1]
        filename = '%s_%s_%s.%s' % (message.type, filename.split('.')[0],
                                    mediaID, filename.split('.')[-1])
        return filename

    def _get_image_from_message(self, message):
        path = '/data/image/'
        if message.type == 'image':
            filename = self._get_filename(message, message.filename)
            message.filename = filename
            if not os.path.isfile(path+filename):
                message.save_media(path, force_download=True)

    def _get_video_from_message(self, message):
        path = '/data/video/'
        if message.type == 'video':
            filename = self._get_filename(message, message.filename)
            message.filename = filename
            if not os.path.isfile(path+filename):
                message.save_media(path, force_download=True)

    def _get_audio_from_message(self, message):
        path = '/data/audio/'
        if message.type == 'audio':
            filename = self._get_filename(message, message.filename)
            message.filename = filename
            if not os.path.isfile(path+filename):
                message.save_media(path, force_download=True)

    def _get_date_from_message(self, message):
        t = str(message)
        index = t.find(' at ') + 4
        index2 = index + 10
        date = t[index:index2]
        return date

    def _get_group_from_message(self, message):
        t = str(message)
        index = t.find('Group chat -') + 12
        group = t[index:].split(':')[0]
        return group

    def _get_load_messages(self, path='/data/groupID/'):
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
                    if date >= maxDate:
                        maxDate = date
                    messagesIDs[ID]['messages'].add(tokens[0])
            messagesIDs[ID]['date'] = date
        return messagesIDs

    def _get_notification_type(self, message, gid):
        if isinstance(message, NotificationMessage):
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
                                'description': "Changed the group description."
                                " Click to view."
                            }
            }
            msgtype = message.type
            msgtype = message._js_obj['type']
            subtype = message._js_obj['subtype']
            timestamp = message._js_obj['timestamp']
            name = smart_str(message._js_obj['chat']['contact']['name'])
            name = name.replace('\t', ' ')
            name = name.replace('\n', ' ')
            name = name.replace('\r', '')

            date = datetime.fromtimestamp(int(timestamp)).strftime(
                '%Y-%m-%d %H:%M:%S')

            try:
                sender_user = message._js_obj['sender']['id']['user']
            except KeyError:
                sender_user = 'No_sender'

            try:
                from_user = message._js_obj['from']['user']
            except KeyError:
                from_user = 'No_user'

            try:
                alert = readable[message.type][message.subtype]
            except KeyError:
                alert = 'Other'

            our_phones = ['491705423146', '491705933848']
            notification_file = '/data/notifications/' + gid + '.txt'
            noti_file = '/data/all_notifications.txt'
            banned_file = '/data/banned.txt'
            finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % \
                (gid, msgtype, subtype,
                    timestamp, date, name, sender_user, from_user)

            with open(notification_file, 'a') as fnot:
                with open(noti_file, 'a') as fn:
                    print(finalstring)
                    print(finalstring, file=fnot)
                    print(finalstring, file=fn)

            if subtype == 'remove' and from_user in our_phones:
                with open(banned_file, 'a') as fb:
                    print(finalstring, file=fb)

    def _save_message(self, message, group_name, chatID, msg_id, file_t,
                      msg_id_path='/data/groupID/'):
        if not message.sender:
            return

        sender = message.sender.id
        sender = sender.replace(' ', '').strip()
        sender = sender.split('@')[0]
        sender = ('+'+sender)

        try:
            phone = phonenumbers.parse(sender)
        except: 
            phone = phonenumbers.parse('+'+sender)
        country = phone.country_code

        mid = smart_str(msg_id)
        gid = smart_str(chatID)
        mid_filename = msg_id_path+gid+'.txt'
        name = self._get_group_from_message(message)

        try:
            content = message.content
            content = smart_str(content)
            content = smart_str(content.replace('\n', ' '))
        except:
            content = '<NoContent>'

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
                filename = self._get_filename(message, message.filename)
                content = '<'+filename+'>'
            except:
                filename = '<NoFile>'
            if hasattr(message, 'caption'):
                content = smart_str(message.caption)

        with open(mid_filename, 'a') as fmid:
            messageLine = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%r\t%s\t%s' % \
                (mid, gid, group_name, country, smart_str(sender),
                    smart_str(date), mediatype, MediaMessage,
                    smart_str(filename), self._process_content(content))
            print(messageLine, file=fmid)
            print(messageLine, file=file_t)
            print(messageLine)

    def run(self, profile_path="/data/firefox_cache"):
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
        driver = WhatsAPIDriver(loadstyles=True, profile=profile_path,
                                client="remote",
                                command_executor=os.environ["SELENIUM"])

        pathlib.Path("/data/text").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/image").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/audio").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/video").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/groupID").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/notifications").mkdir(parents=True, exist_ok=True)

        min_date = self.start_date
        max_date = self.end_date

        if (not max_date or not min_date):
            raise Exception("Can't start collection without a start and end"
                            " date.")

        try:
            print("Waiting for QR")
            driver.wait_for_login()
            print("Saving session")
            driver.save_firefox_profile(remove_old=False)
            print("Bot started")

            messagesID = self._get_load_messages()

            today_date = datetime.date.today().strftime("%Y_%m_%d")
            today_date = 'test'
            date_format = "%Y-%m-%d"

            all_messages = list()
            file_name = "/data/AllMessages_" + today_date + ".txt"
            file_t = open(file_name, 'a')
            start_date = min_date

            print('>>>>>>>>>>>>Getting Groups Messages...', end=' ')
            chats = driver.get_all_chats()
            count = 0
            all_chats = list(chats)

            print(' DONE! %d chats loaded!' % (len(all_chats)))
            random.shuffle(all_chats)

            for chat in (all_chats):
                gid = chat.id
                gid = gid.split('@')[0]

                if not chat._js_obj['isGroup'] or gid in self.group_blacklist:
                    continue

                # PRINT CHAT INFORMATION
                s_name = self._process_content(chat.name)
                members = chat._js_obj['groupMetadata']['participants']
                timestamp = gid.split('-')[-1]
                date = convert_data_from_timestamp(float(timestamp))
                str_date = date.strftime('%Y-%m-%d %H:%M:%S')

                chat_print = "<Group chat - {name}: {id}, {participants} " \
                    "participants - at {time}!!>".format(
                        name=s_name, id=gid, participants=len(members),
                        time=str_date)
                print('>>>>>Loading messages from', chat_print)

                if gid not in messagesID:
                    messagesID[gid] = dict()
                    messagesID[gid]['messages'] = set()
                    messagesID[gid]['date'] = '2000-01-01'

                # PROCESS PREVIOUS LOADED MESSAGES ID AND LAST DATE
                if messagesID[gid]['date'] > max_date:
                    continue
                if messagesID[gid]['date'] > min_date:
                    start_date = messagesID[gid]['date']
                    till_date = datetime.datetime.strptime(start_date,
                                                           date_format)
                else:
                    start_date = min_date
                    till_date = datetime.datetime.strptime(start_date,
                                                           date_format)

                # LOAD MESSAGES FROM WHATSAPP SINCE MIN_DATE
                messages = chat.load_earlier_messages_till(till_date)
                messages = driver.get_all_message_ids_in_chat(
                    chat, include_notifications=True)

                local_messages = list()
                print('>>>>>Total messages %d' % (len(messages)))
                with open('/data/all_msg_ids.txt', 'a') as fo:
                    for mid in messages:
                        local_messages.append([mid, gid])
                        all_messages.append([mid, gid])
                        print('%s\t%s' % (mid, gid), file=fo)
                count += 1

                for msg in local_messages:
                    count += 1
                    gid = msg[1].split('@')[0]
                    mid = msg[0]

                    if mid.strip() in messagesID[gid]['messages']:
                        if self.verbose:
                            print('Message: %d >>> %s from %s was CHECKED' %
                                  (count, mid, gid))
                        continue
                    else:
                        try:
                            j = driver.get_message_by_id(mid)
                        except Exception as e:
                            print('Error getting a message >>', e)
                            continue
                        if not j:
                            continue

                    try:
                        date = self._get_date_from_message(j)
                    except:
                        continue

                    if date > max_date:
                        break
                    if date < start_date:
                        continue
                    # Update day
                    if today_date != date:
                        today_date = date
                        file_t.close()
                        file_name = "/data/text/AllMessages_" + today_date + \
                            ".txt"
                        file_t = open(file_name, 'a')

                    if self.collect_messages:
                        self._save_message(j, s_name, gid, mid, file_t)

                    if self.collect_images:
                        try:
                            self._get_image_from_message(j)
                        except Exception as ei:
                            print('!!!!Error getting image!!!! ', ei)

                    if self.collect_videos:
                        try:
                            self._get_video_from_message(j)
                        except Exception as ev:
                            print('!!!!Error getting video!!!! ', ev)

                    if self.collect_audios:
                        try:
                            self._get_audio_from_message(j)
                        except Exception as ea:
                            print('!!!!Error getting audio!!!! ', ea)

            driver.close()
        except Exception as e:
            print(e)
            driver.close()
            raise Exception(e)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--collection_mode", type=str,
                        help="Modo de coleção a ser utilizado (\'period\'"
                        " ou \'unread\').",
                        default='unread')

    parser.add_argument("-s", "--start_date", type=str,
                        help="Data de início do período de coleta (Modo"
                        " \'period\').")

    parser.add_argument("-e", "--end_date", type=str,
                        help="Data de término do período de coleta (Modo"
                        " \'period\').")

    parser.add_argument("--collect_messages", type=bool,
                        help="Se mensagens de texto devem ser coletadas"
                        " durante a execução.", default=True)

    parser.add_argument("--collect_audios", type=bool,
                        help="Se audios devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--collect_videos", type=bool,
                        help="Se videos devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--collect_images", type=bool,
                        help="Se imagens devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--process_audio_hashes", type=bool,
                        help="Se hashes de audios devem ser calculados durante"
                        " a execução.", default=False)

    parser.add_argument("--process_image_hashes", type=bool,
                        help="Se hashes de imagens devem ser calculados"
                        " durante a execução.", default=False)

    parser.add_argument("--process_video_hashes", type=bool,
                        help="Se hashes de videos devem ser calculados durante"
                        " a execução.", default=False)

    parser.add_argument("--group_blacklist", nargs="+",
                        help="Lista de grupos que devem ser excluídos da"
                        " coleta", default=[])

    parser.add_argument("--user_blacklist", nargs="+",
                        help="Lista de usuários que devem ser excluídos da"
                        " coleta", default=[])

    parser.add_argument("-j", "--json", type=str,
                        help="Caminho para um arquivo json de configuração de "
                        "execução. Individualmente, as opções presentes no "
                        "arquivo sobescreveram os argumentos de linha de "
                        "comando, caso eles sejam fornecidos.")

    args = parser.parse_args()

    print(args)

    try:
        collector = WhatsappCollector(args)
        collector.run()
    except Exception as e:
        error_time = str(datetime.datetime.now())
        error_msg = str(e).strip()
        with open('/data/log.txt', 'w') as ferror:
            print("%s >> Error:\t%s" % (error_time, error_msg))
            print("%s >> Error:\t%s" % (error_time, error_msg), file=ferror)
        time.sleep(1500)


if __name__ == '__main__':
    main()
