# -*- coding: utf-8 -*-
from telethon import TelegramClient, events
from PIL import Image
from kafka_functions import KafkaManager
from kafka import KafkaConsumer
from kafka import KafkaProducer

import asyncio
import pathlib
import argparse
import datetime
import time
import json
import traceback
import hashlib
import imagehash
import pytz
import os
import sys

from shutil import copyfile
from os import listdir
from os.path import isfile, join 

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class TelegramCollector():
    """
    Classe que encapsula o coletor de grupos do Telegram. Possui
    o metodo principal que realiza a leitura da entrada e faz a
    coleta das mensagens, midias e notificacoes.
    Atributos
    -----------
    collection_mode : str
            Modo de colecao a ser utilizado ("period" ou "unread" ou 
            "continuous").
    start_date : str
            Data de inicio do periodo de coleta (Modo "period").
    end_date : str
            Data de termino do periodo de coleta (Modo "period").
    group_blacklist : list
            Lista de ids de grupos que devem ser excluidos da coleta.
    user_blacklist : list
            Lista de ids de usuarios que devem ser excluidos da coleta.
    collect_messages : bool
            Se mensagens de texto devem ser coletadas durante a execucao.
    collect_audios : bool
            Se audios devem ser coletadas durante a execucao.
    collect_videos : bool
            Se videos devem ser coletadas durante a execucao.
    collect_images : bool
            Se imagens devem ser coletadas durante a execucao.
    collect_notifications : bool
            Se notificacoes devem ser coletadas durante a execucao.
    process_audio_hashes : bool
            Se hashes de audios devem ser calculados durante a execucao.
    process_image_hashes : bool
            Se hashes de imagens devem ser calculados durante a execucao.
    process_video_hashes : bool
            Se hashes de videos devem ser calculados durante a execucao.
    api_id : str
            ID da API de Coleta gerado em my.telegram.org (Dado sensivel).
    api_hash : str
            Hash da API de Coleta gerado em my.telegram.org (Dado sensivel).
    
    Metodos
    -----------
    Faz a coleta das mensagens de grupos de Telegram de acordo
    com os parametros fornecidos na criacao do objeto de coleta.

        Parametros
        ------------
            profile_path : str
                Caminho para um profile alternativo do navegador
                utilizado na coleta.
    """

    def __init__(self, args):
        """
        Inicializa o objeto

        Parametros
        ------------
            args : argparse.Namespace()
                Objeto com atributos que contem os argumentos de linha de
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
        if args_dict["write_mode"] not in ['both', 'file', 'kafka']:
            print('Save mode invalid <%s>!! Using <kafka> instead' % (
                args_dict["write_mode"]))
            args_dict["write_mode"] = 'kafka'

        self.session_name          = args_dict["session_name"]
        if (args_dict["api_id"] == '' or args_dict["api_id"] == None) or (args_dict["api_hash"] == '' or args_dict["api_hash"] == None):
            keys_file = '/config/credentials_%s.json'%(self.session_name) 
            if os.path.isfile(keys_file):
                with open(keys_file, 'r') as fin:
                    keys_args = json.load(fin)
                    args_dict["api_id"]       = keys_args["api_id"]
                    args_dict["api_hash"]     = keys_args["api_hash"]
                    args_dict["session_name"]  = keys_args["session_name"]
            else:
                print('No credentials provided: api_id, api_hash\nUnable to connect to Telegram API...')
                sys.exit(1)
            
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
        self.collect_others        = args_dict["collect_others"]
        self.collect_notifications = args_dict["collect_notifications"]
        self.process_audio_hashes  = args_dict["process_audio_hashes"]
        self.process_image_hashes  = args_dict["process_image_hashes"]
        self.process_video_hashes  = args_dict["process_video_hashes"]
        self.process_other_hashes  = args_dict["process_other_hashes"]
        self.api_id                = args_dict["api_id"]
        self.api_hash              = args_dict["api_hash"]
        self.datalake              = args_dict["datalake"]
        self.session_name          = args_dict["session_name"]
        


        self.data_path              = '/data/'        
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
            
        #SAVING CREDENTIALS FOR FUTURE
        with open('/config/credentials_%s.json'%(args_dict["session_name"])  , "w") as json_file:
            api_dict = dict()
            api_dict["api_id"]        = args_dict["api_id"]
            api_dict["api_hash"]      = args_dict["api_hash"]
            api_dict["session_name"]  = args_dict["session_name"]
            json.dump(api_dict, json_file)
        

    def check_user(self, message):
        check_user_w = False
        check_user_b = False
        if len(self.user_whitelist) > 0: check_user_w = True
        if len(self.user_blacklist) > 0: check_user_b = True
        
        sender = ''
        try:
            sender = message.from_id.user_id
        except:
            sender = str(message.to_id.channel_id)

        if check_user_w and (sender not in self.user_whitelist):
            if check_user_w and (sender not in self.user_whitelist):
                return False
                
        if check_user_b and (sender in self.user_blacklist or sender in self.user_blacklist):
            print('User', sender, 'in user blacklist!!! Next message')
            return False
                    
        
        return True
        
    def _get_load_messages(self, path='/data/mid_file.txt'):
        """
        Carrega e retorna um conjunto de ids das mensagens ja coletadas.

        Parametros
        ------------
            path : str
                Caminho para o arquivo contendo os ids das mensagens.
        """
        messagesIDs = set()
        
        if os.path.isfile(path):
            with open(path, 'r') as fin:
                for line in fin:
                    messagesIDs.add((line.strip()))

        return messagesIDs

    def _save_processed_ids(self, id_set, path='/data/mid_file.txt'):
        """
        Salva o conjunto de ids das mensagens ja coletadas.

        Parametros
        ------------
            path : str
                Caminho para o arquivo contendo os ids das mensagens.
        """
        with open(path+".temp", 'w') as fmid:
            for id in id_set:
                print(str(id), file=fmid)
        
        if os.path.isfile(path):
            os.remove(path)
        os.rename(path + ".temp", path)

    def _append_processed_id(self, id, path='/data/mid_file.txt'):
        """
        Salva um novo id de uma mensagem coletada.

        Parametros
        ------------
            path : str
                Caminho para o arquivo contendo os ids das mensagens.
        """
        with open(path, 'a') as fmid:
            print(str(id), file=fmid)

    async def _save_message(self, message, dialog_name, now, daily_path = "/data/mensagens/", group_path="/data/mensagens_grupo/"):
        """
        Escreve em formato json a mensagem coletada no arquivo
        referente ao grupo em que ela foi enviada. Caso o arquivo do grupo
        ainda nao exista, ele sera criado.
        Parametros
        ------------
            message : telethon.tl.custom.message.Message()
                Objeto da mensagem coletada.
            group_path : str
                Caminho da pasta em que os arquivos de mensagens por grupo
                serao escritos.
        """
        #print(message) #log message
        
        item = dict()
        item["idt_coleta"] = now
        try: 
            item["grupo_id"] = message.to_id.chat_id
        except:
            item["grupo_id"] = message.to_id.channel_id
                
        item["identificador"] = message.id
        item["mensagem_id"] = message.id
        item["titulo"] = dialog_name
        
        #print(message)
        #print(message.from_id)
        try:
            item["enviado_por"]     = message.from_id.user_id
        except:
            item["enviado_por"]     = str(message.to_id.channel_id)

        
        item["criado_em"]       = message.date.strftime("%Y-%m-%d %H:%M:%S")
        item["texto"]    = message.message 
        item["arquivo"]  = None
        item["tipo"]  = None
        item["phash"]    = None
        item["checksum"] = None
        
        if message.media:
            if message.photo:
                base_path = self.data_path+"image/"
                item["tipo"] = "image"
            elif message.audio or message.voice:
                base_path = self.data_path+"audio/"
                item["tipo"] = "audio"
            elif message.video or message.video_note:
                base_path = self.data_path+"video/"
                item["tipo"] = "video"
            else:
                base_path = self.data_path+"others/"
                item["tipo"] = "other"

            if (item["tipo"] == "image" and self.collect_images) or \
                    (item["tipo"] == "audio" and self.collect_audios) or \
                    (item["tipo"] == "video" and self.collect_videos) or \
                    (item["tipo"] == "other" and self.collect_others):
                path = os.path.join(base_path, message.date.strftime("%Y-%m-%d"))
                pathlib.Path(path).mkdir(parents=True, exist_ok=True)
                
                path = os.path.join(base_path, message.date.strftime("%Y-%m-%d"), str(item["identificador"]))
                try:
                    file_path = await message.download_media(path)
                    
                    if file_path:
                        if os.path.isfile(file_path): 
                            
                            item["arquivo"] = file_path.split("/")[-1]
                            item["datalake"] = join(self.datalake, item["tipo"], item["criado_em"][0:+10], file_path.split("/")[-1])

                            if file_path != None and (
                                    (item["tipo"] == "image" and self.process_image_hashes) or 
                                    (item["tipo"] == "audio" and self.process_audio_hashes) or 
                                    (item["tipo"] == "video" and self.process_video_hashes) or 
                                    (item["tipo"] == "other" and self.process_other_hashes)):
                                item["checksum"] = md5(file_path)
                                if item["tipo"] == "image":
                                    try: 
                                        item["phash"] = str(imagehash.phash(Image.open(file_path)))
                                    except:
                                        item["phash"] = str(imagehash.phash(Image.open(file_path)))
                except:
                    print ("Error getting the file")
                    item["phash"] = None
                    item["checksum"] = None
                
        print(item)

        if self.save_kafka:
            topic = self.kafka.get_topic('telegram' , 'mensagem')
            json_dump_object = json.dumps(item)
            self.kafka.publish_kafka_message(self.producer, topic, now, json_dump_object)
            
        if self.save_file:
            if self.write_mode == "file" or self.write_mode == "both":
                message_group_filename = os.path.join(group_path, "mensagens_grupo_" + str(item["grupo_id"]) + ".json" )

                
                # Save message on file for all messages of the group
                with open(message_group_filename, "a") as json_file:
                    json.dump(item, json_file)
                    print("", file=json_file)

            if self.write_mode == "file" or self.write_mode == "both":
                message_day_filename = os.path.join(daily_path, "mensagens_" + message.date.strftime("%Y-%m-%d") + ".json")

                # Save message on file for all messages of the day
                with open(message_day_filename, "a") as json_file:
                    json.dump(item, json_file)
                    print("", file=json_file)
    
    def _save_notification(self, message, now, path='/data/notificacoes/'):
        """
        Escreve em formato json a notificacao contida na mensagem no arquivo
        referente ao grupo em que ela foi enviada. Caso o arquivo do grupo
        ainda nao exista, ele sera criado.
        Parametros
        ------------
            message : telethon.tl.custom.message.Message()
                Objeto da mensagem coletada.
            path : str
                Caminho da pasta em que os arquivos de notificacoes serao
                escritos.
        """
        notification = dict()

        notification["idt_coleta"] = now
        notification["identificador"] = message.id
        
        try: 
            notification["grupo_id"] = message.to_id.chat_id
        except:
            notification["grupo_id"] = message.to_id.channel_id
        notification["enviado_em"] = message.date.strftime("%Y-%m-%d %H:%M:%S")       
        notification["acao"] = {"action_class" : type(message.action).__name__ , 
                                  "fields" : message.action.__dict__}
                                  
        
        try:
            notification["enviado_por"] = message.from_id.user_id
        except:
            notification["enviado_por"] = str(message.to_id.channel_id)
            
        #notification["enviado_por"] = message.from_id.user_id

        notification_group_filename = os.path.join(
            path, "notificacoes_grupo_" + str(notification["grupo_id"]) + ".json" )

        if self.save_file:
            #Save message on file for all messages of the group
            #Nao chamar, pois sera salvo no kafka
            with open(notification_group_filename, "a") as json_file:
                json.dump(notification, json_file)
                print("", file=json_file)
 
        if self.save_kafka:
            topic = self.kafka.get_topic('telegram' , 'notificacao')
            json_dump_object = json.dumps(notification)
            self.kafka.publish_kafka_message(self.producer, topic, now, json_dump_object)

    async def _run_unread_collector(self):
        
        session_name =  '%s.session'%(self.session_name)
        if isfile( join(self.data_path, session_name) ):
            copyfile(join(self.data_path, session_name), session_name)
        
        async_client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        if isfile(session_name):
            copyfile(session_name, join(self.data_path, session_name))
            
        group_names = {}

        @async_client.on(events.NewMessage)
        async def event_handler(event):
            message = event.message
            if (self.collect_messages and message.to_id.chat_id and 
                    group_names[str(message.to_id.chat_id)] and 
                    str(message.from_id) not in self.user_blacklist):
                await self._save_message(message, group_names[str(message.to_id.chat_id)])
                self._append_processed_id(message.id)

        @async_client.on(events.ChatAction)
        async def event_handler(event):
            message = event.action_message
            if (self.collect_notifications and message.to_id.chat_id and 
                    group_names[str(message.to_id.chat_id)] and 
                    str(message.from_id) not in self.user_blacklist):
                self._save_notification(message)
                self._append_processed_id(message.id)
                if (type(message.action).__name__ == "MessageActionChatEditTitle") :
                    #in case the title changes
                    group_names[str(message.to_id.chat_id)] = message.action.title

        await async_client.start()

        async for dialog in async_client.iter_dialogs():
            if ((dialog.is_group or dialog.is_channel) and dialog.title not in self.group_blacklist and
                    str(abs(dialog.entity.id)) not in self.group_blacklist):
                    
                group_names[str(abs(dialog.entity.id))] = dialog.title

        await async_client.run_until_disconnected()

    async def run(self):
        """
        Faz a coleta das mensagens de grupos de Telegram de acordo
        com os parametros fornecidos na criacao do objeto de coleta.
        """

        # Create data directories
        pathlib.Path("/data/mensagens").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"image").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"others").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"audio").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.data_path+"video").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/mensagens_grupo").mkdir(parents=True, exist_ok=True)
        pathlib.Path("/data/notificacoes").mkdir(parents=True, exist_ok=True)

        # Get start and end dates
        utc = pytz.UTC
        start_date = utc.localize(datetime.datetime.strptime(self.start_date, "%Y-%m-%d"))
        end_date = utc.localize(datetime.datetime.strptime(self.end_date, "%Y-%m-%d"))

        # Sets the id of the current collection
        now = str(int(time.time()*1000))

        # Load previous saved messages
        previous_ids = self._get_load_messages()

        session_name =  '%s.session'%(self.session_name)
        if isfile( join(self.data_path, session_name) ):
            copyfile(join(self.data_path, session_name), session_name)
        
        
        check_group_w = False
        check_group_b = False
        if len(self.group_whitelist) > 0: check_group_w = True
        if len(self.group_blacklist) > 0: check_group_b = True
        
        
        print("Starting " + self.collection_mode + " collection.")
        try:
            if (self.collection_mode != 'unread'):
                async with TelegramClient(self.session_name, self.api_id, self.api_hash) as client:
                
                    print("Susccessfully connected to API")
                    if isfile(session_name):
                        copyfile(session_name, join(self.data_path, session_name))
                        
                    
                    async for dialog in client.iter_dialogs():
                        group_id = dialog.entity.id
                        try:
                            group_name = dialog.entity.title
                        except:
                            continue
                         
                        if check_group_w and (group_id not in self.group_whitelist):
                            if check_group_w and (group_name not in self.group_whitelist):
                                continue
                        if check_group_b and (group_id in self.group_blacklist or group_name in self.group_blacklist):
                            print('Group',group_id, str(group_name), 'in blacklist and will not be collected! Next group')
                            continue
                    
                    
                        if (dialog.is_group or dialog.is_channel):
                            
                            if   dialog.is_group:   inst = 'group'
                            if dialog.is_channel:   inst = 'channel'
                            print("Collecting mssages for " + str(inst) + ":" + str(group_id) + " - " + str(group_name))
                            async for message in client.iter_messages(dialog):
                                if not self.check_user(message): continue
                                
                                new_id = str(group_id)+'_'+str(message.id )
                                message.id = new_id
                                if (message.date < start_date):
                                    break
                                if (message.date > end_date and self.collection_mode == 'period'):
                                    continue
                                if (message.id in previous_ids):
                                    continue

                                if (not message.action) and self.collect_messages:
                                    await self._save_message(message, dialog.entity.title, now)
                                    previous_ids.add(message.id)   
                                elif message.action and self.collect_notifications:
                                    self._save_notification(message, now)
                                    previous_ids.add(message.id)   

            self._save_processed_ids(previous_ids)

            print("Finished collection.")
        except Exception as e:
            traceback.print_exc()
            self._save_processed_ids(previous_ids)

        if (self.collection_mode == 'unread' or 
                self.collection_mode == 'continuous'): 
            print("Starting unread message collection.")
            await self._run_unread_collector()

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

async def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--collection_mode", type=str,
                        help="Modo de colecao a ser utilizado (\'period\'"
                        " ou \'unread\' ou \'continuous\').",
                        default='period')

    parser.add_argument("-s", "--start_date", type=str,
                        help="Data de inicio do periodo de coleta (Modo"
                        " \'period\').", default='2000-01-01')

    parser.add_argument("-e", "--end_date", type=str,
                        help="Data de termino do periodo de coleta (Modo"
                        " \'period\').", default='2999-12-31')

    parser.add_argument("-w", "--write_mode", type=str,
                        help="Modo de salvamento das mensagens no arquivos de saida(\'both\', \'file\', \'kafka\'). ", default='kafka')

    parser.add_argument("--collect_messages", type=str2bool,
                        help="Se mensagens de texto devem ser coletadas"
                        " durante a execucao.", default=True)

    parser.add_argument("--collect_audios", type=str2bool,
                        help="Se audios devem ser coletadas durante a"
                        " execucao.", default=True)

    parser.add_argument("--collect_videos", type=str2bool,
                        help="Se videos devem ser coletadas durante a"
                        " execucao.", default=True)

    parser.add_argument("--collect_images", type=str2bool,
                        help="Se imagens devem ser coletadas durante a"
                        " execucao.", default=True)

    parser.add_argument("--collect_others", type=str2bool,
                        help="Se outros tipos de midia (e.g. documentos, stickers) devem "
                        "ser coletadas durante a execucao.", default=True)

    parser.add_argument("--collect_notifications", type=str2bool,
                        help="Se as notificacoes devem ser coletadas durante a"
                        " execucao.", default=True)

    parser.add_argument("--process_audio_hashes", type=str2bool,
                        help="Se hashes de audios devem ser calculados durante"
                        " a execucao.", default=True)

    parser.add_argument("--process_image_hashes", type=str2bool,
                        help="Se hashes de imagens devem ser calculados"
                        " durante a execucao.", default=True)

    parser.add_argument("--process_video_hashes", type=str2bool,
                        help="Se hashes de videos devem ser calculados durante"
                        " a execucao.", default=True)

    parser.add_argument("--process_other_hashes", type=str2bool,
                        help="Se hashes de outros tipos de midiaa devem ser calculados durante"
                        " a execucao.", default=False)

    parser.add_argument("--group_blacklist", nargs="+",
                        help="Lista de ids de grupos que devem ser excluidos da"
                        " coleta", default=[])

    parser.add_argument("--user_blacklist", nargs="+",
                        help="Lista de usuarios que devem ser excluidos da"
                        " coleta", default=[])

    parser.add_argument("--group_whitelist", nargs="+",
                        help="Lista de ids de grupos que devem ser incluidos da"
                        " coleta", default=[])

    parser.add_argument("--user_whitelist", nargs="+",
                        help="Lista de usuarios que devem ser incluidos da"
                        " coleta", default=[])

    parser.add_argument("--api_id", type=str,
                        help="ID da API de Coleta gerado em my.telegram.org (Dado sensivel)", default='')

    parser.add_argument("--api_hash", type=str,
                        help="Hash da API de Coleta gerado em my.telegram.org (Dado sensivel)", default='')

    parser.add_argument("--datalake", type=str,
                        help="Local onde sao salvas as midias",
                        default='/datalake/ufmg/telegram/')
                        
    parser.add_argument("--session_name", type=str,
                        help="Nome de secao para autenticacao da API do Telegram. Gera um arquivo <seciton_name>.session autorizando a conta a usar  a API",
                        default='telegram_api')
                        
    parser.add_argument("--bootstrap_servers", nargs="+",
                        help="Lista de endereco para conexao dos servers Kafka"
                        " (Brokers)", default=[])

                        
    parser.add_argument("-j", "--json", type=str,
                        help="Caminho para um arquivo json de configuracao de "
                        "execucao. Individualmente, as opcoes presentes no "
                        "arquivo sobescreveram os argumentos de linha de "
                        "comando, caso eles sejam fornecidos.")

    parser.add_argument("--json_string", type=str,
                        help="String contendo um json de configuracao de"
                        " execucao. Individualmente, as opcoes presentes no "
                        "arquivo sobescreveram os argumentos de linha de "
                        "comando, caso eles sejam fornecidos.")

    args = parser.parse_args()

    try:
        collector = TelegramCollector(args)
        await collector.run()
    except Exception as e:
        #TODO: Print log file
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())

