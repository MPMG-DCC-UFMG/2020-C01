# -*- coding: utf-8 -*-
import copy
import importlib
import json
import time

from kafka import KafkaConsumer
from kafka import KafkaProducer

import sys


class KafkaManager():

    """
    Classe que encapsula as funções referentes ao gerenciamento de filas no Kafka. 
    Possui um método principal que realiza a conexão com o servidor e outra para 
    publicação de mensagem na fila do Kafka (não existe função para consumo do Kafka, 
    pois o coletor funciona apenas como "producer".

    Atributos
    -----------
    KAFKA_SERVERS : list
            Lista de ids dos servidores da fila KAFKA no MPMG.
    KAFKA_TOPIC_STATUS_OK: string
            Topico Kafka de status de sucesso de execução
    KAFKA_TOPIC_STATUS_ERROR: string
            Topico Kafka de status de erro de execução
    
    Métodos
    -----------
    publish_kafka_message(producer_instance, topic_name, key, value):
        Faz a coleta dos metadados de grupos de Telegram de acordo
        com os parâmetros fornecidos na criação do objeto de coleta.
    connect_kafka_producer():
        Faz a coleta dos metadados de grupos de Telegram de acordo
        com os parâmetros fornecidos na criação do objeto de coleta.
    get_topic(socialnetwork, entity):
        Retorna o topico do kafka que será utilizado para a fila dependendo
        da rede social e da entidade de dados manipulada
    """

    def __init__(self):
        """
        Inicializa o objeto

        Parâmetros
        ------------
            args : argparse.Namespace()
                Objeto com atributos que contém os argumentos de linha de
                comando fornecidos.
        """
        #args_dict = vars(args)
        
        ### XXX TODO verificar se esses topicos vao mudar
        #self.KAFKA_SERVERS            = [('hadoopdn-gsi-prod0' + str(j) + '.mpmg.mp.br:6667').replace('010', '10') for j in range(4, 10 + 1)]
        self.KAFKA_SERVERS            = ['hadoopdn-gsi-prod04.mpmg.mp.br:6667'] 
        #self.KAFKA_SERVERS            = ['192.168.99.100:9092'] #Server padrão para testes
        self.KAFKA_TOPIC_STATUS_OK    = "crawler_status_ok"
        self.KAFKA_TOPIC_STATUS_ERROR = "crawler_status_error"

     
        
    def publish_kafka_message(self, producer, topic_name, key, value):
        '''
        Many thanks to https://towardsdatascience.com/getting-started-with-apache-kafka-in-python-604b3250aa05
        '''

        # usage example:
        # publish_message(kafka_producer, 'crawler_whatsapp_message', 'raw', my_string.strip())
        sent = False
        
        if  producer  is not None:
            try:
                key_bytes = bytes(key, encoding='utf-8')
                value_bytes = bytes(value, encoding='utf-8')
                #producer.send(topic_name, key=key_bytes, value=value_bytes)
                producer.send(topic_name,  str.encode(value) )
                producer.flush()
                print('Message published successfully.')
                sent = True
            except Exception as ex:
                print('Exception in publishing message')
                print(str(ex))

        return sent


    def connect_kafka_producer(self ):
        _producer = None
        ##return _producer

        try:
            _producer = KafkaProducer(bootstrap_servers=self.KAFKA_SERVERS, api_version=(0, 10))
            
            if not _producer.bootstrap_connected():
                #_producer = None
                print('Bootstrap not connected!')
            else:
                print('Kafka producer connected succesfully!!')
        except Exception as ex:
            print('Exception while connecting Kafka')
            print(str(ex))

        return _producer


    def get_topic(self, socialnetwork, entity):
        wg = 'crawler_whatsapp_grupo'
        wm = 'crawler_whatsapp_mensagem'
        tg = 'crawler_telegram_grupo'
        tm = 'crawler_telegram_mensagem'
        topics = {
            'whatsapp':{
                'grupo':       'crawler_whatsapp_grupo',
                'notificacao': 'crawler_whatsapp_mensagem',
                'mensagem':    'crawler_whatsapp_mensagem'
            },
            'telegram':{
                'grupo':       'crawler_telegram_grupo',
                'notificacao': 'crawler_telegram_mensagem',
                'mensagem':    'crawler_telegram_mensagem'
            }
        }
        
        s = socialnetwork.lower()
        e = entity.lower()
        try:
            kafka_topic = topics[s][e]        
        except KeyError as e:
            print('Topic error')
            raise Exception('Kafka Error!! Topic for social network %s and entity %s not found.' %(socialnetwork, entity))
        
        return kafka_topic
        
    def create_error_file(self, crawling_id, error_document):
        try:
            ### Se o metodo de error foi chamado crawling_id ja esta preechido
            json_dump_object = json.dumps({"crawling_id": crawling_id, "document": document})
            self.publish_kafka_message(self.producer, self.KAFKA_TOPIC_STATUS_ERROR, 'raw', json_dump_object)
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.getErrorDocument(exception_obj=e, exc_type=exc_type, exc_tb=exc_tb)
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now())
            print("Finalizando script...")
            sys.exit(1)
            
            
    def getErrorDocument(self, exception_obj, exc_type, exc_tb):
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error_str = '{}'.format(str(exception_obj))
        error_details = '{} {} {}'.format(exc_type, fname, exc_tb.tb_lineno)

        error_document = {"erro": error_str, "detalhes": error_details, "data_e_hora": str(datetime.now())}
        return error_document
            
            


if __name__ == '__main__':
    pass
