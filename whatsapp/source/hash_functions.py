__author__ = "Philipe Melo"
__email__ = "philipe@dcc.ufmg.br"

from PIL import ImageFile
from PIL import Image

import os
import hashlib
import imagehash

ImageFile.LOAD_TRUNCATED_IMAGES = True


def hamming_distance(hash1, hash2, treshold=16):
    """
    Calcula a distância de hamming de dois hashs
    """
    hamming = hash1.hammingDistance(hash2)
    if hamming <= treshold:
        return True, hamming
    else:
        return False, hamming


def getCheckSum(filename):
    """
    Realiza o checksum de um arquivo e retorna
    a string de saída gerada
    """
    check = ''
    if os.path.isfile(filename):
        filep = open(filename, 'rb').read()
        check = hashlib.md5(filep).hexdigest()
    return str(check)



def is_image(filename):
    """
    Confere se o arquivo recebido como parâmetro
    é uma imagem. Realiza esta tarefa conferindo
    a extensão do arquivo
    """
    f = filename.lower()
    return f.endswith(".png") or f.endswith(".jpg") or \
        f.endswith(".jpeg") or f.endswith(".bmp") or f.endswith(".gif") or '.jpg' in f


def get_hash_from_method(filename, method):
    """
    Recebe um arquivo e um método de hashing. Retorna
    o hash gerado.
    """
    hash = ''
    hash_function = get_hash_func(method)
    try:
        hash = hash_function(filename)
    except:
        try:
            hash = hash_function(Image.open(filename))
        except Exception as e:
            print('Problem:', e, 'with', filename)
    return str(hash)


def get_hash_func(hashmethod):
    """
    Recebe uma string que representa um método de hashing.
    Dada a string, retorna o método correspondente das
    bibliotecas
    """
    if hashmethod == 'ahash':
        hashfunc = imagehash.average_hash
    elif hashmethod == 'phash':
        hashfunc = imagehash.phash
    elif hashmethod == 'dhash':
        hashfunc = imagehash.dhash
    elif hashmethod == 'whash-haar':
        hashfunc = imagehash.whash
    elif hashmethod == 'whash-db4':
        hashfunc = lambda img: imagehash.whash(img, mode='db4')
    elif hashmethod == 'checksum':
        hashfunc = getCheckSum
    else:
        hashfunc = imagehash.phash
    return hashfunc
