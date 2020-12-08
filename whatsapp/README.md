# Coletor de Whatsapp

Ferramenta de coleta de grupos públicos de Whatsapp desenvolvida para o Ministério Público de Minas Gerais. Realiza coleta de mensagens de texto, aúdios e demais mídias enviadas nos grupos monitorados, armazenando informações sobre os os grupos e seus participantes

## Instalação

_Todos os passos foram testados em máquinas linux (um notebook com Ubunutu 20.04 e um Raspberry Pi 3B rodando Raspbian 10)._

Primeiramente, faça a instalação do Docker seguindo os seguintes [passos](https://docs.docker.com/engine/install/), e instale também o Docker Compose seguindo estes [passos](https://docs.docker.com/compose/install/).

Com o docker instalado, clone este repositório para sua máquina. Dentro da pasta criada, rode o comando `sudo docker-compose build` para que as imagens necessárias sejam criadas.

Em seguida, como teste, rode o comando `sudo docker-compose run --rm collector` para iniciar uma coleta (por padrão, fará uma coleta das mensagens de todos os grupos dos dias 26-05-2020 a 27-05-2020).

Mais informações sobre a necessidade de executar os comandos com privilégios `sudo` podem ser encontradas [aqui](https://docs.docker.com/engine/install/linux-postinstall/)

Na primeira vez que for executado, o coletor requisitará que você leia o codigo QR gerado pelo Whatsapp Web antes de começar a rodar. Para isso você tera que usar um cliente VNC para acessar o navegador utilizado pelo selenium, e conseguir ler o código (para isso usei o [RealVNC](https://www.realvnc.com/en/)). Com o cliente VNC aberto, basta conectar em `localhost:5900` para consultar visualmente o estado do navegador.

## Utilização do docker

Para que a instalação e execução dos scripts de coleta sejam feitas de forma facilitada, optamos por utilizar a plataforma Docker para encapsular o código e suas dependências.

Docker é um software contêiner que fornece uma camada de abstração e automação para virtualização de sistema operacional no Windows e no Linux. O suporte para espaços de nomes do núcleo do Linux na maioria das vezes isola uma visão da aplicação do ambiente operacional, incluindo árvores de processo, rede, IDs de usuário e sistemas de arquivos montados.

A estrutura do programa é dividida em dois containers diferentes. O primeiro é um que roda o Selenium,, um framework criado para automatização de browsers, e que é utilizado pela biblioteca webwhatsapi, necessária para fazer a coleta das informações do whatsapp web. O segundo é o container do código em si, que guarda os scripts e comunica com o container do Selenium para fazer a coleta. A definição destes containers pode ser vista nos arquivos Dockerfile, e docker-compose.yml.

O arquivo Dockerfile descreve o container que contém o código do coletor. Ele define coisas como a versão do python a ser utilizada, a instalação de dependências e a cópia dos códigos em si. Mais detalhes podem ser vistos nos comentários feitos no arquivo.

O arquivo docker-compose.yml define como será feita a composição dos dois containers, criando a rede para que eles se comuniquem entre si, e definindo outras configurações individuais para cada um dos containers.

## Scripts:

O código do coletor é dividido em três scripts que são encapsulados em um container do Docker que por default tem o nome “collector”.

O arquivo docker-compose.yml define a relação deste container com o sistema operacional e o container do Selenium. Um ponto importante de ser notado nessa composição e a execução dos scripts:
Como os scripts são executados dentro de um container que se comporta como uma máquina virtual, eles só conseguem acessar pastas que estão dentro desta “máquina” (Isto inclui os arquivos de entrada e saída). Para fazer com que o código tenha acesso a pastas do sistema operacional do usuário, o arquivo docker-compose.yml define um espelhamento de pastas na seção ‘volumes’. Cada espelhamento está no formato “/pasta/do/sistema/operacional/local:/caminho/para/pasta/no/container”, que define que esta pasta local no Sistema Operacional será acessível dentro do container no caminho escolhido. Por padrão, estão definidas uma pasta ‘data’ para arquivos de saída do coletor, e config para guardar arquivos de configuração json que servem de entrada para o programa.

### get_messages.py

Define a classe “WhatsappCollector”, que encapsula o coletor de grupos do Whatsapp. Possui o método principal que realiza a leitura da entrada e faz a coleta das mensagens, mídias e notificações.

A execução deste script pode ser realizada da seguinte forma:

`docker-compose run --rm collector python get_messages.py`

### metadata_groups.py

Define uma biblioteca auxiliar que compreende funções que coletam metadados de todos os grupos que o usuário participa.

A execução deste script pode ser realizada da seguinte forma :

`docker-compose run --rm collector python metadata_groups.py`

### summarization_util.py

Define uma biblioteca auxiliar que compreende funções extras para realizar sumarização das mídias e mensagens de textos de um certo período.

A execução deste script pode ser realizada da seguinte forma :

`docker-compose run --rm collector python summarization_util.py`

## Classes

### Classe 'WhatsappCollector'

```
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
```

### Classe 'GroupMetadataCollector'

```
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
      com os parâmetros fornecidos na criação do objeto de coleta.s
```

### Classe 'SummarizationUtil'

```
  Biblioteca auxiliar que compreende funções extras para realizar a
  sumarização das mídias e mensagens de um certo período.

  Atributos
  -----------
  media_type : str
          Tipo de mídia para gerar a sumarização (images, audios, videos)
  comparison_method : str
          Metódo para calcular a similaridade/igualdade entre mídias (
          checksum, phash, jaccard).
  start_date : str
          Data de início da sumarização.
  end_date : str
          Data de fim da sumarização.
  messages_path : str
          Caminho em que estão salvos os arquivos de coleta por data.

  Métodos
  -----------
  generate_media_summarization()
      Faz a sumarização das mensagens de um certo tipo de mídia. Calcula
      informações como primeira vez em que a mídia foi compartilhada,
      quantas vezes foi compartilhada, em que grupos, por quais usuários,
      etc.
```

## Entrada

Abaixo, os parâmetros da entrada necessários para execução do coletor:

- collection_mode: Modo de coleção a ser utilizado ('period' ou 'unread').
- start_date: Data de início do período de coleta (Modo 'period').
- end_date: Data de término do período de coleta (Modo 'period').
- collect_messages: Se mensagens de texto devem ser coletadas durante a execução.
- collect_audios: Se áudios devem ser coletadas durante a execução.
- collect_videos: Se vídeos devem ser coletadas durante a execução.
- collect_images: Se imagens devem ser coletadas durante a execução.
- process_audio_hashes: Se hashes de áudios devem ser calculados durante a execução.
- process_image_hashes: Se hashes de imagens devem ser calculados durante a execução.
- process_video_hashes: Se hashes de vídeos devem ser calculados durante a execução.
- group_blacklist: Lista de grupos que devem ser excluídos da coleta
- user_blacklist: Lista de usuários que devem ser excluídos da coleta
- json_string: String contendo um json de configuração de execução. Individualmente, as opções presentes no arquivo sobescreveram os argumentos de linha de comando, caso eles sejam fornecidos.
- json: Caminho para um arquivo json de configuração de execução. Individualmente, as opções presentes no arquivo sobescreveram os argumentos de linha de comando, caso eles sejam fornecidos. Caso esse parâmetro seja utilizado, deve-se fornecer um arquivo .json com os parâmetros listados acima, dentro da pasta config.

## Saídas

É gerada uma pasta `data`, em que são armazenados os arquivos de saída da coleta. Dentro desta pasta, é gerado um log de erros (i.e. _log.txt_). Além disso, as demais informações são divididas em pastas, descritas abaixo:

- audio: Armazena os áudios coletados. O nome dos arquivos é um identificador único gerado pelo Whatsapp

- firefox*cache: Armazena o \_cache* do navegador utilizado para rodar a coleta

- groupID: Nesta pasta, são armazenados arquivos .json, nomeados com o identificador único de um grupo. Dentro de um .json qualquer, estão todas as mensagens coletadas para o grupo identificado no nome do aruqivo. Cada linha é um objeto json distinto. Os campos contidos em cada json estão descritos abaixo:

  - "message_id": Identificador único da mensagem
  - "group_id": Identificador único do grupo onde a mensagem foi enviada
  - "group_name": Nome do grupo onde a mensagem foi enviada
  - "country": País de origem do número que enviou a mensagem,
  - "sender": Número de telefone que enviou a mensagem,
  - "date": Data e hora de envio da mensagem,
  - "type": Tipo da mensagem, pode ser `text`, `image`, `sticker`, `video`, `audio` ou `ptt` (push-to-talk, outra forma de áudio) .
  - "file": Sinaliza se a mensagem vem acompanhada de algum arquivo, com o nome do arquivo armazenado. Caso não a mensagem não tenha um arquivo associado, este campo possui possui "<NoFile>" como valor.
  - "content": Texto da mensagem
  - "checksum": String gerado por checksum. Gerado apenas para mensagens de áudio, vídeo e imagem.
  - "phash": [phash](https://phash.org) gerado apenas para imagens

- image: Armazena as imagens coletadas. O nome dos arquivos é um identificador único gerado pelo Whatsapp

- mids: Armazena, por grupo, arquivos que registram o id único de cada mensagem e o horário em que a mensagem foi enviada. Estes arquivos são utiliados para retomar a coleta da última mensagem coletada, para evitar duplicatas e acelerar a execução


- notifications: notificações são as atividades internas no grupo que modificam de alguma forma em sua estrutura. Uma notificação é gerada, por exemplo, quando um usuário entra/sai ou é adicionado/removido de um grupo, quando alguém modifica o título, imagem ou descrição do grupo ou outras atividades do tipo mais estruturais. Nesta pasta, é armazenado, para grupo, um arquivo .json com as seguintes informações, para cada notificação do grupo:
  - "message_id": identificador unico da mensagem,
  - "group_id": identificador unico do grupo,
  - "timestamp": [Unix time](https://en.wikipedia.org/wiki/Unix_time) de quando a notificacao ocorreu,
  - "date": Data e horario de quando a notificacao ocorreu,
  - "sender": Usuário autor da notificação,
  - "type": Tipo da notificação, dado pelo próprio sistema do WhatsApp. esses tipos podem ser: 

        - "call_log": notificações relacionadas com ligação;
        - "e2e_notification: notificações relacionadas a criptografia
        - "gp2": notificação de movimentação nos grupos
  - "subtype": Qual tipo de notificação aconteceu. É uma especificação do campo anterior, dando mais detalhes do tipo de notificação. Este campo pode conter os seguintes valores:,
        - "miss":  notifiacação para chamadas perdidas.
        - "encrypt": notificação sobre criptografia da mensagem.
        - "invite":  notificação de quando um novo usuário entra a partir do link de convite do grupo.
        - "create":  notificação informado a criação do grupo.
        - "add": notificação indicando que um novo usuário foi adicionado ao grupo por algum administrador.
        - "remove": notificação indicando que algum membro foi removido (banido) do grupo por algum administrador.
        - "leave": notificação indicando que algum usuário deixou o grupo.
        - "description": notificação informando que algum membro modificou a descrição do grupo.
  - "contact": Nome do grupo onde ocorreu a notificacao,
  - "recipient":Usuário alvo da notificação (utilizado para notificações de adição, remoção de membros do grupo),
  - "from": Número de celular de quem recebeu a notificação. (O próprio celular usado na coleta).

- text: Dentro desta pasta, são armazenados arquivos com todas as mensagems coletas, separadas por dia. Cada dia tem seu próprio arquivo, seguindo o padrão `AllMessages_YYYY_MM_DD.txt`. Dentro destes arquivos, cada linha é um objeto json que representa uma mensagem. Nestes objetos, estão armazenadas as seguintes informações:

  - "message_id": Identificador único da mensagem
  - "group_id": Identificador único do grupo onde a mensagem foi enviada
  - "group_name": Nome do grupo onde a mensagem foi enviada
  - "country": País de origem do número que enviou a mensagem,
  - "sender": Número de telefone que enviou a mensagem,
  - "date": Data e hora de envio da mensagem,
  - "type": Tipo da mensagem, pode ser `text`, `image`, `sticker`, `video`, `audio` ou `ptt` (push-to-talk, outra forma de áudio).
  - "file": Sinaliza se a mensagem vem acompanhada de algum arquivo, com o nome do arquivo armazenado. Caso não a mensagem não tenha um arquivo associado, este campo possui possui "<NoFile>" como valor.
  - "content": Texto da mensagem

- video: Armazena os vídeos coletados. O nome dos arquivos é um identificador único gerado pelo Whatsapp
