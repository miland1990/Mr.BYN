# coding: utf-8
from datetime import datetime, timedelta
from calendar import monthrange
from collections import defaultdict

import telebot
from sqlalchemy.orm.query import Query
from sqlalchemy.sql import func, column

from credentials import token
from constants import REPLY_EXPENSES, SIMPLE_EXPENSE_CALLBACK, DELIMETER, \
    REMEMBERED_EXPENSE_DUBLICATES_COUNT, OLD_BELARUSSIAN_RUBLE_CODE, NEW_BELARUSSIAN_RUBLE_CODE, MONTHES, \
    MONTH_DETAILED_CALLBACK, EXPENSES, NO_EXPENSE, NOTES_ALWAYS_NEED_MENU
from models import Purchase, Conversation, PurchaseStatus, ConversationStatus


class BotSpeaker:
    """
    Sends, edit, delete messages in a chat. The service builds interactive menu for choosing purchase expense.
    """

    MARKDOWN = 'Markdown'

    def __init__(
            self,
            session,
            chat_id,
            message_id=None,
            conversation=None,
            parse_mode=MARKDOWN,
            bot=telebot.TeleBot(token),
    ):
        self.chat_id = chat_id
        self.message_id = message_id
        self.session = session
        self.conversation = conversation
        self.parse_mode = parse_mode
        self.bot = bot

    def _get_input_callback_markup(self, position, message_id, expense_input_kind):
        """
        Build interactive menu for choosing purchase expense.
        """
        keyboard = telebot.types.InlineKeyboardMarkup()
        for expense_id, button_name in REPLY_EXPENSES:
            data = '{callback_code}{DELIMETER}{message_id}{DELIMETER}{position}{DELIMETER}{expense_id}'.format(
                callback_code=expense_input_kind,
                message_id=message_id,
                position=position,
                expense_id=expense_id,
                DELIMETER=DELIMETER,
            )
            callback_button = telebot.types.InlineKeyboardButton(text=button_name, callback_data=data)
            keyboard.add(callback_button)
        return keyboard

    def _get_detailed_statistics_callback_markup(self):
        """
        Build interactive menu for choosing month of detailed report by categories.
        """
        keyboard = telebot.types.InlineKeyboardMarkup()
        one_line = []
        for index, (month_id, month_name) in enumerate(MONTHES, start=1):
            data = '{callback_code}{DELIMETER}{month_id}'.format(
                month_id=month_id, DELIMETER=DELIMETER, callback_code=MONTH_DETAILED_CALLBACK
            )
            callback_button = telebot.types.InlineKeyboardButton(text=month_name, callback_data=data)
            one_line.append(callback_button)
            if index % 3 == 0:
                keyboard.add(*one_line)
                one_line = []
        return keyboard

    def _edit_message(self, new_text, message_id):
        self.bot.edit_message_text(
            text=new_text,
            chat_id=self.chat_id,
            message_id=message_id,
            parse_mode=self.parse_mode,
        )

    def send_new_message(self, text):
        """
        Send new message to chat.
        """
        self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=self.parse_mode,
        )

    def send_choose_expense_category_message(self, text, position=1, expense_input_kind=SIMPLE_EXPENSE_CALLBACK):
        """
        Send interactive menu for choosing expense.
        """
        self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=self.parse_mode,
            reply_markup=self._get_input_callback_markup(
                position=position,
                message_id=self.message_id,
                expense_input_kind=expense_input_kind,
            )
        )

    def send_choose_month_of_detailed_stats_message(self, text):
        """
        Send interactive menu for choosing month of detailed stats.
        """
        self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=self.parse_mode,
            reply_markup=self._get_detailed_statistics_callback_markup(),
        )

    def delete_message(self, message_id):
        """
        Delete message from chat.
        """
        self.bot.delete_message(
            chat_id=self.chat_id,
            message_id=message_id,
        )

    def edit_purchase_bot_message(self, new_text, purchase_message_id):
        """Edit message in chat. Message should have changes."""
        self._edit_message(
            new_text=new_text,
            message_id=purchase_message_id,
        )

    def edit_conversation_bot_message(self, new_text):
        """
        Edit conversation message
        """
        return self._edit_message(
            new_text=new_text,
            message_id=self.conversation.bot_message_id
        )

    def edit_detailed_command_message(self, new_text, message_id):
        """
        Edit detailed stat message
        """
        return self._edit_message(
            new_text=new_text,
            message_id=message_id,
        )


