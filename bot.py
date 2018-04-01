# coding: utf-8

import re
from datetime import date, datetime
from time import mktime
import telebot
import config
from database_api import SQLighter
from credentials import token

bot = telebot.TeleBot(token)


# TODO: сделать приложением, которое работает во взаимодействии как с телеграмом, так и имеет веб-морду
# TODO: сделать добавление токена Telegram при запуске скрипта
# TODO: добавить тестирование
# TODO: миграция и создания БД файлика автоматом
# TODO: сделать кнопки в клаве
# TODO: логика бонусов
# TODO: логика ведения баланса (ввод источников доходов с описанием)
# TODO: парсинг чеков
# TODO: метрики и стата по видам
# TODO: клепание отчета excel
# TODO: расход по стройке (нужно сразу конвертер валют делать)
# TODO: задолженноть по стройке
# TODO: уведомление о накопленной сумме
# TODO: сравнительный анализ
# TODO: построение графиков
# TODO: возможность редактирования (при неудачном посте или выборе неверной категории)
# TODO: попробовать использовать API ПриорБанка
# TODO: рефакторинг оптимальности запросов
# TODO: возможность просмотра статы за указанный период времени и сравнение с аналогичными тремя периодами
# TODO: возможность переноса платежа на следующий месяц

PRIOR_RE_STR = r'^Priorbank\. Karta (?:\d\*{3}\d{4}). (?P<datetime>.{17}). ' \
               r'Oplata (?P<prise>\d*[.,]?\d*) (?P<currency>[\w+]{3}). (?P<place>.*). Dostupno:'
PRIOR_SMS_RE = re.compile(PRIOR_RE_STR)
PRISE_RE = re.compile(r'^\d+?\.\d+?$')
PRIOR_DATETIME_FORMAT = '%d-%m-%y %H:%M:%S'


def generate_bot_text(db):
    td = date.today().replace(day=1)
    month_start = mktime(td.timetuple())
    return u'Cпасибо. Израсходовано за месяц: {} BYN'.format(round(db.stat_by_total_month(month_start), 2))


@bot.message_handler(regexp=PRIOR_RE_STR)
def prior_msg(message):
    db = SQLighter(config.database_name)
    response = consume_prior(message, db)
    for message_timestamp, user_note in response:
        keyboard = telebot.types.InlineKeyboardMarkup()
        previous_expense = db.find_prior_expense(message_timestamp)
        if not previous_expense or len(previous_expense) > 1:
            for index, purch in enumerate(config.PURCHASES, start=1):
                callback_button = telebot.types.InlineKeyboardButton(text=purch, callback_data=index)
                keyboard.add(callback_button)
            bot.send_message(message.chat.id, u'"{}"'.format(user_note), reply_markup=keyboard)
        else:
            db.delete_expense_by_timestamp(message_timestamp)
            bot.send_message(message.chat.id, u'Данный расход уже был учтен ранее')


@bot.message_handler(content_types=["text"])
def any_msg(message):
    db = SQLighter(config.database_name)
    if not message.text.startswith('/'):
        keyboard = telebot.types.InlineKeyboardMarkup()
        note, user_note = consume_message(message, db)
        if not note:
            bot.send_message(message.chat.id, u'Введите корректно расход: "цена комментарий"')
        else:
            previous_expense = db.find_expense(note)
            if not previous_expense or not previous_expense[0][0] or len(previous_expense) > 1:
                for index, purch in enumerate(config.PURCHASES, start=1):
                    callback_button = telebot.types.InlineKeyboardButton(text=purch, callback_data=index)
                    keyboard.add(callback_button)
                bot.send_message(message.chat.id, u'"{}"'.format(user_note), reply_markup=keyboard)
            else:
                db.update_expense(message.message_id, previous_expense[0][0])
                bot.send_message(message.chat.id, generate_bot_text(db))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    db = SQLighter(config.database_name)
    if call.data == str(len(config.PURCHASES)):
        db.delete_expense_by_id(call.message.message_id - 1)
        if call.message:
            bot.delete_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )
            bot.send_message(call.message.chat.id, u'не засчитано из-за отмены ввода данных')
    else:
        db.update_expense(call.message.message_id - 1, call.data)
        if call.message:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=generate_bot_text(db)
            )


def is_number_regex(s):
    if PRISE_RE.match(s) is None:
        return s.isdigit()
    return True


def get_parts(line):
    parts = line.split()
    prise = parts[0].replace(',', '.').replace(u'ю', u'.')
    note = ' '.join(parts[1:])
    return prise, note


def consume_prior(message, db):
    purchase = message.text
    messages = filter(None, purchase.split('\n'))
    result = []
    for purchase in messages:
        prior_sms = PRIOR_SMS_RE.match(purchase)
        message_timestamp = mktime(datetime.strptime(prior_sms.group('datetime'), PRIOR_DATETIME_FORMAT).timetuple())
        raw_note = prior_sms.group('place')
        user_note = u'{}: {}'.format(prior_sms.group('place'), prior_sms.group('prise'))
        db.record_item(
            message.from_user.id,
            message.message_id,
            message_timestamp,
            prior_sms.group('prise'),
            raw_note
        )
        result.append((message_timestamp, user_note),)
    return result


def consume_message(message, db):
    purchase = message.text
    message_prise, raw_note = get_parts(purchase)
    user_note = u'{}: {}'.format(raw_note, message_prise)
    if not is_number_regex(message_prise) or not raw_note:
        return None, None
    message_timestamp = message.date
    db.record_item(
        message.from_user.id,
        message.message_id,
        message_timestamp,
        message_prise,
        raw_note
    )
    return raw_note, user_note

if __name__ == '__main__':
    bot.polling(none_stop=True)
