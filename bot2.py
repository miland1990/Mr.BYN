# coding: utf-8
from __future__ import unicode_literals
from collections import namedtuple
from datetime import datetime
from sqlalchemy.sql import column
from sqlalchemy.orm.query import Query
from sqlalchemy.sql import func

import telebot

from credentials import token
from constants import RE_SIMPLE, RE_SIMPLE_STR, CURRENCY_DEFAULT, REPLY_EXPENSES, SIMPLE_TYPE, \
    NOTES_NEVER_NEED_MENU, EXPENSES
from utils import authorise
from models import Purchase, Conversation
from database import db_make_session

bot = telebot.TeleBot(token)

_simple_input = namedtuple('_simple_input', 'prise,currency,note,expense_id,position') # лучше классами
_prior_sms_input = namedtuple('_prior_sms_input', 'epoch,prise,currency,note')


@bot.message_handler(commands=[u'stat'])
@authorise
def current_stats(message):
    session = db_make_session()
    last_conversation = session.query(Conversation).all()[-1]
    for purchase in last_conversation.purchases:
        bot.edit_message_text('ura', message.chat.id, purchase.bot_message_id)
    bot.edit_message_text('total', message.chat.id, last_conversation.bot_message_id)


def create_conversation(session):
    conversation = Conversation()
    session.add(conversation)
    session.commit()
    return conversation

def _validate_currency_code(code, faked_byn=True):
    # в библиотеках используется старая сигнатура валюты белорусского рубля
    # эта функция адаптирует код валюты белорусского рубля на противоположный и делает его в upper'e
    if faked_byn:
        if not code or code == 'BYN':
            return CURRENCY_DEFAULT
        else:
            return code.upper()
    else:
        if not code or code == CURRENCY_DEFAULT:
            return 'BYN'
        else:
            return str(code).upper()


def _validate_prise(prise):
    return prise.replace("ю", ".").replace(",", ".")


def create_purchases(session, conversation, message, purchases, status=Purchase.KIND_SIMPLE):
    purchases_items = []
    for purchase_info in purchases:
        purchase = Purchase(
            user_message_id=message.message_id,
            conversation_id=conversation.id,
            position=purchase_info.position,
            status=status,
            currency=_validate_currency_code(purchase_info.currency),
            user_id=message.from_user.id,
            epoch=datetime.fromtimestamp(message.date),
            prise=_validate_prise(purchase_info.prise),
            note=purchase_info.note,
            expense_id=purchase_info.expense_id
        )
        purchases_items.append(purchase)
    session.add_all(purchases_items)
    session.commit()


def guess_expense(session, note):
    for fragment_info in NOTES_NEVER_NEED_MENU:
        # TODO: подумать на case-sensivity (пока не приводит к какому-либо регистру)
        if fragment_info[0] in note:
            return fragment_info[1]
    previous_purchases = session.query(Purchase).filter(
        column('expense_id').isnot(None),
        column('note').is_(note),
    ).all()
    if len(previous_purchases) > 1:
        return previous_purchases[-1].expense_id


def get_callback_reply_markup(position, message_id, callback_type):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for expense_id, button_name in REPLY_EXPENSES:
        data = f'{callback_type}|{message_id}|{position}|{expense_id}'
        callback_button = telebot.types.InlineKeyboardButton(text=button_name, callback_data=data)
        keyboard.add(callback_button)
    return keyboard


@bot.message_handler(regexp=RE_SIMPLE_STR)
@authorise
def simple_user_input(message):
    session = db_make_session()
    conversation = create_conversation(session)

    purchases = []
    for position, info in enumerate(RE_SIMPLE.finditer(message.text), start=1):
        purchases.append(
            _simple_input(
                info.group('price'),
                info.group('currency'),
                info.group('note'),
                guess_expense(session, info.group('note')),
                position
            )
        )
    create_purchases(session, conversation, message, purchases)

    for purchase_info in purchases:
        if purchase_info.expense_id:
            bot.send_message(
                message.chat.id,
                make_purchase_report_message(purchase_info)
            )
        else:
            bot.send_message(
                message.chat.id,
                f'Назначьте категорию расходу: '
                f'{_validate_prise(purchase_info.prise)} '
                f'{_validate_currency_code(purchase_info.currency, faked_byn=False)} - '
                f'"{purchase_info.note}".',
                reply_markup=get_callback_reply_markup(purchase_info.position, message.message_id, SIMPLE_TYPE))

    bot.send_message(message.chat.id, f'Потраченно за месяц с учетом новых трат: {get_month_stat(session)} BYN.')
    session.commit()
    session.close()

def get_month_stat(session):
    month_start = datetime.now().\
        replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    purchase = session.query(func.sum(Purchase.prise).label('total_price')).\
        filter(Purchase.epoch >= month_start).scalar().normalize()
    return purchase


def make_purchase_report_message(purchase):
    category_name = dict(EXPENSES).get(str(purchase.expense_id))
    return f'Учтено: {purchase.prise.normalize()} {_validate_currency_code(purchase.currency, faked_byn=False)} - ' \
           f'{purchase.note}. ' \
           f'Категория: "{category_name.capitalize()}".'

def make_expense_report_reply(month_sum, conversation_open_purchases_count):
    return f'Потраченно за месяц с учетом новых трат: {month_sum} BYN. ' \
           f'Необходимо выбрать категории трат для {conversation_open_purchases_count - 1} трат.'

@authorise
@bot.callback_query_handler(func=lambda call: call.data.startswith(u's'))
def reply_to_simple_choice(call):

    session = db_make_session()
    callback_type, message_id, position, expense_id = call.data.split(u'|')

    purchase = Query(Purchase).filter_by(
        user_message_id=message_id,
        position=position,
    ).with_session(session=session).one()
    purchase.expense_id = expense_id
    purchase.status = Purchase.STATUS_CLOSED

    conversation = Query(Conversation).\
        with_session(session=session).\
        get(purchase.conversation_id)
    bot.edit_message_text(make_purchase_report_message(purchase), call.message.chat.id, purchase.bot_message_id)

    conversation_open_purchases_count = Query(Purchase).\
        with_session(session=session). \
        join(Conversation.purchases).\
        filter_by(status=Purchase.STATUS_OPEN, conversation_id=conversation.id).count()

    is_processed_conversation = conversation_open_purchases_count == 1
    month_sum = get_month_stat(session)
    if is_processed_conversation:
        conversation.status = Conversation.STATUS_CLOSED
        bot.edit_message_text(
            f'Потраченно всего за месяц: {month_sum} {_validate_currency_code(purchase.currency, faked_byn=False)}.',
            call.message.chat.id,
            conversation.bot_message_id,
        )
    else:
        bot.edit_message_text(
            make_expense_report_reply(month_sum, conversation_open_purchases_count),
            call.message.chat.id,
            conversation.bot_message_id,
        )
    session.commit()
    session.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)

