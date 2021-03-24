from __future__ import print_function

from builtins import str
from webwhatsapi import WhatsAPIDriver


from kafka_functions import KafkaManager
from kafka import KafkaConsumer
from kafka import KafkaProducer


import datetime
import os
import pathlib
import json
import argparse


from os import listdir
from os.path import isfile, join


def smart_str(x):
    if isinstance(x, int) or isinstance(x, float):
        return str(x, "utf-8")
    return x


def convert_data_from_timestamp(time_message):
    time_obj = datetime.datetime.fromtimestamp(time_message)
    return time_obj


class GroupMetadataCollector():
    """
    Classe que encapsula o coletor de metadados de grupos do Whatsapp. Possui
    o método principal que realiza a leitura da entrada e faz a coleta de
    informações como o título, integrantes, criador e administrados dos grupos
    que o usuário faz parte.

    Atributos
    -----------
    group_blacklist : list
            Lista de ids de grupos que devem ser excluídos da coleta.

    Métodos
    -----------
    run()
        Faz a coleta dos metadados de grupos de Whatsapp de acordo
        com os parâmetros fornecidos na criação do objeto de coleta.
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
        
        if args_dict["write_mode"] not in ['both', 'file', 'kafka']:
            print('Save mode invalid <%s>!! Using <kafka> instead' % (
                args_dict["write_mode"]))
            args_dict["write_mode"] = 'kafka'
        
        
        if args.json:
            with open(args.json) as json_file:
                json_args = json.load(json_file)
                args_dict.update(json_args)
        elif args.json_string:
            json_args = json.loads(args.json_string)
            args_dict.update(json_args)

        self.data_path           = '/data/'
        self.datalake            = args_dict["datalake"]
        self.write_mode          = args_dict["write_mode"]
        self.group_blacklist     = args_dict["group_blacklist"]
        self.bootstrap_servers   = args_dict["bootstrap_servers"]
        self.profiles            = args_dict["profiles"]


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

    def run(self, profile_path="/data/firefox_cache"):
        """
        Faz a coleta dos metadados de grupos de Whatsapp de acordo
        com os parâmetros fornecidos na criação do objeto de coleta.

        Parâmetros
        ------------
            profile_path : str
                Caminho para um profile alternativo do navegador
                utilizado na coleta.
        """

        today = datetime.date.today().strftime('%Y-%m-%d')
        all_groups_filename = '/data/all_grupos_%s.json' %(today)
        with open(all_groups_filename, 'w') as json_file:
            print('Collecting metadata for groups at %s'%(today)) 

        if not os.path.exists(profile_path):
            os.makedirs(profile_path)

        driver = WhatsAPIDriver(
            loadstyles=True, profile=profile_path, client="remote",
            command_executor=os.environ["SELENIUM"])

        try:
            print("Waiting for WhatsApp Web Login")
            driver.wait_for_login()
            print("Saving session")
            driver.save_firefox_profile(remove_old=False)
            print("Bot started")

            pathlib.Path(join(self.data_path, 'grupos/')).mkdir(parents=True, exist_ok=True)

            print('>>>>>>>>>>> Loading chat ids')
            chats = driver.get_all_chats()

            for chat in (chats):
                # Does not collect direct messages, only group chats
                if not chat._js_obj['isGroup']:
                    continue

                gid = chat.id
                gid = gid.split('@')[0]
                s_name = self._process_string(chat.name)

                # Skip group if it is on blacklist (can be name or groupID)
                if (s_name in self.group_blacklist or
                        gid in self.group_blacklist):
                    continue

                group = dict()

                _id = chat.id
                creator = _id.split('-')[0]
                timestamp = _id.split('-')[-1].split('@')[0]
                date = convert_data_from_timestamp(float(timestamp))
                str_date = date.strftime('%Y-%m-%d %H:%M:%S')
                name = chat.name.strip().replace('\t', ' ')

                kind = chat._js_obj["kind"]

                participants = list()
                if self.profiles:
                    for member in driver.group_get_participants(_id):
                        user = dict()
                        user['name'] = member.verified_name
                        user['short_name'] = member.short_name
                        user['nome_formatado'] = member.formatted_name
                        user['number'] = member.id
                        user['isBusiness'] = member.is_business
                        user['profile_pic'] = member.profile_pic
                        participants.append(user)

                group['group_id'] = _id
                group['creator'] = creator
                group['kind'] = kind
                group['creation'] = dict()
                group['creation']['creation_date'] = str_date
                group['creation']['creation_timestamp'] = timestamp
                group['title'] = name
                group['members'] = participants

                path = join(self.data_path, 'grupos/')
                filename = '%sgrupos_%s.json' % (path, _id.split('@')[0].strip())
                print(group)
                
                if self.save_kafka:
                    topic = self.kafka.get_topic('whatsapp' , 'grupo')
                    json_dump_object = json.dumps(group)
                    self.kafka.publish_kafka_message(self.producer, topic, 'raw', json_dump_object)
            
                
                if self.save_file:
                    with open(filename, 'w') as json_file:
                        json.dump(group, json_file)
                        print('', file=json_file)
                    with open(all_groups_filename, 'a') as json_file:
                        json.dump(group, json_file)
                        print('', file=json_file)

            driver.close()
        except Exception as e:
            print(e)
            driver.close()
            raise Exception(e)

               
                
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

    parser.add_argument("--group_blacklist", nargs="+",
                        help="Lista de ids de grupos que devem ser excluídos"
                        " da coleta", default=[])

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
                            
    parser.add_argument("--profiles", type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Flag para listar quem sÃo os usuários ")
                        
                        
    parser.add_argument("-w", "--write_mode", type=str,
                        help="Modo de salvamento das mensagens no arquivos de saída(\'file\', \'kafka\'). ", default='kafka')

    parser.add_argument("--datalake", type=str,
                        help="Local onde sao salvas as midias",
                        default='/datalake/ufmg/whatsapp/')

    parser.add_argument("--bootstrap_servers", nargs="+",
                        help="Lista de endereço para conexão dos servers Kafka"
                        " (Brokers)", default=[])


    args = parser.parse_args()
    
    
    try:
        collector = GroupMetadataCollector(args)
        collector.run()
    except Exception as e:
        error_time = str(datetime.datetime.now())
        error_msg = str(e).strip()
        with open('/data/log_grupos.txt', 'w') as ferror:
            print("%s >> Error:\t%s" % (error_time, error_msg))
            print("%s >> Error:\t%s" % (error_time, error_msg), file=ferror)


if __name__ == '__main__':
    main()

