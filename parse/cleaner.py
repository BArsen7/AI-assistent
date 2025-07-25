import pandas as pd
import re
import argparse 


#========================================    Аргументы командной строки    ========================================
parser = argparse.ArgumentParser(description="Очистка спарсенных постов.")  
parser.add_argument("-r", action="store_true", help="Rewrite. Если указан этот аргумент, скрипт перезаписывает файл вывода, если аргумент не указан, скрипт дозаписывает существующий файл.")  
parser.add_argument("-l", action="store_true", help="Del_Links. Если указан этот аргумент, скрипт удаляет все ссылки из постов, если аргумент не указан, скрипт сохраняет ссылки.")  
parser.add_argument("--min_len", type=int, default=7, help="Минимальное колличество слов в посте. По умолчанию - 7.")
args = parser.parse_args()




data = pd.read_csv('parse-data.csv')



# ==========================================    Очистка     ====================================================

data.drop_duplicates(subset='text', keep='first', inplace=True, ignore_index=True)
array = []

for index, row in data.iterrows():
    #print(row['i'], row['time'], row['id'], row['text'])
    if row['text']!=row['text']: continue # пропускаем записи без текста
    if args.l:
        print("Удаление ссылок")
        y = ' '.join(re.sub("(@[А-Яа-яA-Za-z0-9]+)|([^0-9A-Za-zА-Яа-я \t])|(\w+:\/\/\S+)"," ",row['text']).split())
    else:
        print("Сохранение ссылок")
        y = ' '.join(re.sub(r"(@[А-Яа-яA-Za-z0-9]+)|([^0-9A-Za-zА-Яа-я \t:/.\-_?&=%])", " ", row['text']).split())
    if len(y.split())>=args.min_len:    
        array.append([row['i'], row['time'],row['id'], [y]])



new_data = pd.DataFrame(array, columns = ['index', 'time', 'id', 'c-text'])

if not(args.r): #rewrite
    old_data = pd.read_csv('clean_data.csv')
    new_data = pd.concat([old_data, new_data], ignore_index=True)

new_data.to_csv('clean_data.csv', index=False)
