# coding: utf-8
import re

RE_SIMPLE_STR = r'(?P<price>[\d\.\,ю]+)(?:\s+)?(?P<currency>USD|BYR|BYN|RUB|UAH|EUR|PLN)?(?:\s+)?(?P<note>[\w].*?)(?:  |$|;)'
RE_SIMPLE = re.compile(RE_SIMPLE_STR, re.U | re.I)

RE_REMOVE_PURCHASE_STR = r'^(?:remove|rm|del)(?:\s+)?(?P<purchase_id>[\d]+)'
RE_REMOVE_PURCHASE = re.compile(RE_REMOVE_PURCHASE_STR, re.U | re.I)

RE_PRIOR_SMS_STR = r'Priorbank. Karta (?:\d\*{3}\d{4}) (?P<epoch>.{19}). Oplata (?P<price>\d*[.,]?\d*) (?P<currency>[\w+]{3}). (?P<note>[^\.]+).*'
RE_PRIOR_SMS = re.compile(RE_PRIOR_SMS_STR)

RE_INT_STR = r'(?P<integer>[\d]+)'
RE_INT = re.compile(RE_INT_STR, re.U | re.I)

OLD_BELARUSSIAN_RUBLE_CODE = 'BYR'
NEW_BELARUSSIAN_RUBLE_CODE = 'BYN'

UI_CANCEL_BUTTON = 'отмена ввода ❌'

EXPENSE_COMMUNAL = 'ежемесячные 🌔'
EXPENSE_PRODUCT_SHOP = 'продовольственные 🛒'
EXPENSE_FEE = 'подарки 💸'
EXPENSE_DOMESTIC = 'бытовые 🛁'
EXPENSE_HEALTH = 'здоровье 💊'
EXPENSE_TRANSPORT = 'транспорт 🚗'
EXPENSE_BEAUTY = 'красота 👑'
EXPENSE_NTERTAINMENT = 'развлечения 🎉'
EXPENSE_BUY = 'покупки 👔'
EXPENSE_CHILD = 'ребенок 👼'
EXPENSE_DOG = 'собака 🦮'
EXPENSE_INSURANCE = 'страховка 🧤'
EXPENSE_CREDIT = 'рассрочки-кредиты 🎃'
EXPENSE_ANOTHER = 'иное 🗿'
NO_EXPENSE = 'без категории 🔎'

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
    ('13', EXPENSE_DOG),
    ('14', EXPENSE_INSURANCE),
    ('15', EXPENSE_CREDIT),
    ('12', EXPENSE_ANOTHER),
)

MONTHES = (
    ('1', u'Январь ❄️'),
    ('2', u'Февраль ❄️'),
    ('3', u'Март 🌱️'),
    ('4', u'Апрель 🌱'),
    ('5', u'Май 🌱'),
    ('6', u'Июнь 🌞'),
    ('7', u'Июль 🌞'),
    ('8', u'Август 🌞'),
    ('9', u'Сентябрь 🍁'),
    ('10', u'Октябрь 🍁'),
    ('11', u'Ноябрь 🍁'),
    ('12', u'Декабрь ❄️'),
)

UI_CANCEL_INDEX = str(max(map(lambda x: int(x[0]), EXPENSES)) + 1)

REPLY_EXPENSES = EXPENSES + ((UI_CANCEL_INDEX, UI_CANCEL_BUTTON),)

NOTES_ALWAYS_NEED_MENU = (
    'BLR MOBILE BANK',  # мобильный банкинг через приложение
    'BLR SHOP',  # может быть абсолютно любой магазин
)

SIMPLE_EXPENSE_CALLBACK = 's'
EXPENSE_DETALIZATION_CALLBACK = 'e'
MONTH_DETAILED_CALLBACK = 'm'
DELIMETER = '|'
REMEMBERED_EXPENSE_DUBLICATES_COUNT = 2
