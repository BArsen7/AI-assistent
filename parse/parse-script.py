import requests
import json
import time
from openpyxl import Workbook

# переменные 
TOKEN_USER = #токен пользователя
VERSION = 5.131 # используемая версия апи
DOMAIN =  'mephi_official' #имя сообщества из адресной строки

array = []
date =  time.time()
wb= Workbook()
ws=wb.active
i = 0




while date > 1693515599: #парсинг с первого сентября 2023 года 1693515599
	# через api vk вызываем статистику постов
	response = requests.get('https://api.vk.com/method/wall.get',
	params={'access_token': TOKEN_USER,
        	'v': VERSION,
        	'domain': DOMAIN,
		'offset': i,
        	'count': 100,
        	'filter': str('owner')})

	data = response.json()['response']['items']
	print("получено 100 записей")
	for j in range(100):
		date = data[j]['date']
		#print(i*100+j, time.ctime(date)) #, data[i*100+j]['text'])
		ws.append( [i*100+j,time.ctime(date), data[j]['text']]) # если заменить ws на array, значения будут сохраняться в соответствующем массиве
	i+=1
	wb.save(f"{DOMAIN}.xlsx")



