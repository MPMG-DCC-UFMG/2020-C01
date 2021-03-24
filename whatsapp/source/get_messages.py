from __future__ import print_function

from builtins import str
from os import listdir
from os.path import isfile, join
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import NotificationMessage
from webwhatsapi.objects import message as MESSAGE

from kafka_functions import KafkaManager
from kafka import KafkaConsumer
from kafka import KafkaProducer

import time
import random
import datetime
import os
import pathlib
import argparse
import json
import phonenumbers
import hash_functions


def smart_str(x):
    if isinstance(x, int) or isinstance(x, float):
        return str(x, "utf-8")
    return x


def get_messages_by_group(driver):
    msg_list = driver.get_unread(include_me=False, include_notifications=True, use_unread_count=False)
    return msg_list


def convert_data_from_timestamp(time_message):
    time_obj = datetime.datetime.fromtimestamp(time_message)
    return time_obj


class WhatsappCollector():
    """
    Classe que encapsula o coletor de grupos do Whatsapp. Possui
    o método principal que realiza a leitura da entrada e faz a
    coleta das mensagens, mídias e notificações.

    Atributos
    -----------
    collection_mode : str
            Modo de coleção a ser utilizado ("period" ou "unread" ou 
            "continuous").
    start_date : str
            Data de início do período de coleta (Modo "period").
    end_date : str
            Data de término do período de coleta (Modo "period").
    group_blacklist : list
            Lista de ids de grupos que devem ser excluídos da coleta.
    user_blacklist : list
            Lista de ids de usuários que devem ser excluídos da coleta.
    collect_messages : bool
            Se mensagens de texto devem ser coletadas durante a execução.
    collect_audios : bool
            Se áudios devem ser coletadas durante a execução.
    collect_videos : bool
            Se vídeos devem ser coletadas durante a execução.
    collect_images : bool
            Se imagens devem ser coletadas durante a execução.
    collect_notifications : bool
            Se notificações devem ser coletadas durante a execução.
    process_audio_hashes : bool
            Se hashes de áudios devem ser calculados durante a execução.
    process_image_hashes : bool
            Se hashes de imagens devem ser calculados durante a execução.
    process_video_hashes : bool
            Se hashes de vídeos devem ser calculados durante a execução.


    Métodos
    -----------
    Faz a coleta das mensagens de grupos de Whatsapp de acordo
    com os parâmetros fornecidos na criação do objeto de coleta.

        Parâmetros
        ------------
            profile_path : str
                Caminho para um profile alternativo do navegador
                utilizado na coleta.

    """
    def __init__(self, args):
        """
        Inicializa o objeto

        Parâmetros
        ------------
            args : argparse.Namespace()
                Objeto com atributos que contém os argumentos de linha de
                comando fornecidos.
        """
        args_dict = vars(args)

        if args.json:
            with open(args.json) as json_file:
                json_args = json.load(json_file)
                args_dict.update(json_args)
        elif args.json_string:
            json_args = json.loads(args.json_string)
            args_dict.update(json_args)

        if (args_dict["collection_mode"] not in
                ['continuous', 'period', 'unread']):
            print('Collection mode invalid <%s>!! Using <continuous> instead' %
                  (args_dict["collection_mode"]))
            args_dict["collection_mode"] = 'continuous'
        if args_dict["write_mode"] not in ['both', 'day', 'group', 'kafka']:
            print('Save mode invalid <%s>!! Using <kafka> instead' % (
                args_dict["write_mode"]))
            args_dict["write_mode"] = 'kafka'
        
        
        
        self.collection_mode       = args_dict["collection_mode"]
        self.start_date            = args_dict["start_date"]
        self.end_date              = args_dict["end_date"]
        self.write_mode            = args_dict["write_mode"]
        self.group_blacklist       = args_dict["group_blacklist"]
        self.user_blacklist        = args_dict["user_blacklist"]
        self.group_whitelist       = args_dict["group_whitelist"]
        self.user_whitelist        = args_dict["user_whitelist"]
        self.collect_messages      = args_dict["collect_messages"]
        self.collect_audios        = args_dict["collect_audios"]
        self.collect_videos        = args_dict["collect_videos"]
        self.collect_images        = args_dict["collect_images"]
        self.collect_notifications = args_dict["collect_notifications"]
        self.process_audio_hashes  = args_dict["process_audio_hashes"]
        self.process_image_hashes  = args_dict["process_image_hashes"]
        self.process_video_hashes  = args_dict["process_video_hashes"]
        self.profile               = args_dict["profile"]
        self.data_path             = '/data/'
        self.datalake              = args_dict["datalake"]
        self.bootstrap_servers     = args_dict["bootstrap_servers"]

        
        if self.write_mode == 'kafka' or self.write_mode == 'both':
            self.save_file             = False
            self.save_kafka            = True
            self.kafka                 = KafkaManager()
            if len(args_dict["bootstrap_servers"]) > 1:
                self.bootstrap_servers     = args_dict["bootstrap_servers"]
                self.kafka.update_servers(self.bootstrap_servers )
            if len(args_dict["bootstrap_servers"]) == 1:
                self.bootstrap_servers     = args_dict["bootstrap_servers"][0].split(',')
                self.kafka.update_servers(self.bootstrap_servers )
            self.producer              = self.kafka.connect_kafka_producer()
        else:
            self.save_file             = True
            self.save_kafka            = False
        
        if self.write_mode == 'both':
            self.save_file             = True
            self.save_kafka            = True
         
        
    def _process_string(self, string):
        """
        Processa strings que irão pra saída do coletor, removendo quebras
        de linha, tabulações e espaços extras.

        Parâmetros
        ------------
            string : str
                String a ser processada.
        """
        string = string.strip()
        string = string.replace('\r', '')
        string = string.replace('\n', ' ')
        string = string.replace('\t', ' ')
        string = smart_str(string)

        return string

    def _generate_unique_filename(self, message, filename):
        """
        Gera um novo nome único para o arquivo de mídia contido na mensagem.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto de messagem que contem uma mídia.
            filename : str
                Nome original do arquivo.
        """
        date = self._get_date_from_message(message).split(' ')[0]
        mediaID = message.id.split('.')[-1]
        filename = '%s/%s_%s_%s.%s' % (date, message.type, filename.split('.')[0],
                                    mediaID, filename.split('.')[-1])
        return filename

    def _get_image_from_message(self, message, path='/data/image/'):
        """
        Baixa a imagem contida na mensagem coletada, caso ela exista.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto de messagem que contem uma imagem que pode ser baixada.
            path : str
                Caminho para a pasta onde o arquivo será salvo.
        """
        if message.type == 'image':
            date = self._get_date_from_message(message).split(' ')[0]
            
            filename = self._generate_unique_filename(
                message, message.filename)
            message.filename = filename
            
            out_folder = join(path, filename.split('/')[0])
            pathlib.Path(out_folder).mkdir(parents=True, exist_ok=True)
            if not os.path.isfile(path+filename):
                message.save_media(path, force_download=True)

    def _get_video_from_message(self, message, path='/data/video/'):
        """
        Baixa o vídeo contido na mensagem coletada, caso ele exista.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto de messagem que contem um vídeo que pode ser baixado.
            path : str
                Caminho para a pasta onde o arquivo será salvo.
        """
        if message.type == 'video':
            date = self._get_date_from_message(message).split(' ')[0]
            
            filename = self._generate_unique_filename(
                message, message.filename)
            message.filename = filename
            
            out_folder = join(path, filename.split('/')[0])
            pathlib.Path(out_folder).mkdir(parents=True, exist_ok=True)
            if not os.path.isfile(path+filename):
                message.save_media(path, force_download=True)

    def _get_audio_from_message(self, message, path='/data/audio/'):
        """
        Baixa o áudio contido na mensagem coletada, caso ele exista.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto de messagem que contem um áudio que pode ser baixado.
            path : str
                Caminho para a pasta onde o arquivo será salvo.
        """
        if message.type == 'audio' or message.type == 'ptt':
            date = self._get_date_from_message(message).split(' ')[0]
            
            filename = self._generate_unique_filename(
                message, message.filename)
            message.filename = filename
            
            out_folder = join(path, filename.split('/')[0])
            pathlib.Path(out_folder).mkdir(parents=True, exist_ok=True)
            if not os.path.isfile(path+filename):
                message.save_media(path, force_download=True)

    def _get_date_from_message(self, message):
        """
        Retorna a data em que a mensagem foi enviada.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto de mensagem.
        """
        t = str(message)
        index = t.find(' at ') + 4
        index2 = index + 10
        date = t[index:index2]
        return date

    def _get_group_from_message(self, message):
        """
        Retorna o nome do grupo em que a mensagem foi enviada.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto de mensagem.
        """
        t = str(message)
        index = t.find('Group chat -') + 12
        group = t[index:].split(':')[0]
        return group

    def _get_load_notifications(self, path='/data/notificacoes/'):
        """
        Carrega e retorna um dicionário contendo os ids e datas das
        notificações já coletadas.

        Parâmetros
        ------------
            path : str
                Caminho para pasta contendo arquivos de notificações.
        """
        messagesIDs = dict()
        allfiles = [f for f in listdir(path) if isfile(join(path, f))]
        for f in allfiles:
            ID = f.split('.')[0].split('@')[0]
            messagesIDs[ID] = set()
            with open(path+f, 'r') as fin:
                for line in fin:
                    data = json.loads(line.strip())
                    mid = data['identificador']
                    messagesIDs[ID].add(mid)

        return messagesIDs

    def _get_load_messages(self, path='/data/mids/'):
        """
        Carrega e retorna um dicionário contendo os ids e datas das
        mensagens já coletadas.

        Parâmetros
        ------------
            path : str
                Caminho para pasta contendo arquivos de mensagens.
        """
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
                    if date >= maxDate:
                        maxDate = date
                    messagesIDs[ID]['messages'].add(tokens[0])
            messagesIDs[ID]['date'] = date
        return messagesIDs

    def _is_notification(self, messageID):
        """
        Verifica se uma mensagem é do tipo notificação a partir do seu id.

        Parâmetros
        ------------
            messageID : str
                Id de uma mensagem coletada.
        """
        if messageID.find('true') < 0:
            return False
        else:
            return True
    
    
    def check_user(self, message):
        check_user_w = False
        check_user_b = False
        if len(self.user_whitelist) > 0: check_user_w = True
        if len(self.user_blacklist) > 0: check_user_b = True
        
        sender = ''
        id = message.sender.id
        sender = message.sender.id
        sender = sender.replace(' ', '').strip()
        sender = sender.split('@')[0]
        sender = ('+'+sender)

        if check_user_w and (id not in self.user_whitelist):
            if check_user_w and (sender not in self.user_whitelist):
                return False
                
        if check_group_b and (id in self.user_blacklist or sender in self.user_blacklist):
            print('User', sender, 'in user blacklist!!! Next message')
            return False
                    
        
        return True
        
    def _save_notification_(self, message, gid, path='/data/notificacoes/'):
        """
        Escreve em formato json a notificação contida na mensagem no arquivo
        referente ao grupo em que ela foi enviada. Caso o arquivo do grupo
        ainda não exista, ele será criado.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto da mensagem coletada.
            gid : str
                Id do grupo em que a mensagem foi enviada.
            path : str
                Caminho da pasta em que os arquivos de notificações serão
                escritos.
        """
        if(isinstance(message, NotificationMessage)):
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
            name = self._process_string(name)
            date = datetime.datetime.fromtimestamp(int(timestamp)).strftime(
                '%Y-%m-%d %H:%M:%S')

            try:
                sender_user = message._js_obj['sender']['id']['user']
            except Exception:
                sender_user = 'No_sender'

            try:
                from_user = message._js_obj['from']['user']
            except Exception:
                from_user = 'No_user'

            try:
                alert = readable[message.type][message.subtype]
            except KeyError as e:
                alert = 'Other'

            notification = dict()

            notification['identificador'] = str(message.id)
            notification['mensagem_id'] = str(message.id)
            notification['grupo_id'] = gid
            notification['acao'] = msgtype
            notification['notification_type'] = subtype
            notification['timestamp'] = timestamp
            notification['criado_em'] = date
            notification['enviado_por'] = sender_user
            notification['contact'] = name
            notification['received_by'] = from_user

            n_date = notification['criado_em'].split(' ')[0]
            all_notification_filename = self.data_path+'all_notificacoes/all_notificacoes_%s.json' % \
                (n_date)

            if message._js_obj['recipients']:
                for item in message._js_obj['recipients']:
                    try:
                        recipient_user = item['user']
                    except Exception:
                        recipient_user = 'No_user'
                    notification['recipient'] = recipient_user
                    finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % \
                        (str(message.id), gid, msgtype, subtype, timestamp,
                         date, name, sender_user, recipient_user, from_user)
                    print(finalstring)
                                                
                    if self.save_kafka:
                        topic = self.kafka.get_topic('whatsapp' , 'notificacao')
                        json_dump_object = json.dumps(notification)
                        self.kafka.publish_kafka_message(self.producer, topic, 'raw', json_dump_object)
                    
                    if self.save_file:
                        filename = '%snotificacoes_%s.json' % (path, gid)
                        with open(filename, 'a') as json_file:
                            json.dump(notification, json_file)
                            print('', file=json_file)
                        with open(all_notification_filename, 'a') as json_file:
                            json.dump(notification, json_file)
                            print('', file=json_file)

            else:
                try:
                    recipient_user = message._js_obj['recipients'][0]['user']
                except Exception:
                    recipient_user = 'No_user'
                notification['recipient'] = recipient_user
                finalstring = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % \
                    (str(message.id), gid, msgtype, subtype, timestamp, date,
                     name, sender_user, recipient_user, from_user)
                print(finalstring)
                                            
                if self.save_kafka:
                    topic = self.kafka.get_topic('whatsapp' , 'notificacao')
                    json_dump_object = json.dumps(notification)
                    self.kafka.publish_kafka_message(self.producer, topic, 'raw', json_dump_object)
                
                if True:
                    filename = '%snotificacoes_%s.json' % (path, gid)
                    with open(filename, 'a') as json_file:
                        json.dump(notification, json_file)
                        print('', file=json_file)
                    with open(all_notification_filename, 'a') as json_file:
                        json.dump(notification, json_file)
                        print('', file=json_file)

            return notification

    def _save_message(self, message, group_name, chat_id, msg_id, file_name,
                      msg_id_path='/data/mensagens_grupo/'):
        """
        Escreve em formato json a mensagem coletada no arquivo
        referente ao grupo em que ela foi enviada. Caso o arquivo do grupo
        ainda não exista, ele será criado.

        Parâmetros
        ------------
            message : webwhatsapi.Message()
                Objeto da mensagem coletada.
            group_name : str
                Nome do grupo em que a mensagem foi enviada.
            chat_id : str
                Id do grupo em que a mensagem foi enviada.
            msg_id : str
                Id da mensagem coletada.
            file_name : str
                Nome do arquivo da mídia possivelmente contida na mensagem.
            msg_id_path : str
                Caminho da pasta em que os arquivos de mensagens por grupo
                serão escritos.
        """

        if not message.sender:
            return
        item = dict()
        sender = message.sender.id
        sender = sender.replace(' ', '').strip()
        sender = sender.split('@')[0]
        sender = ('+'+sender)

        try:
            phone = phonenumbers.parse(sender)
        except Exception:
            phone = phonenumbers.parse('+'+sender)
        country_code = phone.country_code
        country = phonenumbers.phonenumberutil.region_code_for_country_code(
            country_code)

        mid = smart_str(msg_id)
        gid = smart_str(chat_id)

        try:
            content = message.content
            content = smart_str(content)
            content = smart_str(content.replace('\n', ' '))
        except Exception:
            content = '<NoContent>'

        t = str(message)
        index = t.find(' at ') + 4
        index2 = index + 19
        date = str(t[index:index2])
        date = smart_str(date.replace(' ', '\t').strip())

        filename = '<NoFile>'
        mediatype = 'application/json'
        if (isinstance(message,  MESSAGE.MediaMessage) or
                isinstance(message, MESSAGE.MMSMessage)):
            mediatype = smart_str(message.type)
            try:
                filename = message.filename
                content = '<'+filename+'>'
            except Exception:
                filename = '<NoFile>'
            if hasattr(message, 'caption'):
                content = smart_str(message.caption)

        if 'text' in mediatype:
            mediatype = 'application/json'
        phash = ''
        checksum = ''

        if ((mediatype == 'image' and self.process_image_hashes) or
                (mediatype == 'video' and self.process_video_hashes) or
                (mediatype == 'audio' and self.process_audio_hashes)):
            dir = ""
            if mediatype == 'image':
                dir = self.data_path+"image"
            if mediatype == 'video':
                dir = self.data_path+"video"
            if mediatype == 'audio':
                dir = self.data_path+"audio"

            try:
                checksum = hash_functions.get_hash_from_method(os.path.join(
                    dir, message.filename), "checksum")
            except Exception:
                print("Couldn't process checksum for file %s." % (
                    message.filename))

            if mediatype == 'image':
                try:
                    phash = hash_functions.get_hash_from_method(os.path.join(
                        dir, message.filename), "phash")
                except Exception:
                    print("Couldn't process phash for file %s." % (
                        message.filename))

        item['mensagem_id'] = mid
        item['identificador'] = mid
        item['grupo_id'] = gid
        item['titulo'] = group_name
        item['pais'] = country
        item['enviado_por'] = smart_str(sender)
        item['criado_em'] = smart_str(date)
        item['tipo'] = mediatype
        item['arquivo'] = smart_str(filename)
        item['datalake'] = join(self.data_path, smart_str(filename))
        item['texto'] = smart_str(content)
        if (mediatype == 'video' or mediatype == 'image'
                or mediatype == 'audio'):
            item['checksum'] = checksum
        if mediatype == 'image':
            item['phash'] = phash

        messageLine = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%r\t%s\t%s' % \
            (mid, gid, group_name, country, smart_str(sender),
             smart_str(date), mediatype, checksum, smart_str(filename),
             self._process_string(content))
        print(messageLine)

        # Save message on kafka
                
        if self.save_kafka:
            topic = self.kafka.get_topic('whatsapp' , 'mensagem')
            json_dump_object = json.dumps(item)
            self.kafka.publish_kafka_message(self.producer, topic, 'raw', json_dump_object)
        
        if self.save_file:
            # Save message on group ID file
            if self.write_mode == 'group' or self.write_mode == 'file' or self.write_mode == 'both':
                message_group_filename = '%smensagens_grupo_%s.json' % (msg_id_path, gid)
                with open(message_group_filename, 'a') as json_file:
                    json.dump(item, json_file)
                    print('', file=json_file)

            if self.write_mode == 'day' or self.write_mode == 'file' or self.write_mode == 'both':
                message_day_filename = file_name

                # Save message on file for all messages of the day
                with open(message_day_filename, 'a') as json_file:
                    json.dump(item, json_file)
                    print('', file=json_file)
        
        
        # Always save mid reference for future checks
        reference_mid_filename = '/data/mids/%s.txt' % (gid)
        with open(reference_mid_filename, 'a') as fmid:
            messageLine = '%s\t%s\t%s' % (mid, gid, smart_str(date))
            print(messageLine, file=fmid)

        return item

    def run(self, profile_path="/data/firefox_cache"):
    
        profile_path = self.profile
        """
        Faz a coleta das mensagens de grupos de Whatsapp de acordo
        com os parâmetros fornecidos na criação do objeto de coleta.

        Parâmetros
        ------------
            profile_path : str
                Caminho para um profile alternativo do navegador
                utilizado na coleta.
        """
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
        driver = WhatsAPIDriver(loadstyles=True, profile=profile_path,
                                client="remote",
                                command_executor=os.environ["SELENIUM"])

        pathlib.Path(self.data_path+"mensagens").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"image").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"audio").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"video").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"mensagens_grupo").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"notificacoes").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"all_notificacoes").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/mids").mkdir(parents=True, exist_ok=True)

        min_date = self.start_date
        max_date = self.end_date
        include_notf = self.collect_notifications
        looping = True
        if (self.collection_mode == 'period') and (min_date < '2020-01-01'):
            raise Exception("Can't start collection without a start and end"
                            " date.")
        
        check_group_w = False
        check_group_b = False
        if len(self.group_whitelist) > 0: check_group_w = True
        if len(self.group_blacklist) > 0: check_group_b = True
        
        while looping:

            if self.collection_mode == 'continuous':
                looping = True
            else:
                looping = False

            try:
                print("Waiting for WhatsApp Web Login")
                driver.wait_for_login()
                print("Saving session")
                driver.save_firefox_profile(remove_old=False)
                print("Bot started")

                print('>>>>>>>>>>> Loading previous saved Messages')
                messagesID = self._get_load_messages()
                notificationsID = self._get_load_notifications()

                today_date = datetime.date.today().strftime("%Y-%m-%d")
                date_format = "%Y-%m-%d"
                file_name = self.data_path+"mensagens/mensagens_" + today_date + ".json"
                start_date = min_date

                print('>>>>>>>>>>>>Getting Groups Messages...', end=' ')
                chats = driver.get_all_chats()
                count = 0
                all_chats = list(chats)

                print(' DONE! %d chats loaded!' % (len(all_chats)))
                random.shuffle(all_chats)

                for chat in (all_chats):
                    # Does not collect direct messages, only group chats
                    if not chat._js_obj['isGroup']:
                        continue

                    gid = chat.id
                    gid = gid.split('@')[0]
                    s_name = self._process_string(chat.name)

                    if check_group_w and (gid not in self.group_whitelist):
                        if check_group_w and (s_name not in self.group_whitelist):
                            continue
                    if check_group_b and (gid in self.group_blacklist or s_name in self.group_blacklist):
                        print('Group',gid, str(s_name), 'in blacklist and will not be collected! Next group')
                        continue
                    
                    # Skip group if it is on blacklist (can be name or groupID)
                    if (s_name in self.group_blacklist or
                            gid in self.group_blacklist):
                        continue

                    # PRINT CHAT INFORMATION
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
                    if self.collection_mode == 'continuous':
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
                            chat, include_notifications=include_notf)

                    elif self.collection_mode == 'period':
                        till_date = datetime.datetime.strptime(start_date,
                                                               date_format)
                        # LOAD MESSAGES FROM WHATSAPP SINCE MIN_DATE
                        messages = chat.load_earlier_messages_till(till_date)
                        messages = driver.get_all_message_ids_in_chat(
                            chat, include_notifications=include_notf)

                    elif self.collection_mode == 'unread':
                        # LOAD UNREAD MESSAGES FROM WHATSAPP
                        messages = chat.get_unread_messages(
                            include_me=False,
                            include_notifications=include_notf)

                    print('>>>>>Total messages %d' % (len(messages)))
                    count += 1

                    for msg in messages:
                        count += 1
                        gid = gid.split('@')[0]
                        mid = msg

                        if self._is_notification(mid):
                            if gid not in notificationsID.keys():
                                notificationsID[gid] = set()
                            if mid.strip() in notificationsID[gid]:
                                continue
                            j = driver.get_message_by_id(mid)
                            self._save_notification_(j, gid)
                            continue

                        if mid.strip() in messagesID[gid]['messages']:
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
                        
                        if not self.check_user(j): continue
                        
                        try:
                            date = self._get_date_from_message(j)
                        except Exception:
                            continue

                        if (date > max_date) and (self.collection_mode == 'period'):
                            break
                        if (date < start_date):
                            continue

                        # Update day
                        if today_date != date:
                            today_date = date
                            file_name = self.data_path+"mensagens/mensagens_" + today_date + ".json"

                        if self.collect_images:
                            try:
                                self._get_image_from_message(j, self.data_path+"image")
                            except Exception as ei:
                                print('!!!!Error getting image!!!! ', ei)

                        if self.collect_videos:
                            try:
                                self._get_video_from_message(j, self.data_path+"video")
                            except Exception as ev:
                                print('!!!!Error getting video!!!! ', ev)

                        if self.collect_audios:
                            try:
                                self._get_audio_from_message(j, self.data_path+"audio")
                            except Exception as ea:
                                print('!!!!Error getting audio!!!! ', ea)

                        if self.collect_messages:
                            self._save_message(j, s_name, gid, mid, file_name)

                driver.close()
            except Exception as e:
                print(e)
                driver.close()
                raise Exception(e)

            if looping:
                print('Waiting code to start again...')
                time.sleep(3600)


