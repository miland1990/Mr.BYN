# coding: utf-8
import telebot

from credentials import token
from constants import RE_SIMPLE_STR, SIMPLE_EXPENSE_CALLBACK, DELIMETER, RE_REMOVE_PURCHASE_STR, \
    MONTH_DETAILED_CALLBACK, RE_PRIOR_SMS_STR, RE_PRIOR_SMS, RE_SIMPLE, EXPENSE_DETALIZATION_CALLBACK
from decorators import authorise, wrap_to_session, logg
from logg import logger
from services import BotSpeaker, TextMaker, ExpenseCallbackProcessor, Statist, ExpenseInputProcessor, \
    ExpenseEditorProcessor
from usecases import InputCallbackUsecase, ExpenseInputUsecase, PurchaseDeleteUseCase, \
    StatsUsecase, StatsCallbackUsecase, ExpenseCategoryDetailzation, ExpenseCategoryCallbackUsecase

bot = telebot.TeleBot(token)


@bot.message_handler(regexp=RE_REMOVE_PURCHASE_STR)
@authorise
@wrap_to_session
@logg
def remove_purhcase(session, message):

    processor = ExpenseEditorProcessor(session=session)

    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
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


@bot.message_handler(regexp=RE_PRIOR_SMS_STR)
@authorise
@wrap_to_session
@logg
def sms_user_input(session, message):

    processor = ExpenseInputProcessor(
        session=session,
        message_id=message.message_id,
        user_id=message.from_user.id,
        message_datetime=message.date,
        is_sms=True,
    )
    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,
        conversation=processor.conversation,
    )
    statist = Statist(session=session)

    usecase = ExpenseInputUsecase(
        session=session,
        processor=processor,
        speaker=speaker,
        statist=statist,
        text_maker=TextMaker,
        message_text=message.text,
        regexp=RE_PRIOR_SMS,
    )
    usecase.execute()


@bot.message_handler(regexp=RE_SIMPLE_STR)
@authorise
@wrap_to_session
@logg
def simple_user_input(session, message):

    processor = ExpenseInputProcessor(
        session=session,
        message_id=message.message_id,
        user_id=message.from_user.id,
        message_datetime=message.date,
        is_sms=False
    )
    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,
        conversation=processor.conversation,
    )
    statist = Statist(session=session)

    usecase = ExpenseInputUsecase(
        session=session,
        processor=processor,
        speaker=speaker,
        statist=statist,
        text_maker=TextMaker,
        message_text=message.text,
        regexp=RE_SIMPLE,
    )
    usecase.execute()


@bot.callback_query_handler(func=lambda call: call.data.startswith(SIMPLE_EXPENSE_CALLBACK))
@authorise
@wrap_to_session
@logg
def simple_callback_view(session, call):

    expense_input_kind, message_id, position, expense = call.data.split(DELIMETER)
    processor = ExpenseCallbackProcessor(
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

    usecase = InputCallbackUsecase(
        session=session,
        processor=processor,
        speaker=speaker,
        text_maker=TextMaker,
        statist=statist
    )
    usecase.execute(expense=expense)


@bot.message_handler(commands=[u'stat'])
@authorise
@wrap_to_session
@logg
def get_month_detailed_stat_choices(session, message):

    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,
    )

    usecase = StatsUsecase(
        session=session,
        speaker=speaker,
        text_maker=TextMaker,
    )
    usecase.execute()


@bot.callback_query_handler(func=lambda call: call.data.startswith(MONTH_DETAILED_CALLBACK))
@authorise
@wrap_to_session
@logg
def detailed_month_stats_callback_view(session, call):

    month_callback_call, month_code = call.data.split(DELIMETER)

    statist = Statist(session=session)
    speaker = BotSpeaker(
        session=session,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )
    usecase = StatsCallbackUsecase(
        session=session,
        speaker=speaker,
        text_maker=TextMaker,
        statist=statist
    )

    usecase.execute(month_code=month_code, message_id=call.message.message_id)


@bot.message_handler(commands=[u'category_expenses'])
@authorise
@wrap_to_session
@logg
def get_category_expenses(session, message):

    speaker = BotSpeaker(
        session=session,
        chat_id=message.chat.id,
        message_id=message.message_id,
    )

    usecase = ExpenseCategoryDetailzation(
        session=session,
        speaker=speaker,
        text_maker=TextMaker,
    )
    usecase.execute()


@bot.callback_query_handler(func=lambda call: call.data.startswith(EXPENSE_DETALIZATION_CALLBACK))
@authorise
@wrap_to_session
@logg
def detailed_expense_category_callback_view(session, call):

    expense_category_callback_call, expense_category = call.data.split(DELIMETER)

    statist = Statist(session=session)
    speaker = BotSpeaker(
        session=session,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )
    usecase = ExpenseCategoryCallbackUsecase(
        session=session,
        speaker=speaker,
        text_maker=TextMaker,
        statist=statist
    )

    usecase.execute(expense_category=expense_category, message_id=call.message.message_id)


@bot.message_handler(regexp=r'.*')
@authorise
@wrap_to_session
def logg_incorrect_command(session, message):
    logger.info('unparsed: {}'.format(message.text))


if __name__ == '__main__':
    bot.polling(none_stop=True)

