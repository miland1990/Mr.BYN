# coding: utf-8
from datetime import datetime

import telebot
from sqlalchemy.orm.query import Query
from sqlalchemy.sql import func, column

from credentials import token
from constants import REPLY_EXPENSES, SIMPLE_TYPE, DELIMETER, NOTES_NEVER_NEED_MENU, \
    REMEMBERED_EXPENSE_DUBLICATES_COUNT, OLD_BELARUSSIAN_RUBL_CODE, NEW_BELARUSSIAN_RUBL_CODE
from models import Purchase, Conversation


class BotSpeaker:
    """
    Сервис отвечает за отправку, редактирование, удаление сообщения в чате.
    Имеет встроенный функционал построения интерактивного меню выбора возможных категорий расходов.
    """

    MARKDOWN = 'Markdown'

    def __init__(
            self,
            session,
            chat_id,
            message_id,
            conversation,
            parse_mode=MARKDOWN,
            bot=telebot.TeleBot(token),
    ):
        self.chat_id = chat_id
        self.message_id = message_id
        self.session = session
        self.conversation = conversation
        self.parse_mode = parse_mode
        self.bot = bot

    def _get_callback_markup(self, position, message_id, expense_input_kind):
        """
        Построение интерактивного меню выбора категории расхода.
        """
        keyboard = telebot.types.InlineKeyboardMarkup()
        for expense_id, button_name in REPLY_EXPENSES:
            data = '{expense_input_kind}{DELIMETER}{message_id}{DELIMETER}{position}{DELIMETER}{expense_id}'.format(
                expense_input_kind=expense_input_kind,
                message_id=message_id,
                position=position,
                expense_id=expense_id,
                DELIMETER=DELIMETER,
            )
            callback_button = telebot.types.InlineKeyboardButton(text=button_name, callback_data=data)
            keyboard.add(callback_button)
        return keyboard

    def _edit_message(self, new_text, message_id):
        self.bot.edit_message_text(
            text=new_text,
            chat_id=self.chat_id,
            message_id=message_id,
            parse_mode=self.parse_mode,
        )

    def send_simple_input_message(self, text):
        self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=self.parse_mode,
        )

    def send_choose_expense_category_message(self, text, position=1, expense_input_kind=SIMPLE_TYPE):
        self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=self.parse_mode,
            reply_markup=self._get_callback_markup(
                position=position,
                message_id=self.message_id,
                expense_input_kind=expense_input_kind,
            )
        )

    def delete_message(self, message_id):
        self.bot.delete_message(
            chat_id=self.chat_id,
            message_id=message_id,
        )

    def edit_purchase_bot_message(self, new_text, purchase_message_id):
        self._edit_message(
            new_text=new_text,
            message_id=purchase_message_id,
        )

    def edit_conversation_bot_message(self, new_text):
        return self._edit_message(
            new_text=new_text,
            message_id=self.conversation.bot_message_id
        )


