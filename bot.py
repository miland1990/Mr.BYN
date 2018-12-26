# coding: utf-8
import telebot

from credentials import token
from constants import RE_SIMPLE_STR, SIMPLE_TYPE, DELIMETER
from utils import authorise
from database import db_make_session
from services import BotSpeaker, TextMaker, SimpleExpenseCallbackDAO, Statist, SimpleExpenseInputDAO
from usecases import SimpleInputCallbackUsecase, SimpleExpenseInputUsecase

bot = telebot.TeleBot(token)


@bot.message_handler(commands=[u'stat'])
@authorise
def get_month_stat(message):

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


@bot.message_handler(regexp=RE_SIMPLE_STR)
@authorise
def simple_user_input(message):

    session = db_make_session()
    dao = SimpleExpenseInputDAO(
        session=session,
        message_id=message.message_id,
        user_id=message.from_user.id,
        message_datetime=message.date,
    )
    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,
        conversation=dao.conversation,
    )
    statist = Statist(session=session)

    usecase = SimpleExpenseInputUsecase(
        session=session,
        dao=dao,
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

    session = db_make_session()
    expense_input_kind, message_id, position, expense = call.data.split(DELIMETER)
    dao = SimpleExpenseCallbackDAO(
        session=session,
        message_id=message_id,
        position=position,
    )
    speaker = BotSpeaker(
        session=session,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        conversation=dao.conversation,
    )
    statist = Statist(session=session)

    usecase = SimpleInputCallbackUsecase(
        session=session,
        dao=dao,
        speaker=speaker,
        text_maker=TextMaker,
        statist=statist
    )
    usecase.execute(expense=expense)

    session.commit()
    session.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)

