# coding: utf-8
from __future__ import unicode_literals

from collections import namedtuple

import telebot

from credentials import token
from constants import RE_SIMPLE_STR, SIMPLE_TYPE, DELIMETER
from utils import authorise
from database import db_make_session
from services import BotSpeaker, TextMaker, SimpleCallbackDialogDAO, Statist, SimpleInputDialogDAO
from usecases import SimpleInputCallbackUsecase, SimpleInputUsecase

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
# TODO: добавить смайлики в выдачу

# баги
# TODO: плохо распознает в сплошном простом вводе числа, относящиеся не к цене
# TODO: при множественном выборе может быть ситуация дублирования предпоследнего и последнего bot сообщения с итогом - откуда ошибка api логгируется
# TODO: разобраться, почему не работают смс-ки

# рефакторинг
# TODO: сделать в чистой архитектуре
# TODO: исправить prise на price в модели
# TODO: более совершенный механизм отложенного удаления суммирующего сообщения завершенной беседы


@bot.message_handler(commands=[u'stat'])
@authorise
def current_stats(message):
    session = db_make_session()
    statist = Statist(session=session)

    bot.send_message(
        message.chat.id,
        TextMaker.get_month_purchases_stats(
            statist.get_current_month_stats()
        ),
        parse_mode='Markdown'
    )
    session.close()


@bot.message_handler(regexp=RE_SIMPLE_STR)
@authorise
def simple_user_input(message):
    session = db_make_session()
    dao = SimpleInputDialogDAO(
        session=session,
        message_id=message.message_id,
        user_id=message.from_user.id,
        message_datetime=message.date,
    )
    bot_speaker = BotSpeaker(
        chat_id=message.chat.id,
        message_id=message.message_id,
        session=session,
        conversation=dao.conversation,
    )
    statist = Statist(session=session)

    usecase = SimpleInputUsecase(
        session=session,
        dao=dao,
        speaker=bot_speaker,
        text_maker=TextMaker,
        statist=statist,
        message_text=message.text,
    )
    usecase.execute()

    session.commit()
    session.close()


@authorise
@bot.callback_query_handler(func=lambda call: call.data.startswith(SIMPLE_TYPE))
def simple_callback_view(call):

    session = db_make_session()
    callback_kind, user_message_id, conversation_position, category_id = call.data.split(DELIMETER)
    dao = SimpleCallbackDialogDAO(
        session=session,
        user_message_id=user_message_id,
        position=conversation_position,
    )
    speaker = BotSpeaker(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        session=session,
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
    usecase.execute(category_id=category_id)

    session.commit()
    session.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)