class TextMaker:
    """
    Make human-readable messages for chat.
    """

    MONTH_PURCHASES_SUMM_TEMPLATE = '''
_Итого_ 📎:
{grouped_stats}
    '''

    DETAILED_MONTH_PURCHASES_SUMM_TEMPLATE = '''
_{month_name}_:
{grouped_stats}
    '''

    DETAILED_MONTH_PURCHASES_NO_DATA_TEMPLATE = '''За *{month_name}* расходов не зарегистрировано.'''

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

    DECLINE_PURCHASE_REPORT = '''
*Отменен* ⭕️ расход: {price} {currency_code} - "{note}".
    '''

    DELETED_PURCHASE_REPORT = '''
*Удален* ❌ расход: {price} {currency_code} - "{note}"*(id={purchase_id})*.
    '''

    NOT_FOUND_PURCHASE_REPORT = '''
Расход *id={purchase_id}* не найден 😧.
    '''

    CHOOSE_MONTH_MENU = '''Выберите анализируемый месяц 👆:'''

    DETAILED_ONE_EXPENSE_REPORT = '''
*{expense_name}*: {currency_report}'''

    DETAILED_ONE_CURRENCY_REPORT = '''_{currency_code}_ - {total_by_currency}'''

    @classmethod
    def get_month_stat_report(cls, grouped_stats):
        """
        Make message with month statistics grouped by currencies.
        """
        grouped_stats = cls._format_month_stats(grouped_stats)
        return cls.MONTH_PURCHASES_SUMM_TEMPLATE.\
            format(grouped_stats=grouped_stats)

    @classmethod
    def get_detailed_month_stat_report(cls, grouped_stats, month_name, total_stats):
        """
        Make message with month statistics grouped by currencies and categories.
        """
        if not grouped_stats:
            return cls.DETAILED_MONTH_PURCHASES_NO_DATA_TEMPLATE.format(month_name=month_name.lower())
        else:
            return cls.DETAILED_MONTH_PURCHASES_SUMM_TEMPLATE.\
                format(grouped_stats=cls._format_detailed_month_stats(grouped_stats), month_name=month_name) + \
                   cls.get_month_stat_report(total_stats)

    @classmethod
    def _format_month_stats(cls, grouped_stats):
        expenses = []
        if not grouped_stats:
            return ''
        for currency, summ in grouped_stats:
            expenses.append(cls.ONE_CURRENCY_REPORT.format(currency=currency, summ=summ))
        return ''.join(expenses)

    @classmethod
    def get_delete_purchase_report(cls, price, currency_code, note):
        """
        Make detailed message about deleted purchase (cancel button submit).
        """
        return cls.DECLINE_PURCHASE_REPORT.format(
            price=price,
            currency_code=currency_code,
            note=note
        )

    @classmethod
    def get_choose_message_report(cls):
        """
        Make choose month menu for detailed statistics.
        """
        return cls.CHOOSE_MONTH_MENU

    @classmethod
    def get_conversation_intermediate_report(cls, grouped_stats, uncategorized_purchases):
        """
        Промежуточный итог под всеми меню выбора категорий расходов одного ввода траты(трат), где
        упоминается сумма за месяц с текущими тратами и указание количества трат, которым нужно
        указать категорию расхода для данного ввода траты(трат).
        """
        if uncategorized_purchases:
            return cls.MULTIPLE_PURCHASES_GROUP_CHOOSING_INTERMEDIATE_TEMPLATE.\
                format(
                    groupped_stats=cls._format_month_stats(grouped_stats),
                    uncategorized_purchases=uncategorized_purchases,
                )
        else:
            return cls.get_month_stat_report(grouped_stats=grouped_stats)

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

    @classmethod
    def get_deleted_message_report(cls, price, currency_code, note, purchase_id):
        """
        Notificate about deleted purhcase from db.
        """
        return cls.DELETED_PURCHASE_REPORT.format(
            price=price,
            currency_code=currency_code,
            note=note,
            purchase_id=purchase_id,
        )

    @classmethod
    def get_not_found_purchase_report(cls, purchase_id):
        return cls.NOT_FOUND_PURCHASE_REPORT.format(purchase_id=purchase_id)

    @classmethod
    def _format_detailed_month_stats(cls, grouped_stats):
        by_expenses = defaultdict(list)
        if not grouped_stats:
            return ''
        for currency_code, total_by_currency, expense_id in grouped_stats:
            expense_name = dict(EXPENSES).get(str(expense_id), NO_EXPENSE).capitalize()
            by_expenses[expense_name].append(
                cls.DETAILED_ONE_CURRENCY_REPORT.format(currency_code=currency_code, total_by_currency=total_by_currency)
            )
        by_category = []
        for expense_name, currency_report in by_expenses.items():
            by_category.append(
                cls.DETAILED_ONE_EXPENSE_REPORT.format(expense_name=expense_name, currency_report=' '.join(currency_report))
            )
        return ''.join(by_category)


