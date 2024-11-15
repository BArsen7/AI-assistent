# AI-assistent
AI assistent for MEPHI students

## Файлы
1. Папка data - папка для подготовленных данных для модели
1.1. import_db.py - Скрипт для поиска информации в ВБД  
1.2. faiss_db_vk - ВБД на основе постов из групп: osomephi, mephi_official  
1.3. faiss_db_vk_large - ВБД на основе постов из групп: osomephi, mephi_official, vmephi, reactorclub, snomephi  
1.4. faiss_db_policy - ВБД на основе методички
2. Папка parse - папка с парсером и неподготовленными данными  
2.1. testApi.py - тестовый скрипт для работы с API ВК
2.2. parse-vk.py - скрипт для парсинга постов сообщества ВК  
2.3. cleaner.py - скрипт предобработки текста  
2.4. faiss-db-create.py - скипт для векторизации текста и создания векторной базы данных FAISS  
2.5. faiss_db_api.py - API на FastAPI для взаимодействия с векторной базой данных FAISS  
2.6. osomephi.csv - спарсенные данные из ОСО МИФИ  
2.7. reactorclub.csv - спарсенные данные из группы Реактор МИФИ  
2.8. snomephi.csv - спарсенные данные из СНО МИФИ  
2.9. vmephi.csv - спарсенные данные из группы МИФИ  
2.10. clean_data.csv - очищенные и подготовленные данные для создания ВБД  
3. Папка RAG - папка с RAG, скриптом для автоматического получения iam_token'a
3.1  RAG_with_api.py - API на FastAPI для взаимодействия с RAG
3.2  create_iam_token.py - скрипт для автоматического получения iam_token'a
3.3  keys.json - файл с авторизованными ключами, которые необходимы для получения iam_token'a

Ссылка на векторные базы данных : https://disk.yandex.ru/d/2-F--Aw44QbGjg

## Получение токена пользователя
1. Создать приложение по ссылке https://vk.com/editapp?act=create
   Выбрать Платформу Standalone-приложение и нажать на кнопку "Перейти в сервис"  
   ![image](https://github.com/user-attachments/assets/eca8855b-4897-40fd-a7dc-6ac772c4967c)
2. Выбрать платформу Web
3. Базовый домен и доверенный URL можно указать любые
4. Завершить создание приложения
5. Запомнить id приложения
   ![image](https://github.com/user-attachments/assets/7fd0c800-bc82-40e5-86c2-455a1d3528c8)
6. подставить id приложения, полученный на предыдущем шаге, вместо параметра {ID} в ссылку
   https://oauth.vk.com/authorize?client_id={ID}&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=friends,notify,photos,wall,email,mail,groups,stats,offline&response_type=token&v=5.74
7. Вставить ссылку в адресную строку браузера и перейти по ней
8. После всех манипуляций в адресной строке браузера будет находиться токен пользователя
   