class TextMaker:

    MONTH_PURCHASES_SUMM_TEMPLATE = '''
*Структура расходов* за месяц:
{groupped_stats}
    '''

    PURCHASE_REPORT_AUTO_TEMPLATE = '''
*Учтено автоматически*: {price} {currency_code} - "{note}".
*Категория*: "{category_name}".
*ID расхода*: {purchase_id}.
    '''

    PURCHASE_REPORT_UNIQUE_TEMPLATE = '''
*Учтено*: {price} {currency_code} - "{note}".
*Категория*: "{category_name}".
*ID расхода*: {purchase_id}.
    '''

    MULTIPLE_PURCHASES_GROUP_CHOOSING_INTERMEDIATE_TEMPLATE = '''
Потрачено за месяц *с учетом новых расходов*: {groupped_stats}
Необходимо *выбрать* категорий расходов - {uncategorized_purchases}.
    '''

    PURCHASE_SET_CATEGORY_TEMPLATE = '''
*Назначьте* категорию расходу: {price} {currency_code} - "{note}".
    '''
    ONE_CURRENCY_REPORT = '''
*{currency}*: {summ}'''

    DELETE_PURCHASE_REPORT = '''
*Отменен* расход: {price} {currency_code} - "{note}".
    '''

    @classmethod
    def get_month_stat_report(cls, groupped_stats):
        """
        Сообщение о суммарной трате за текущий месяц с группировкой  по валютам.
        """
        return cls.MONTH_PURCHASES_SUMM_TEMPLATE.\
            format(groupped_stats=cls._format_month_stats(groupped_stats))

    @classmethod
    def _format_month_stats(cls, groupped_stats):
        expenses = []
        if not groupped_stats:
            return ''
        for currency, summ in groupped_stats:
            expenses.append(cls.ONE_CURRENCY_REPORT.format(currency=currency, summ=summ))
        return ''.join(expenses)

    @classmethod
    def get_delete_purchase_report(cls, price, currency_code, note):
        """
        Сообщение с подробной информацией об отмененном расходе (при  нажатии в меню выбора категорий - 'отмена')
        """
        return cls.DELETE_PURCHASE_REPORT.format(
            price=price,
            currency_code=currency_code,
            note=note
        )

    @classmethod
    def get_conversation_intermediate_report(cls, groupped_stats, uncategorized_purchases):
        """
        Промежуточный итог под всеми меню выбора категорий расходов одного ввода траты(трат), где
        упоминается сумма за месяц с текущими тратами и указание количества трат, которым нужно
        указать категорию расхода для данного ввода траты(трат).
        """
        if uncategorized_purchases:
            return cls.MULTIPLE_PURCHASES_GROUP_CHOOSING_INTERMEDIATE_TEMPLATE.\
                format(
                    groupped_stats=cls._format_month_stats(groupped_stats),
                    uncategorized_purchases=uncategorized_purchases,
                )
        else:
            return cls.get_month_stat_report(groupped_stats=groupped_stats)

    @classmethod
    def set_purchase_expense(cls, price, currency_code, note):
        """
        Используется для заголовка выбора категории траты (описание траты).
        """
        return cls.PURCHASE_SET_CATEGORY_TEMPLATE.format(
            price=price,
            currency_code=currency_code,
            note=note,
        )

    @classmethod
    def get_purchase_auto_message_report(cls, price, currency_code, note, category_name, purchase_id):
        """
        Используется для трат, которые система запомнила и для которых не требуется указание категории.
        """
        return cls.PURCHASE_REPORT_AUTO_TEMPLATE.format(
            purchase_id=purchase_id,
            price=price,
            currency_code=currency_code,
            note=note,
            category_name=category_name,
        )

    @classmethod
    def get_purchase_unique_message_report(cls, price, currency_code, note, category_name, purchase_id):
        """
        Используется для трат, которые требуют уточнения категории.
        """
        return cls.PURCHASE_REPORT_UNIQUE_TEMPLATE.format(
            price=price,
            currency_code=currency_code,
            note=note,
            category_name=category_name,
            purchase_id=purchase_id,
        )


class Statist:
    def __init__(
            self,
            session,
    ):
        self.session = session

    def _get_month_start_datetime(self):
        return datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def get_current_month_stats(self):
        stats = self.session.\
            query(Purchase.currency, func.sum(Purchase.price)).\
            filter(Purchase.epoch >= self._get_month_start_datetime()).\
            group_by(Purchase.currency).all()

        currency_expenses = []
        for currency, groupped_currency_summ in stats:
            currency_expenses.append(
                (
                    currency if currency != OLD_BELARUSSIAN_RUBL_CODE else NEW_BELARUSSIAN_RUBL_CODE,
                    round(groupped_currency_summ, 2)
                )
            )
        if not currency_expenses:
            return 0
        return currency_expenses