class Statist:
    def __init__(
            self,
            session,
    ):
        self.session = session
        self.now = datetime.now()

    def _get_choosen_month_and_year(self, month=None):
        month = month or self.now.month
        if month and self.now.month < month:
            year = self.now.year - 1
        else:
            year = self.now.year
        return year, month

    def _get_month_start_datetime(self, month=None):
        year, month = self._get_choosen_month_and_year(month=month)
        return self.now.replace(hour=0, minute=0, second=0, month=month, year=year, day=1)

    def _get_month_end_datetime(self, month=None):
        year, month = self._get_choosen_month_and_year(month=month)
        max_month_day = monthrange(year, month)[1]
        return self.now.replace(hour=23, minute=59, second=59, month=month, year=year, day=max_month_day)

    def get_current_month_stats(self, month=None):
        stats = self.session.\
            query(Purchase.currency, func.sum(Purchase.price)).\
            filter(Purchase.epoch >= self._get_month_start_datetime(month=month),
                   Purchase.epoch < self._get_month_end_datetime(month=month)).\
            group_by(Purchase.currency).all()

        currency_expenses = []
        for currency, groupped_currency_summ in stats:
            currency_expenses.append(
                (
                    currency if currency != OLD_BELARUSSIAN_RUBLE_CODE else NEW_BELARUSSIAN_RUBLE_CODE,
                    round(groupped_currency_summ, 2)
                )
            )
        if not currency_expenses:
            return 0
        return currency_expenses

    def get_detailed_month_stats(self, month):
        stats = self.session.\
            query(Purchase.currency, func.sum(Purchase.price), Purchase.expense).\
            filter(Purchase.epoch >= self._get_month_start_datetime(month=month),
                   Purchase.epoch < self._get_month_end_datetime(month=month)).\
            group_by(Purchase.currency, Purchase.expense).all()

        currency_expenses = []
        for currency, groupped_currency_summ, expense_id in stats:
            currency_expenses.append(
                (
                    currency.code if currency != OLD_BELARUSSIAN_RUBLE_CODE else NEW_BELARUSSIAN_RUBLE_CODE,
                    round(groupped_currency_summ, 2),
                    expense_id,
                )
            )
        if not currency_expenses:
            return 0
        return currency_expenses


class ExpenseCallbackProcessor:

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
            status=PurchaseStatus.open,
            conversation_id=self.conversation.id
        ).count()

    def delete_current_purchase(self):
        Query(Purchase).with_session(session=self.session).filter_by(id=self.purchase.id).delete()
        self.decrement_open_purchases_of_conversation()
        self.close_conversation()

        self.session.commit()

    def set_purchase_category(self, expense):
        self.decrement_open_purchases_of_conversation()
        self.purchase.expense = expense

        self.session.commit()

    def close_conversation(self):
        self.conversation.status = ConversationStatus.closed

        self.session.commit()

    def close_purchase(self):
        self.purchase.status = PurchaseStatus.closed

        self.session.commit()

    def decrement_open_purchases_of_conversation(self):
        self.conversation_open_purchases_count -= 1

    @property
    def is_conversation_finished(self):
        return self.conversation_open_purchases_count == 0


class ConversationMixin:

    def create_conversation(self, status=ConversationStatus.open):
        conversation = Conversation(status=status)

        self.session.add(conversation)
        self.session.commit()

        return conversation


class ExpenseEditorProcessor(ConversationMixin):

    def __init__(
            self,
            session,
    ):
        self.session = session

    def get_purchase_data(self, purchase_id):
        purchase = Query(Purchase).with_session(session=self.session).filter_by(id=purchase_id).first()
        if purchase:
            return purchase.rounded_price, purchase.currency_code, purchase.note, purchase_id
        else:
            return None, None, None, None

    def remove_purhcases_by_ids(self, ids):
        ids = tuple(map(int, ids))
        Query(Purchase).with_session(session=self.session). \
            filter(Purchase.id.in_(ids)).delete(synchronize_session=False)


class StatProcessor(ConversationMixin):

    def __init__(
            self,
            session,
    ):
        self.session = session
        self.conversation = self.create_conversation(
            status=ConversationStatus.closed
        )

    def get_monthes_choices(self):
        pass


class ExpenseInputProcessor(ConversationMixin):

    def __init__(
            self,
            session,
            message_id,
            user_id,
            message_datetime,
            is_sms,
    ):
        self.session = session
        self.message_id = message_id
        self.user_id = user_id
        self.message_datetime = message_datetime
        self.is_sms = is_sms
        self.conversation = self.create_conversation()

    @staticmethod
    def _need_force_menu_expense(note):
        for force_mark in NOTES_ALWAYS_NEED_MENU:
            if force_mark in note:
                return True
        return False

    def find_expense_category(self, note):
        """
        Категория расхода сперва пытается определиться по слову-метке из констант,
        а затем - ходит в базу в попытке найти категорию расхода с таким же комментарием.
        :param note: комментарий расхода.
        :return: категорию расхода (если она определилась), либо None.
        """
        expense_category = None

        if self.is_sms:
            if self._need_force_menu_expense(note):
                return None

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
            status = PurchaseStatus.closed if expense_category else PurchaseStatus.open
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
                    kind=expense_match.kind,
                )
            )

        self.conversation.bot_message_id = self.message_id + len(purchases) + 1

        self.session.add_all(purchases)
        self.session.commit()

        return purchases
