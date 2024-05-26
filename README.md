# Python Meetup Бот: Руководство по использыванию и документация
## Оглавление
- [Описание проекта](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#описание-проекта)
- [Роли в боте](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#роли-в-боте)
  - [Слушатель](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#слушатель)
  - [Спикер](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#спикер)
  - [Организатор](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#организатор)
- [Что понадобиться?](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#что-понадобится)
  - [Предварительные требования](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#предворительные-требования)
  - [Установка зависимостей](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#установка-зависимостей)
  - [Переменные окружения](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#переменные-окружения)
  - [Дополнительные требования](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#дополнительные-требования)
  - [Запустить миграцию](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#запустить-миграцию)
  - [Создать суперпользователя](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#создать-суперпользователя) 
- [Как запустить?](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#как-запустить)
  - [Запуск админ-панели](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#запуск-админ-панели)
  - [Запуск бота](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#запуск-бота)
- [Админ-панель](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#админ-панель)
- [Основные скрипты](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#основные-скрипты)
- [Цели проекта](https://gist.github.com/18372738/4c162188e895e5461449724dc529234a#цели-проекта)
### Описание проекта
Бот для организации, управления и просмотра мероприятий. Бот предоставляет пользователям три роли на выбор: слушатель, спикер, организатор 
### Роли в боте
#### Слушатель 
Данная роль позволяет просматривать запланированные мероприятия, увидеть какой спикер сейчас выступает, возможность задать вопрос спикеру во время и после выступления, и получить обратную связь.
#### Спикер
Данная роль позволяет оставить заявку, если у вас есть доклад и вы хотите выступить на мероприятии. Увидеть все вопросы, которые задали слушатели. Уведомлять о начале и завершении своего выступления. Просматривать запланированные мероприятия.
#### Организатор
Данная роль позволяет перейти к админ-панели, где сможет организовывать мероприятия, просматривать новых спикеров, управлять базой данных. Для работы с админ-панелью понадобиться логин и пароль.
### Что понадобится?
#### Предварительные требования
Скачайте или склонируйте репозиторий на свой компьютер.
Python3 должен быть уже установлен. 
#### Установка зависимостей
Используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```
#### Переменные окружения
Создайте файл ```.env``` в вашей директории проекта, откройте его в любом текстовом редакторе. Вам понадобятся следующие переменные окружения:
```
TELEGRAM_BOT_TOKEN=Токен вашего бота
```
#### Доплнительные требования
Создать телеграм бота и получить токен. Для регистрации и получения токена, нужно написать в [@BotFather](https://t.me/BotFather)
```
/newbot - регистрация нового бота
/token - получить токен бота 
```
#### Запустить миграцию
Для настройки базы данных SQLite
```bush
python manage.py migrate
```
#### Создать суперпользователя 
Для получения логина и пароля от админ-панели
```bush
python manage.py createsuperuser
```
При запуске команды вам понадобиться ввести данные (логин, E-mail, пароль)
### Как запустить 
#### Запуск админ-панели 
```bush
python manage.py runserver
```
При запуске команды выводится url-адрес в конце которого нужно добавить ```/admin```, получится ссылка типа ```http://127.0.0.1:8000/admin```, которая откроет страницу с админ-панелью, где нужно будет ввести логин и пароль, который указывали при создании суперпользователя.
#### Запуск бота
```bush
python bot.py
```
При запуске команды, если все шаги сделали правильно, бот готов к работе.


### Админ-панель

После запуска админ-понели откроется окно в котором отображены все таблицы

![Снимок экрана 2024-05-26 155039](https://gist.github.com/assets/133884450/c60aeec9-6fe8-45e3-8f34-e885b952bdc5)

Админка Django позволяет управлять данными бота. Просматривать данные таблицы, вносить изменения, удалять. В данном боте представлены 4 таблицы:

1. Events - мероприятия, в данной таблице 5 полей (Название, Адрес, Время начала, Время окончания, Спикеры). Данные в эту таблицу вносятся вручную организатором или администратором.
2. New speakers - новые спикеры, в данной таблице 4 поля (ФИО, Тема доклада, Номер телефона, Telegram ID). После того как пользователь ввёл свои данные через бота, данные сохраняются автоматически в эту таблицу.
3. Questions - вопросы и ответы, в данной таблице 3 поля (Спикер. Вопрос, Ответ). Значения в поля "Спикер" и "Вопрос" добавляются автоматически, когда слушатель напишет свой вопрос через бота выбрав нужного спикера. В поле "Ответ" значения добавляются автоматически когда спикер ответил на вопрос.
4. Speakers - спикеры, в данной таблице 5 полей (ФИО, Тема доклада, Номер телефона, Время начала, Время окончания, Telegram ID). Данные в эту таблицу вносятся вручную организатором или администратором.
### Основные скрипты
- [bot.py](https://github.com/18372738/bot_event/blob/main/bot.py)
- [models.py](https://github.com/18372738/bot_event/blob/main/event_models/models.py)
### Цели проекта
Проект написан в образовательных целях.



