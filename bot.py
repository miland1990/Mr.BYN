# coding: utf-8

import re
from datetime import date, datetime
from time import mktime
import telebot
import config
from database_api import SQLighter
from credentials import token
from utils import authorise

bot = telebot.TeleBot(token)


# TODO: сделать приложением, которое работает во взаимодействии как с телеграмом, так и имеет веб-морду
# TODO: документация в md формате адекватная
# TODO: добавить тестирование
# TODO: миграция и создания БД файлика автоматом
# TODO: логика бонусов
# TODO: логика ведения баланса (ввод источников доходов с описанием)
# TODO: парсинг чеков
# TODO: стата по видам
# TODO: клепание отчета excel
# TODO: расход по стройке (нужно сразу конвертер валют делать)
# TODO: задолженноть по стройке
# TODO: сравнительный анализ
# TODO: построение графиков
# TODO: возможность редактирования при неверно выбранной категории либо удаление (спортно) записи
# TODO: возможность просмотра статы за указанный период времени и сравнение с аналогичными тремя периодами
# TODO: возможность переноса платежа на следующий месяц
# TODO: проверку на дубликат за последние 10 инпутов простых сообщений по категории и цене с обработкой типа "уверены?"
# TODO: сделать для категорий Foreign Key
# TODO: должно игнорировать при копировании имя

PRIOR_RE_STR = r'Priorbank\. Karta (?:\d\*{3}\d{4}). (?P<datetime>.{17}). ' \
               r'Oplata (?P<prise>\d*[.,]?\d*) (?P<currency>[\w+]{3}). (?P<place>[^\.]+).*'
PRIOR_SMS_RE = re.compile(PRIOR_RE_STR)
PRISE_RE = re.compile(r'^\d+?\.\d+?$')
PRIOR_DATETIME_FORMAT = '%d-%m-%y %H:%M:%S'


