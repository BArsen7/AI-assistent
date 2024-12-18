import pandas as pd
import re


data = pd.read_csv('parse-data.csv')
rewrite = False # False - дозапись в файл, True - перезапись файла
del_link = False # False - оставляем ссылки в тексте постов, True - удаляем ссылки из постов
data.drop_duplicates(subset='text', keep='first', inplace=True, ignore_index=True)
array = []

for index, row in data.iterrows():
    #print(row['i'], row['time'], row['id'], row['text'])
    if row['text']!=row['text']: continue # пропускаем записи без текста
    if del_link:
        y = ' '.join(re.sub("(@[А-Яа-яA-Za-z0-9]+)|([^0-9A-Za-zА-Яа-я \t])|(\w+:\/\/\S+)"," ",row['text']).split())
    else:
        y = ' '.join(re.sub(r"(@[А-Яа-яA-Za-z0-9]+)|([^0-9A-Za-zА-Яа-я \t:/.\-_?&=%])", " ", row['text']).split())
    array.append([row['i'], row['time'],row['id'], [y]])



new_data = pd.DataFrame(array, columns = ['index', 'time', 'id', 'c-text'])

if not(rewrite): 
    old_data = pd.read_csv('clean_data.csv')
    new_data = pd.concat([old_data, new_data], ignore_index=True)

new_data.to_csv('clean_data.csv', index=False)
