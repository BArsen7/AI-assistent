import requests
import json
import time
from openpyxl import Workbook

# переменные 
TOKEN_USER =  #токен пользователя
VERSION = 5.131 # используемая версия апи
DOMAIN =  'mephi_official' #имя сообщества из адресной строки

array = []
date =  time.time()
wb= Workbook()
ws=wb.active
i = 1
while date > 1693515599: #парсинг с первого сентября 2023 года 1693515599
	# через api vk вызываем статистику постов
	response = requests.get('https://api.vk.com/method/wall.get',
	params={'access_token': TOKEN_USER,
        	'v': VERSION,
        	'domain': DOMAIN,
        	'count': i,
        	'filter': str('owner')})

	data = response.json()['response']
	date = data['items'][len(data['items'])-1]['date']
	#print (data['count'], time.ctime(data['items'][len(data['items'])-1]['date']), '\n', data['items'][len(data['items'])-1]['text'] )
	ws.append( [i,time.ctime(date), data['items'][len(data['items'])-1]['text']]) # если заменить ws на array, значения будут сохраняться в соответствующем массиве
	print(i, time.ctime(date))
	i+=1
wb.save(f"{DOMAIN}.xlsx")


