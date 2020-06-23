# Coletor de Whatsapp - Relatório de Instalação

Passos que segui para fazer o coletor do monitor funcionar em minha máquina.

## Problemas Iniciais

Primeiramente, tive problemas para usar a biblioteca de coleta [webwhatsapi](https://github.com/mukulhase/WebWhatsapp-Wrapper) normalmente em um ambiente python em conjunto com o código de coleta do monitor.

Na minha primeira tentativa, criei um ambiente python2 e tentei instalar as bibliotecas necessárias, e já tive um problema aí. Não consegui achar as bibliotecas nas versões necessárias para rodar o código (a versão da lib webwhatsapi disponível no pypi está desatualizada). Mesmo assim, instalei as versões que consegui, e obtive um erro de compatibilidade entre o codigo da api e o selenium.

A partir daí, tentei mudar para um ambiente python3 e usar a versão mais nova da biblioteca, baixando o código fonte direto do github. Para não ter problemas de compatibilidade novamente, tentei usar o docker para encapsular as sessões do selenium e também o código do coletor. Essa foi a abordagem que deu mais certo até então.

## Setup

_Todos os passos foram testados em máquinas linux (um notebook com Ubunutu 20.04 e um Raspberry Pi 3B rodando Raspbian 10)._

Primeiramente, faça a instalação do Docker seguindo os seguintes [passos](https://docs.docker.com/engine/install/), e instale também o Docker Compose seguindo estes [passos](https://docs.docker.com/compose/install/).

Com o docker instalado, clone este repositório para sua máquina. Dentro da pasta criada, rode o comando `sudo docker-compose build` para que as imagens necessárias sejam criadas.

Em seguida, rode o comando `sudo docker-compose run --rm collector` para iniciar uma coleta (por padrão, fará uma coleta das mensagens de todos os grupos dos dias 26-05-2020 a 27-05-2020).

Mais informações sobre a necessidade de executar os comandos com privilégios `sudo` podem ser encontradas [aqui](https://docs.docker.com/engine/install/linux-postinstall/)

Na primeira vez que for executado, o coletor requisitará que você leia o codigo QR gerado pelo Whatsapp Web antes de começar a rodar. Para isso você tera que usar um cliente VNC para acessar o navegador utilizado pelo selenium, e conseguir ler o código (para isso usei o [RealVNC](https://www.realvnc.com/en/)). Com o cliente VNC aberto, basta conectar em `localhost:5900` para consultar visualmente o estado do navegador.

## Execução

### Input

{
"group_blacklist": ["groupA_id", "groupB_id"],
"user_blacklist": ["+99 99 999999999", "+11 11 111111111"],
"collection_mode": "period",
"start_date": "2020-06-01",
"end_date": "2020-06-10",
"collect_messages": true,
"collect_audios": true,
"collect_videos": true,
"collect_images": true,
"process_audio_hashes": true,
"process_image_hashes": true,
"process_video_hashes": true,
}

### Output

{
"mid" : "XXXXXX",
"gid" : "XXXXXX",
"group_name" : "XXXXXX",
"country" : "XXXXXX",
"sender" : "XXXXXX",
"date" : "XXXXXX",
"mediatype" : "XXXXXX",
"media_message" : "XXXXXX",
"content" : "XXXXXX",
"filename" : "XXXXXX",
"media_checksum": "XXXXXXXXXXXX",
"image_phash": "XXXXXXXXXXXX",
}

## Adendos

Alguns pontos que acho relevante levantar.

### Conversão para Python 3

Inicialmente o código do coletor estava escrito em python2, e como disse, tive problemas para utilizá-lo com versões mais novas da biblioteca.

Dessa forma, eu converti o código fonte para python3 utilizando a biblioteca [futurize](https://python-future.org/futurize.html). Ela passa por todo o código aplicando modificações para que se torne válido em Python 3, e também retro compatível com Python 2.

Além disso, tive que remover a dependência do django, que não possuia as funções de String utilizadas em python 3. No lugar, criei uma função simples que creio que faz a mesma coisa que essas outras funções.

Creio que essas mudanças não quebraram o funcionamento do coletor, mas creio que é válida uma inspeção mais a fundo sobre os possíveis problemas de compatibilidade.

### Outras modificações

No geral, a unica grande mudança que fiz foi comentar a linha que pega os metadados dos grupos, pois não entendi o que ela precisava para funcionar.

Também comentei ou removi algumas linhas que não estavam fazendo nada (no geral por conta do driver do selenium estar rodando no docker agora, e algumas coisas relacionadas a conversão de strings para unicode, que agora já são padrão unicode no python3).