class BaseMrBYN:
    def __init__(self, db, bot, expense_choices=config.EXPENSES):
        self.db = db
        self.bot = bot
        self.expense_choices = expense_choices

    _note = None
    _prise = None
    _message_timestamp = None
    _month_start_timestamp = None
    _last_chat_message_id = None
    _chat_id = None
    _message = None
    _currency = u'BYN'

    UI_MESSAGE_DUPLICATE = u'Платеж ({}) уже был засчитан.'
    UI_MESSAGE_MONTH_THANK = u'Cпасибо. Израсходовано за месяц: {} BYN.'
    UI_MESSAGE_MONTH_STAT = u'Израсходовано за месяц: {} BYN.'
    UI_MESSAGE_INVALID = u'Введите корректно расход. Первым словом должна быть цена. Слова разделяются пробелами.'
    UI_MESSAGE_CANCELED = u'Пользователь {} отменил ввод платежа.'
    UI_MESSAGE_UNKNOWN_FORMAT = u'Внимание! Соообщение "{}" - не распознано. Введите расход вручную.'

    @property
    def note(self):
        if not self._note:
            prise, note = self.user_prise_and_note
            self._note = note
            self._prise = prise
        return self._note

    @property
    def prise(self):
        if not self._prise:
            prise, note = self.user_prise_and_note
            self._note = note
            self._prise = prise
        return self._prise

    @property
    def message_timestamp(self):
        if not self._message_timestamp:
            self._message_timestamp = self._message.date
        return self._message_timestamp

    @property
    def month_start_timestamp(self):
        if not self._month_start_timestamp:
            td = date.today().replace(day=1)
            self._month_start_timestamp = mktime(td.timetuple())
        return self._month_start_timestamp

    @property
    def user_prise_and_note(self):
        parts = self._message.text.split()
        prise = parts[0].replace(',', '.')
        note = ' '.join(parts[1:])
        return prise, note

    def callback_reply_markup(self, stat_message_id=u'', button_message_id=u''):
        keyboard = telebot.types.InlineKeyboardMarkup()
        choice_buttons = list(self.expense_choices) + [u'отмена ввода']
        for index, purch in enumerate(choice_buttons, start=1):
            callback_data = str(index) + u'|' + str(self._message.message_id) + u'|' + str(stat_message_id) + u'|' + str(button_message_id)
            callback_button = telebot.types.InlineKeyboardButton(text=purch, callback_data=callback_data)
            keyboard.add(callback_button)
        return keyboard

    @property
    def get_payment_title(self):
            return u'{}: {}'.format(self.note, self.prise)

    @property
    def is_valid_prise(self):
        if PRISE_RE.match(self.prise) is None:
            return self.prise.isdigit()
        return True

    # setter for 'Message' telegram instanse
    def _set_message(self, message, text=None):
        self._message = message
        if text:
            self._message.text = text

    #  отправка сообщений в чат и редактирование сообщений
    def send_to_chat_with_choice_buttons(self, text, stat_message_id=u''):
        self.bot.send_message(self._message.chat.id, text, reply_markup=self.callback_reply_markup(stat_message_id))

    def send_to_chat(self, text):
        self.bot.send_message(self._message.chat.id, text)

    def edit_message_from_chat(self, edited_text, message_id):
        self.bot.edit_message_text(
            chat_id=self._message.chat.id,
            message_id=message_id,
            text=edited_text
        )

    #  запросы в БД
    def record_expense_row(self, expense=None):
        self.db.record_item(
            user_id=self._message.from_user.id,
            message_id=self._message.message_id,
            message_timestamp=self.message_timestamp,
            prise=self.prise,
            note=self.note,
            expense=expense
        )

    def update_expense(self, expense, text=None):
        self.db.update_expense(self._message.message_id, expense, text)

    def delete_message_from_chat_by_message_id(self, message_id):
        self.db.delete_expense_by_timestamp(message_id)

    def find_expense_by_note(self):
        expense_raw = self.db.find_expense(self.note)
        if expense_raw:
            return expense_raw[0]

    def find_expense_by_timestamp(self, timestamp):
        expense = self.db.find_expense_by_timestamp(timestamp)
        if expense:
            expense = expense[0]
        return expense

    #  статистика
    def get_current_month_stat_message(self, template=UI_MESSAGE_MONTH_THANK):
        stats = self.db.stat_by_total_month(self.month_start_timestamp)
        value = round(stats[0] if stats else 0, 2)
        return template.format(value)

    def get_current_stats(self, message):
        self._set_message(message)
        self.send_to_chat(self.get_current_month_stat_message(template=self.UI_MESSAGE_MONTH_STAT))

    def reply_to_choice(self, call):
        raise NotImplementedError

    def reply_to_message(self, message):
        raise NotImplementedError


class SimpleMrBYN(BaseMrBYN):

    def reply_to_message(self, telegram_message_instance):
        self._set_message(telegram_message_instance)
        if not (self.note and self.is_valid_prise):
            self.send_to_chat(text=self.UI_MESSAGE_INVALID)
        else:
            previous_expense = self.find_expense_by_note()
            if not previous_expense:
                self.record_expense_row()
                self.send_to_chat_with_choice_buttons(text=self.get_payment_title)
            else:
                self.record_expense_row(expense=previous_expense)
                self.send_to_chat(text=self.get_current_month_stat_message())

    def reply_to_choice(self, call):
        self._set_message(call.message)
        expense_index, message_id, stat_message_id, _ = call.data.split(u'|')
        if expense_index == str(len(self.expense_choices) + 1):
            self.db.delete_expense_by_message_id(message_id)
            edited_text = self.UI_MESSAGE_CANCELED.format(call.from_user.first_name)
        else:
            self.db.update_expense(message_id, expense_index)
            edited_text = self.get_current_month_stat_message(template=self.UI_MESSAGE_MONTH_STAT)
        self.bot.delete_message(call.message.chat.id, call.message.message_id)
        self.send_to_chat(edited_text)


