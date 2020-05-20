import requests

from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

from wikip import search_wiki

from datetime import datetime
import json

APIT = "trnsl.1.1.20200515T163846Z.32ef820fdb044ba9.621f050582c0e43ce22cd11c6e06ba408895f327"

with open('token.txt', 'r') as fl:
    TOKEN = fl.read().strip()

reply_keyboard = [['/address', '/phone'],
                  ['/site', '/work_time']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

lang = ['en-ru', 'ru-en', 'de-ru', 'ru-de', 'fr-ru', 'ru-fr']


def startmenu(update, context):
    keyboard = [[InlineKeyboardButton(lang[i], callback_data=i)]
                for i in range(len(lang))]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Выберите направление перевода:', reply_markup=reply_markup)


def starttranslate(update, context):
    context.user_data['lang'] = "en-ru"
    update.message.reply_text("Переводчик с русского на английский")


def translate(update, context):
    text_out = "Для начала работы переводчика введите /starttrans"
    if "lang" in context.user_data:
        params = {"key": APIT,
                  "text": ' '.join(context.args),
                  "lang": context.user_data['lang']}
        r = requests.get(f"https://translate.yandex.net/api/v1.5/tr.json/translate", params=params)
        text_out = ' '.join(json.loads(r.text)["text"])

    update.message.reply_text(text_out)


def time(update, context):
    dtn = datetime.now()
    update.message.reply_text(dtn.strftime("%H:%M"))


def date(update, context):
    dtn = datetime.now()
    update.message.reply_text(dtn.strftime("%d.%m.%Y"))


def close_keyboard(update, context):
    update.message.reply_text("Ok", reply_markup=ReplyKeyboardRemove())


def echo(update, context):
    print(update)
    text_in = update.message.text
    text_out = "Эхо: " + text_in
    if text_in.lower() in ['привет', "здаров", "хай"]:
        text_out = "И тебе привет, человек"
    if text_in.lower() in ["hi", "hello", "good morning"]:
        text_out = "I'm dont speak English very well. I am speak Russia."
    update.message.reply_text(text_out)

def voice(update, context):
    update.message.reply_text("Я вас не могу слышать, я бот и у меня нет ушей :) ....")


def start(update, context):
    update.message.reply_text("Привет, я Эхо бот, справочник. Могу здороваться и повторять то что ты напишешь.",
                              reply_markup=markup)


def help(update, context):
    update.message.reply_text("""
    /help - вызов помощи
    /start - запуск меню
    /adress - получить адрес компании
    /work_time - часы работы
    /phone - телефон компании
    /site - сайт компании
    /close - убрать меню
    /geobot <адрес> - получить карту по <адресу>
    /wiki <запрос> - получить данные из википедии по <запросу>
    /date - текущая дата
    /time - текущее время сервера
    /starttrans - запуск переводчика EN-RU
    /translate <фраза для перевода на английском>  - переводчик
    /startmenu - вызов меню выбора направления перевода (не работает!)    
    """)


# Напишем соответствующие функции.
def work_time(update, context):
    update.message.reply_text("Врем работы с 9:00 до 19:00. Без перерыва. Ежедневно.")


def address(update, context):
    update.message.reply_text("Адрес: г. Москва, ул. Льва Толстого, 16")


def phone(update, context):
    update.message.reply_text("Телефон: +7(495)776-3030")


def site(update, context):
    update.message.reply_text("Сайт: http://www.yandex.ru/company")


# Получаем параметры объекта для рисования карты вокруг него.
def get_ll_span(address):
    toponym = address
    if not toponym:
        return None, None

    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Долгота и Широта :
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    # Собираем координаты в параметр ll
    ll = ",".join([toponym_longitude, toponym_lattitude])

    # Рамка вокруг объекта:
    envelope = toponym["boundedBy"]["Envelope"]

    # левая, нижняя, правая и верхняя границы из координат углов:
    l, b = envelope["lowerCorner"].split(" ")
    r, t = envelope["upperCorner"].split(" ")

    # Вычисляем полуразмеры по вертикали и горизонтали
    dx = abs(float(l) - float(r)) / 2.0
    dy = abs(float(t) - float(b)) / 2.0

    # Собираем размеры в параметр span
    span = "{dx},{dy}".format(**locals())

    return (ll, span)


def geocoder(update, context):
    addr = ' '.join(context.args)
    update.message.reply_text("Ждите карту для адреса => " + addr)

    geocoder_uri = geocoder_request_template = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(geocoder_uri, params={
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": addr
    })

    toponym = response.json()["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    ll, spn = get_ll_span(toponym)
    # Можно воспользоваться готовой функцией,
    # которую предлагалось сделать на уроках, посвящённых HTTP-геокодеру.

    static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll}&spn={spn}&l=map"
    context.bot.send_photo(
        update.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
        # Ссылка на static API, по сути, ссылка на картинку.
        # Телеграму можно передать прямо её, не скачивая предварительно карту.
        static_api_request,
        caption="Нашёл!"
    )


def wikipedia(update, context):
    poisk = ' '.join(context.args).strip()
    update.message.reply_text("Ищем данные в Википедии для => " + poisk)
    w = search_wiki(poisk)
    print(2, len(w))
    if w:
        update.message.reply_text(w[:4000])
    else:
        update.message.reply_text("В Википедии нет данных по термину" + poisk)


def word(update, context):
    poisk = context.args[0]
    update.message.reply_text("Ищем данные для => " + poisk)


def main():
    print("Бот MItest запущен....")
    REQUEST_KWARGS = {'proxy_url': 'socks5://127.0.0.1:9150', }
    updater = Updater(TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)
    # updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("address", address))
    dp.add_handler(CommandHandler("phone", phone))
    dp.add_handler(CommandHandler("site", site))
    dp.add_handler(CommandHandler("work_time", work_time))
    dp.add_handler(CommandHandler("close", close_keyboard))
    dp.add_handler(CommandHandler("geobot", geocoder))
    dp.add_handler(CommandHandler("wiki", wikipedia))
    dp.add_handler(CommandHandler("time", time))
    dp.add_handler(CommandHandler("date", date))
    dp.add_handler(CommandHandler("starttrans", starttranslate))
    dp.add_handler(CommandHandler("translate", translate))
    dp.add_handler(CommandHandler("startmenu", startmenu))

    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.voice, voice))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
