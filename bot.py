# coding: utf-8
import logging

import telebot

from credentials import token
from constants import RE_SIMPLE_STR, SIMPLE_TYPE, DELIMETER, RE_REMOVE_PURCHASE_STR
from utils import authorise
from database import db_make_session
from services import BotSpeaker, TextMaker, SimpleExpenseCallbackProcessor, Statist, SimpleExpenseInputProcessor, \
    ExpenseEditorProcessor
from usecases import SimpleInputCallbackUsecase, SimpleExpenseInputUsecase, PurchaseDeleteUseCase

bot = telebot.TeleBot(token)

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('vol/main.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@bot.message_handler(commands=[u'stat'])
@authorise
def get_month_stat(message):

    logger.info(message.text)

    session = db_make_session()
    statist = Statist(session=session)

    bot.send_message(
        chat_id=message.chat.id,
        text=TextMaker.get_month_stat_report(
            statist.get_current_month_stats()
        ),
        parse_mode='Markdown'
    )

    session.close()


@bot.message_handler(regexp=RE_REMOVE_PURCHASE_STR)
@authorise
def remove_purhcase(message):

    logger.info(message.text)

    session = db_make_session()

    processor = ExpenseEditorProcessor(session=session)

    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,  # в данном юзкейсе не нужно
        conversation=processor.conversation,  # в данном юзкейсе не нужно
    )

    statist = Statist(session=session)

    usecase = PurchaseDeleteUseCase(
        session=session,
        processor=processor,
        speaker=speaker,
        statist=statist,
        text_maker=TextMaker,
        message_text=message.text,
    )
    usecase.execute()

    session.commit()
    session.close()


@bot.message_handler(regexp=RE_SIMPLE_STR)
@authorise
def simple_user_input(message):

    logger.info(message.text)

    session = db_make_session()
    processor = SimpleExpenseInputProcessor(
        session=session,
        message_id=message.message_id,
        user_id=message.from_user.id,
        message_datetime=message.date,
    )
    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,
        conversation=processor.conversation,
    )
    statist = Statist(session=session)

    usecase = SimpleExpenseInputUsecase(
        session=session,
        processor=processor,
        speaker=speaker,
        statist=statist,
        text_maker=TextMaker,
        message_text=message.text,
    )
    usecase.execute()

    session.commit()
    session.close()


@authorise
@bot.callback_query_handler(func=lambda call: call.data.startswith(SIMPLE_TYPE))
def simple_callback_view(call):

    logger.info(call.message.text + ' - ' + call.data)

    session = db_make_session()
    expense_input_kind, message_id, position, expense = call.data.split(DELIMETER)
    processor = SimpleExpenseCallbackProcessor(
        session=session,
        message_id=message_id,
        position=position,
    )
    speaker = BotSpeaker(
        session=session,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        conversation=processor.conversation,
    )
    statist = Statist(session=session)

    usecase = SimpleInputCallbackUsecase(
        session=session,
        processor=processor,
        speaker=speaker,
        text_maker=TextMaker,
        statist=statist
    )
    usecase.execute(expense=expense)

    session.commit()
    session.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)

