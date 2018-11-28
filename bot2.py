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
    NOTES_NEVER_NEED_MENU, EXPENSES, UI_CANCEL_INDEX
from utils import authorise
from models import Purchase, Conversation
from database import db_make_session

bot = telebot.TeleBot(token)

_simple_input = namedtuple('_simple_input', 'prise,currency,note,expense_id,position') # лучше классами, а еще лучше создать нормальный класс
_prior_sms_input = namedtuple('_prior_sms_input', 'epoch,prise,currency,note')  # здесь та же проблема

# фичи
# TODO: сделать командой конвертацию трат месяца к BYN или USD
# TODO: сделать возможность заблаговременно в сообщении указать, что необходим ручной выбор категории
# TODO: тэггирование о том, что этот расход не должен учитываться с статистике месяца (черная категория)
# TODO: сделать возможность тэггирования расхода, чтобы именно по нему можно было узнать стату
# TODO: сделать команду для тэггированного расхода
# TODO: продумать возможность удобного добавления id пользователя, чтобы можно было авторизовываться
# TODO: возможность переноса траты  на следующий месяц
# TODO: возможность отмены траты по id траты  (ее нужно дописать в мессагу)
# TODO: варнинги об увеличении трат за аналогичные периоды в прошлые периоды
# TODO: возможность изменить категорию уже запомненного варианта

# баги
# TODO: плохо распознает в сплошном простом вводе числа, относящиеся не к цене
# TODO: разобраться, почему не работают смс-ки

# рефакторинг
# TODO: сделать в чистой архитектуре
# TODO: исправить prise на price


@bot.message_handler(commands=[u'stat'])
@authorise
def current_stats(message):
    session = db_make_session()
    bot.send_message(message.chat.id, f'*Итого* за месяц:\n {get_month_stat(session)}', parse_mode='Markdown')
    session.close()


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


def create_purchases(session, conversation, message, purchases):
    purchases_items = []
    for purchase_info in purchases:
        status = Purchase.STATUS_CLOSED if purchase_info.expense_id else Purchase.STATUS_OPEN
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
    conversation.bot_message_id = message.message_id + len(purchases) + 1
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
                info.group('prise'),
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
                make_purchase_report_message(purchase_info, counted='Учтено автоматически'),
                parse_mode='Markdown',
            )
        else:
            bot.send_message(
                message.chat.id,
                f'Назначьте категорию расходу: '
                f'{_validate_prise(purchase_info.prise)} '
                f'{_validate_currency_code(purchase_info.currency, faked_byn=False)} - '
                f'"{purchase_info.note}".',
                reply_markup=get_callback_reply_markup(purchase_info.position, message.message_id, SIMPLE_TYPE))

    bot.send_message(message.chat.id, f'Потраченно за месяц с учетом новых трат:\n {get_month_stat(session)}', parse_mode='Markdown')
    session.commit()
    session.close()

def get_month_stat(session):
    session.commit()  # если вдруг в сессии удалился расход
    month_start = datetime.now().\
        replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stats = dict(session.query(Purchase.currency, func.sum(Purchase.prise)).\
        filter(Purchase.epoch >= month_start).group_by(Purchase.currency).all())
    stats = [f'*{str(currency if currency != "BYR" else "BYN")}*: _{str(round(currency_total_summ, 2))}_'
             for currency, currency_total_summ in stats.items()]
    if stats:
        return '\n' + '\n'.join(stats)
    return 0  # если это первая стата месяца


def make_purchase_report_message(purchase, counted='Учтено'):
    category_name = dict(EXPENSES).get(str(purchase.expense_id))
    price = round(purchase.prise, 2) if not isinstance(purchase.prise, str) else purchase.prise
    report = f'*{counted}*: {price} {_validate_currency_code(purchase.currency, faked_byn=False)} - ' \
           f'{purchase.note}. ' \
           f'*Категория*: "{category_name.capitalize()}". '
    report += f'ID расхода - {purchase.id}' if isinstance(purchase, Purchase) else ""
    return report

def make_expense_report_reply(month_sum, conversation_open_purchases_count):
    positive_open_conversation_purchases_count = conversation_open_purchases_count - 1
    if positive_open_conversation_purchases_count:
        reply = f'Потраченно за месяц с учетом новых расходов:\n {month_sum}.' \
                f'\nНеобходимо выбрать категорий расходов - {positive_open_conversation_purchases_count}.'
    else:
        reply = f'*Итого* за месяц:\n {month_sum}'
    return reply

def get_conversation_open_purchases_count(session, conversation):
    session.commit()
    return Query(Purchase). \
        with_session(session=session). \
        join(Conversation.purchases). \
        filter_by(status=Purchase.STATUS_OPEN, conversation_id=conversation.id).count()


@authorise
@bot.callback_query_handler(func=lambda call: call.data.startswith(u's'))
def reply_to_simple_choice(call):

    session = db_make_session()
    callback_type, message_id, position, expense_id = call.data.split(u'|')

    purchase = Query(Purchase).filter_by(
        user_message_id=message_id,
        position=position,
    ).with_session(session=session).one()

    conversation = Query(Conversation). \
        with_session(session=session). \
        get(purchase.conversation_id)

    if  expense_id == UI_CANCEL_INDEX:
        purchase = Query(Purchase).filter_by(
            user_message_id=message_id,
            position=position,
        ).join(Conversation.purchases).with_session(session=session).one()
        Query(Purchase).filter_by(
            id=purchase.id,
        ).with_session(session=session).delete()

        conversation_purchases_count = purchase.conversation.purchases_count
        if conversation_purchases_count:
            bot.edit_message_text(
                make_expense_report_reply(get_month_stat(session), get_conversation_open_purchases_count(session, conversation)),
                call.message.chat.id,
                conversation.bot_message_id,
                parse_mode='Markdown',
            )
        else:
            bot.delete_message(call.message.chat.id, purchase.conversation.bot_message_id)
        bot.delete_message(call.message.chat.id, purchase.bot_message_id)
    else:
        purchase.expense_id = expense_id

        bot.edit_message_text(make_purchase_report_message(purchase), call.message.chat.id, purchase.bot_message_id, parse_mode='Markdown')

        is_processed_conversation = get_conversation_open_purchases_count(session, conversation) == 0
        if is_processed_conversation:
            conversation.status = Conversation.STATUS_CLOSED
            bot.edit_message_text(
                f'*Итого* за месяц:\n {get_month_stat(session)}',
                call.message.chat.id,
                conversation.bot_message_id,
                parse_mode='Markdown'
            )
        else:
            bot.edit_message_text(
                make_expense_report_reply(get_month_stat(session), get_conversation_open_purchases_count(session, conversation)),
                call.message.chat.id,
                conversation.bot_message_id,
                parse_mode='Markdown',
            )
            purchase.status = Purchase.STATUS_CLOSED
    session.commit()
    session.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)