def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

        
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--collection_mode", type=str,
                        help="Modo de coleção a ser utilizado (\'period\'"
                        " ou \'unread\' ou \'continuous\').",
                        default='continuous')

    parser.add_argument("-p", "--profile", type=str,
                        help="Perfil de usuario",
                        default='/data/firefox_cache')

    parser.add_argument("-s", "--start_date", type=str,
                        help="Data de início do período de coleta (Modo"
                        " \'period\').", default='2000-01-01')

    parser.add_argument("-e", "--end_date", type=str,
                        help="Data de término do período de coleta (Modo"
                        " \'period\').", default='2999-12-31')

    parser.add_argument("-w", "--write_mode", type=str,
                        help="Modo de salvamento das mensagens no arquivos de saída(\'both\', \'day\', \'group\', \'kafka\'). ", default='kafka')

    parser.add_argument("--collect_messages", type=str2bool,
                        help="Se mensagens de texto devem ser coletadas"
                        " durante a execução.", default=True)

    parser.add_argument("--collect_audios", type=str2bool,
                        help="Se audios devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--collect_videos", type=str2bool,
                        help="Se videos devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--collect_images", type=str2bool,
                        help="Se imagens devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--collect_notifications", type=str2bool,
                        help="Se as notificações devem ser coletadas durante a"
                        " execução.", default=True)

    parser.add_argument("--process_audio_hashes", type=str2bool,
                        help="Se hashes de audios devem ser calculados durante"
                        " a execução.", default=True)

    parser.add_argument("--process_image_hashes", type=str2bool,
                        help="Se hashes de imagens devem ser calculados"
                        " durante a execução.", default=True)

    parser.add_argument("--process_video_hashes", type=str2bool,
                        help="Se hashes de videos devem ser calculados durante"
                        " a execução.", default=True)

    parser.add_argument("--group_blacklist", nargs="+",
                        help="Lista de ids de grupos que devem ser excluídos da"
                        " coleta", default=[])
                        
    parser.add_argument("--user_blacklist", nargs="+",
                        help="Lista de ids de grupos que devem ser excluídos da"
                        " coleta", default=[])

    parser.add_argument("--group_whitelist", nargs="+",
                        help="Lista de ids de grupos que devem ser incluidos da"
                        " coleta", default=[])

    parser.add_argument("--user_whitelist", nargs="+",
                        help="Lista de usuarios que devem ser incluidos da"
                        " coleta", default=[])

    parser.add_argument("--datalake", type=str,
                        help="Local onde sao salvas as midias",
                        default='/datalake/ufmg/whatsapp/')
                        
    parser.add_argument("--session_name", type=str,
                        help="Nome de secao para autenticacao da API do Telegram. Gera um arquivo <seciton_name>.session autorizando a conta a usar  a API",
                        default='telegram_api')

    parser.add_argument("--bootstrap_servers", nargs="+",
                        help="Lista de endereço para conexão dos servers Kafka"
                        " (Brokers)", default=[])

    parser.add_argument("-j", "--json", type=str,
                        help="Caminho para um arquivo json de configuração de "
                        "execução. Individualmente, as opções presentes no "
                        "arquivo sobescreveram os argumentos de linha de "
                        "comando, caso eles sejam fornecidos.")

    parser.add_argument("--json_string", type=str,
                        help="String contendo um json de configuração de"
                        " execução. Individualmente, as opções presentes no "
                        "arquivo sobescreveram os argumentos de linha de "
                        "comando, caso eles sejam fornecidos.")

    args = parser.parse_args()

    try:
        collector = WhatsappCollector(args)
        collector.run( )
    except Exception as e:
        error_time = str(datetime.datetime.now())
        error_msg = str(e).strip()
        with open('/data/log.txt', 'w') as ferror:
            print("%s >> Error:\t%s" % (error_time, error_msg))
            print("%s >> Error:\t%s" % (error_time, error_msg), file=ferror)


if __name__ == '__main__':
    main()