class SimpleExpenseCallbackDAO:

    def __init__(
            self,
            session,
            message_id,
            position,
    ):
        self.session = session
        self.message_id = message_id
        self.position = position
        self.conversation = None
        self.purchase = None
        self.conversation_open_purchases_count = None
        self.load_initial_data(message_id, position)

    def load_initial_data(self, message_id, position):
        purchase = Query(Purchase).with_session(session=self.session).\
            join(Conversation.purchases).\
            filter_by(
            user_message_id=message_id,
            position=position,
        ).one()
        self.purchase = purchase
        conversation = Query(Conversation).with_session(session=self.session).\
            filter_by(
            id=purchase.conversation_id
        ).one()
        self.conversation = conversation

        self.conversation_open_purchases_count = Query(Purchase).with_session(session=self.session).\
            filter_by(
            status=Purchase.STATUS_OPEN,
            conversation_id=self.conversation.id
        ).count()

    def delete_current_purchase(self):
        Query(Purchase).with_session(session=self.session).filter_by(id=self.purchase.id).delete()
        self.decrement_open_purchases_of_conversation()

        self.session.commit()

    def set_purchase_category(self, expense):
        self.decrement_open_purchases_of_conversation()
        self.purchase.expense = expense

        self.session.commit()

    def close_conversation(self):
        self.conversation.status = Conversation.STATUS_CLOSED

        self.session.commit()

    def close_purchase(self):
        self.purchase.status = Purchase.STATUS_CLOSED

        self.session.commit()

    def decrement_open_purchases_of_conversation(self):
        self.conversation_open_purchases_count -= 1

    @property
    def is_conversation_open(self):
        return self.conversation_open_purchases_count == 0


class SimpleExpenseInputDAO:

    def __init__(
            self,
            session,
            message_id,
            user_id,
            message_datetime,
    ):
        self.session = session
        self.message_id = message_id
        self.user_id = user_id
        self.message_datetime = message_datetime
        self.conversation = self.create_conversation()

    def create_conversation(self):
        conversation = Conversation()

        self.session.add(conversation)
        self.session.commit()

        return conversation

    @staticmethod
    def _get_no_menu_expense(note):
        for category_mark, category_name in NOTES_NEVER_NEED_MENU:
            if category_mark.lower() in note.lower():
                return category_name
        return None

    def find_expense_category(self, note):
        """
        Категория расхода сперва пытается определиться по слову-метке из констант,
        а затем - ходит в базу в попытке найти категорию расхода с таким же комментарием.
        :param note: комментарий расхода.
        :return: категорию расхода (если она определилась), либо None.
        """
        expense_category = None

        no_menu_expense = self._get_no_menu_expense(note)
        if no_menu_expense:
            return no_menu_expense

        purchase_queryset = self.session.query(Purchase).filter(
            column('expense').isnot(None),
            column('note').is_(note)
        )
        dublicate_expense_count = purchase_queryset.count()

        if dublicate_expense_count >= REMEMBERED_EXPENSE_DUBLICATES_COUNT:
            expense_category = purchase_queryset.order_by('-id').first().expense

        return expense_category

    def create_purchases(self, matched_expenses):
        purchases = []
        for expense_match in matched_expenses:

            expense_category = self.find_expense_category(expense_match.note)
            status = Purchase.STATUS_CLOSED if expense_category else Purchase.STATUS_OPEN
            epoch = datetime.fromtimestamp(self.message_datetime)

            purchases.append(
                Purchase(
                    user_message_id=self.message_id,
                    conversation_id=self.conversation.id,
                    position=expense_match.position,
                    status=status,
                    currency=expense_match.currency,
                    user_id=self.user_id,
                    epoch=epoch,
                    price=expense_match.price,
                    note=expense_match.note,
                    expense=expense_category,
                )
            )

        self.conversation.bot_message_id = self.message_id + len(purchases) + 1

        self.session.add_all(purchases)
        self.session.commit()

        return purchases
