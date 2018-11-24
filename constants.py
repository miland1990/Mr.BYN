# coding: utf-8
import re

# RE_PRIOR_SMS_STR = r'Priorbank\. Karta (?:\d\*{3}\d{4}). (?P<epoch>.{17}). Oplata (?P<prise>\d*[.,]?\d*) (?P<currency>[\w+]{3}). (?P<note>[^\.]+).*'
# RE_PRIOR_SMS = re.compile(RE_PRIOR_SMS_STR)
# TODO: сделать все варианты выбора валют нормально
# TODO: протестировать регулярку!!!
RE_SIMPLE_STR = r'(?P<price>[\d\.\,ю]+)(?:\s+)?(?P<currency>USD|BYR|BYN|RUB|UAH|EUR|PLN)?(?:\s+)?(?P<note>[^\d\.\,]+[^\d\.\,\s])'
RE_SIMPLE = re.compile(RE_SIMPLE_STR, re.U | re.I)

# PRIOR_DATETIME_FORMAT = '%d-%m-%y %H:%M:%S'

CURRENCY_DEFAULT = 'BYR'

# UI_MESSAGE_DUPLICATE = 'Платеж ({}) уже был засчитан.'
# UI_MESSAGE_MONTH_STAT = 'Израсходовано за месяц: {} BYN.'
# UI_MESSAGE_MONTH_THANK = 'Спасибо. ' + UI_MESSAGE_MONTH_STAT
# UI_MESSAGE_INVALID = 'Введите корректно расход. Первым словом должна быть цена. Слова разделяются пробелами.'
# UI_MESSAGE_CANCELED = 'Пользователь {} отменил ввод платежа.'
# UI_MESSAGE_UNKNOWN_FORMAT = 'Внимание! Соообщение "{}" - не распознано. Введите расход вручную.'
UI_CANCEL_BUTTON = 'отмена ввода'

EXPENSE_COMMUNAL = 'коммуналка'
EXPENSE_PRODUCT_SHOP = 'магазин'
EXPENSE_FEE = 'сборы'
EXPENSE_DOMESTIC = 'бытовые'
EXPENSE_HEALTH = 'здоровье'
EXPENSE_TRANSPORT = 'транспорт'
EXPENSE_BEAUTY = 'красота'
EXPENSE_NTERTAINMENT = 'развлечения'
EXPENSE_BUY = 'покупки'
EXPENSE_CHILD = 'ребенок'
EXPENSE_HOME_BUILDING = 'стройка'
EXPENSE_ANOTHER = 'иное'

EXPENSES_NAMES = (EXPENSE_COMMUNAL, EXPENSE_PRODUCT_SHOP, EXPENSE_FEE,
                  EXPENSE_DOMESTIC, EXPENSE_HEALTH, EXPENSE_TRANSPORT,
                  EXPENSE_BEAUTY, EXPENSE_NTERTAINMENT, EXPENSE_BUY,
                  EXPENSE_CHILD, EXPENSE_HOME_BUILDING, EXPENSE_ANOTHER)

EXPENSES = (
    ('1', EXPENSE_COMMUNAL),
    ('2', EXPENSE_PRODUCT_SHOP),
    ('3', EXPENSE_FEE),
    ('4', EXPENSE_DOMESTIC),
    ('5', EXPENSE_HEALTH),
    ('6', EXPENSE_TRANSPORT),
    ('7', EXPENSE_BEAUTY),
    ('8', EXPENSE_NTERTAINMENT),
    ('9', EXPENSE_BUY),
    ('10', EXPENSE_CHILD),
    ('11', EXPENSE_HOME_BUILDING),
    ('12', EXPENSE_ANOTHER),
)

UI_CANCEL_INDEX = str(len(EXPENSES) + 1)

REPLY_EXPENSES = EXPENSES + ((UI_CANCEL_INDEX, UI_CANCEL_BUTTON),)

NOTES_ALWAYS_NEED_MENU = ('BLR MOBILE BANK',)
NOTES_NEVER_NEED_MENU = (
    ('NLD UBER', EXPENSE_TRANSPORT),
)

SIMPLE_TYPE = 's'
