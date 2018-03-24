# coding: utf-8

import telebot
import config
from database_api import SQLighter

bot = telebot.TeleBot(config.token)

PURCHASES = (u'коммуналка', u'магазин', u'сборы', u'бытовуха', u'здоровье',
             u'транспорт', u'красота', u'развлекушки', u'покупки', u'Глеб', u'иные расходы')


@bot.message_handler(content_types=["text"])
def any_msg(message):
    if not message.text.startswith('/'):
        keyboard = telebot.types.InlineKeyboardMarkup()
        consume_message(message)
        for index, purch in enumerate(PURCHASES, start=1):
            callback_button = telebot.types.InlineKeyboardButton(text=purch, callback_data=index)
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, u'статья расходов', reply_markup=keyboard)
    elif message.text == '/migrate':
        db = SQLighter(config.database_name)
        db.set_up_tables()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    db = SQLighter(config.database_name)
    db.update_expense(call.message.message_id - 1, call.data)
    if call.message:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=u'Cпасибо за покупку. В этом месяце потрачено: {} BYN'.format(db.stat_by_total())
        )


def consume_message(message):
    purchase = message.text
    splitted = purchase.split()
    db = SQLighter(config.database_name)
    prise = splitted[0].replace(',', '.')
    note = ''.join(splitted[1:])
    db.record_item(message.from_user.id, message.message_id, message.date, prise, note)
    db.close()

if __name__ == '__main__':
    bot.polling(none_stop=True)
