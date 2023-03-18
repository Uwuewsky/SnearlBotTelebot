import os
import sys
import json

#Либо разбить эти функции на разные файлы (для записи в блеклист и войслист) либо засунуть все в классы
def write_to_voices():
    with open(voices_filename, mode="w", encoding='utf8') as f:
        json.dump(voicelist, f, indent='\t', ensure_ascii=False)

def read_from_voices():
    if not os.path.isfile(voices_filename) or os.path.getsize(voices_filename) == 0:
        return []
    with open(voices_filename, mode="r", encoding='utf8') as f:
        return json.load(f)

voices_filename = os.path.join(sys.path[0], 'services\\voices.json') #В репозитории вместо файла со всеми данными
voicelist = read_from_voices()                                       #есть файл voices_example.json


#Запись в блеклист
def write_to_blacklist():
    with open(blacklist_filename, mode="w", encoding='utf8') as f:
        json.dump(blacklist, f, indent='\t', ensure_ascii=False)

#Чтение из блеклиста
def read_from_blacklist():
    if not os.path.isfile(blacklist_filename):
        return []
    with open(blacklist_filename, mode="r", encoding='utf8') as f:
        return json.load(f)

blacklist_filename = os.path.join(sys.path[0], 'services\\blacklist.json')#В репозитории вместо файла со всеми данными
voicelist = read_from_voices()                                            #есть файл blacklist_example.json
blacklist = read_from_blacklist()