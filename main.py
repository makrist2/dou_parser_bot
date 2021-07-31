import telebot
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import regex as rx
import unicodedata
import logging
import time
import threading
import datetime
import config

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
req = Request(config.dou, headers=config.HEADERS)
page = urlopen(req).read()  # dou page
soup = BeautifulSoup(page, 'lxml')  # souping

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)


def events_updater():
    """
    Main logic of the program
    """
    while True:
        kinda_db_file = open('kindadb.txt', 'r+')
        kinda_db_lines = kinda_db_file.readlines()
        time_stored = datetime.datetime.fromisoformat(kinda_db_lines[0][0:len(kinda_db_lines[0]) - 1])
        time_now = datetime.datetime.now()
        time_delta = time_now - time_stored
        if len(kinda_db_lines) < 2 or time_delta.total_seconds() > 86400:                       # date check
            events_lst = []
            try:
                events = soup.find_all('article', class_='b-postcard')
                for event in events:
                    title = rx.sub(r'\p{C}', '', event.h2.a.text)
                    date = rx.sub(r'\p{C}', '', event.div.span.text)
                    link = event.a.get('href')
                    if title in events_lst:
                        continue
                    else:
                        events_lst.append({'Title': unicodedata.normalize("NFKD", title),
                                           'Date': unicodedata.normalize("NFKD", date),
                                           'Link': link,
                                           })
                if len(kinda_db_lines) < 2 or kinda_db_lines[1] != events_lst[0].get('Link'):   # link check
                    for event in events_lst:
                        bot.send_message(config.chat_id,
                                         f'Название: {event.get("Title")}\n'
                                         f'Дата: {event.get("Date")}\n'
                                         f'Ссылка: {event.get("Link")}')
                        kinda_db_file.close()
                        kinda_db_file = open('kindadb.txt', 'w')
                        kinda_db_file.writelines(str(datetime.datetime.now()) + '\n' + events_lst[0].get('Link'))
            except Exception as e:
                bot.send_message(config.owner_id, logger.error(e))
        kinda_db_file.close()
        time.sleep(5)


def background_worker(func):
    """
    Thread creator for keep logic running in BG
    :param func: events_updater
    """
    t1 = threading.Thread(target=func)
    t1.start()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Initial message handler
    :param message:
    """
    if str(message.from_user.id) == config.owner_id:
        last_date = datetime.datetime.now()
        last_link = ''
        bot.reply_to(message, "Howdy, how are you doing?")
        kinda_db = open('kindadb.txt', 'r+')                # initial data
        kinda_db.truncate(0)                                #
        kinda_db.write(str(last_date) + '\n' + last_link)   #
        kinda_db.close()                                    #

        background_worker(events_updater())                 # starting handler


bot.polling()