class PriorMrBYN(BaseMrBYN):

    MESSAGE_DELIMETER = u'\n'
    SMS_NOTES_NEED_MENU = (u'BLR MOBILE BANK',)
    SMS_NOTES_PREDICTORS = (
        (u'NLD UBER', 6),
    )

    def get_messages(self, message):
        return message.text.split(self.MESSAGE_DELIMETER)

    def get_timestamp_from_string(self, datetime_string):
        return int(mktime(datetime.strptime(datetime_string, PRIOR_DATETIME_FORMAT).timetuple()))

    def reply_to_message(self, message_instance):
        messages = self.get_messages(message_instance)
        stat_message_id = str(message_instance.message_id + len(messages) + 1)
        button_message_counter = message_instance.message_id
        for message in messages:
            prior_sms = PRIOR_SMS_RE.match(message)
            if not prior_sms:
                text = self.UI_MESSAGE_UNKNOWN_FORMAT.format(message)
                self._set_message(message_instance, text=text)
                button_message_counter += 1
                self.send_to_chat(text)
                continue
            self._set_message(message_instance, text=message)
            self._prise = prior_sms.group(u'prise')
            self._note = prior_sms.group(u'place')
            self._currency = prior_sms.group(u'currency')
            self._message_timestamp = self.get_timestamp_from_string(prior_sms.group(u'datetime'))
            if self.find_expense_by_timestamp(self._message_timestamp):
                text = self.UI_MESSAGE_DUPLICATE.format(self.get_payment_title)
                self._set_message(message_instance, text=text)
                button_message_counter += 1
                self.send_to_chat(text)
            else:
                prev_note_expense = self.find_expense_by_note()
                if not prev_note_expense:
                    for sub_note, expense in self.SMS_NOTES_PREDICTORS:
                        if sub_note in self._note:
                            prev_note_expense = expense
                    self.record_expense_row(prev_note_expense)
                elif not prev_note_expense or prev_note_expense not in self.SMS_NOTES_NEED_MENU:
                    button_message_counter += 1
                    self.bot.send_message(
                        self._message.chat.id,
                        self.get_payment_title,
                        reply_markup=self.callback_reply_markup(stat_message_id, button_message_counter)
                    )
        self.send_to_chat(self.get_current_month_stat_message(template=self.UI_MESSAGE_MONTH_STAT))
            
    def reply_to_choice(self, call):
        self._set_message(call.message)
        expense_index, message_id, stat_message_id, buttons_message_id = call.data.split(u'|')
        text = call.message.text.split(u':')[0]
        if expense_index == str(len(self.expense_choices) + 1):
            self.db.delete_expense_by_message_id(message_id, text=text)
            self.bot.delete_message(call.message.chat.id, stat_message_id)
        else:
            self.db.update_expense(message_id, expense_index, text=text)
        self.bot.delete_message(call.message.chat.id, buttons_message_id)


@bot.message_handler(commands=[u'stat'])
@authorise
def current_stats(message):
    mr_dollar = SimpleMrBYN(SQLighter(), bot)
    mr_dollar.get_current_stats(message)


@bot.message_handler(func=lambda message: u'Priorbank. Karta' in message.text)
@authorise
def prior_msg(message):
    mr_dollar = PriorMrBYN(SQLighter(), bot)
    mr_dollar.reply_to_message(message)


@bot.message_handler(content_types=[u'text'])
@authorise
def simple_msg(message):
    mr_dollar = SimpleMrBYN(SQLighter(), bot)
    mr_dollar.reply_to_message(message)


@bot.callback_query_handler(func=lambda call: call.data.endswith(u'|'))
@authorise
def reply_to_simple_choice(call):
    mr_dollar = SimpleMrBYN(SQLighter(), bot)
    mr_dollar.reply_to_choice(call)


@bot.callback_query_handler(func=lambda call: True)
@authorise
def reply_to_prior_choice(call):
    mr_dollar = PriorMrBYN(SQLighter(), bot)
    mr_dollar.reply_to_choice(call)


if __name__ == '__main__':
    bot.polling(none_stop=True)
