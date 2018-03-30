# coding: utf-8

from datetime import date
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


def generate_bot_text(db):
    td = date.today().replace(day=1)
    month_start = mktime(td.timetuple())
    return u'Cпасибо за покупку. Израсходовано: {} BYN'.format(round(db.stat_by_total_month(month_start), 2))


@bot.message_handler(content_types=["text"])
def any_msg(message):
    db = SQLighter(config.database_name)
    if not message.text.startswith('/'):
        keyboard = telebot.types.InlineKeyboardMarkup()
        note = consume_message(message)
        if not note:
            bot.send_message(message.chat.id, u'Введите корректно расход: "цена комментарий"')
        else:
            previous_expense = db.find_expense(note)
            if not previous_expense or len(previous_expense) > 1:
                for index, purch in enumerate(config.PURCHASES, start=1):
                    callback_button = telebot.types.InlineKeyboardButton(text=purch, callback_data=index)
                    keyboard.add(callback_button)
                bot.send_message(message.chat.id, u'"{}"'.format(message.text), reply_markup=keyboard)
            else:
                db.update_expense(message.message_id, previous_expense[0][0])
                bot.send_message(message.chat.id, generate_bot_text(db))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    db = SQLighter(config.database_name)
    db.update_expense(call.message.message_id - 1, call.data)
    if call.message:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=generate_bot_text(db)
        )


def is_correct_price(value):
    return bool(value) or isinstance(value, int) or isinstance(value, float)


def consume_message(message):
    purchase = message.text
    splitted = purchase.split()
    db = SQLighter(config.database_name)
    prise = splitted[0].replace(',', '.')
    if not is_correct_price(prise) or len(splitted) < 2:
        return None
    note = ''.join(splitted[1:])
    db.record_item(message.from_user.id, message.message_id, message.date, prise, note)
    db.close()
    return note

if __name__ == '__main__':
    bot.polling(none_stop=True)
