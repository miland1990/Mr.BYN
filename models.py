# coding: utf-8
from sqlalchemy import Column, Integer, Sequence, ForeignKey, TIMESTAMP, Float, String
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import ChoiceType, CurrencyType
from enum import Enum

from database import Base
from constants import EXPENSES, OLD_BELARUSSIAN_RUBLE_CODE, NEW_BELARUSSIAN_RUBLE_CODE


class PurchaseInputKind(Enum):
    simple = '1'
    sms = '2'


class PurchaseStatus(Enum):
    open = '1'
    closed = '2'


class ConversationStatus(Enum):
    open = '1'
    closed = '2'


class Purchase(Base):
    """
    Логическая трата, которых может быть несколько в сообщении пользователя.
    """
    __tablename__ = 'purchase'

    id = Column(Integer, Sequence('id'), primary_key=True, autoincrement=True)
    kind = Column(ChoiceType(PurchaseInputKind), default=PurchaseInputKind.simple)
    user_message_id = Column(Integer)
    status = Column(ChoiceType(PurchaseStatus), default=PurchaseStatus.open)
    position = Column(Integer)
    currency = Column(CurrencyType, default=OLD_BELARUSSIAN_RUBLE_CODE)
    user_id = Column(Integer)
    epoch = Column(TIMESTAMP())
    price = Column(Float(asdecimal=True))
    expense = Column(Integer, ForeignKey('expense_category.id'))
    conversation_id = Column(Integer, ForeignKey('conversation.id'))
    note = Column(String(200))
    conversation = relationship('Conversation', back_populates='purchases')

    @property
    def bot_message_id(self):
        """
        Предвычесленный id резульирующего сообщения, описывающего реакцию бота на каждое из введенных логических трат.
        """
        return self.user_message_id + self.position

    @property
    def rounded_price(self):
        """
        Цену округляем до двух знаков после запятой.
        """
        return round(self.price, 2)

    @property
    def currency_code(self):
        """
        Костыль библиотеки, в которой нет BYN кода.
        """
        return NEW_BELARUSSIAN_RUBLE_CODE if self.currency == OLD_BELARUSSIAN_RUBLE_CODE else self.currency

    @property
    def category_name(self):
        return dict(EXPENSES).get(str(self.expense), "").capitalize()


class Conversation(Base):
    """
    Пользователь может ввести в одном сообщении как одну трату, так и несколько 
    (несколько скопированных sms, либо несколько трат в одной строке). За кулисами
    сообщение разбивается на отдельные траты. Данная модель определяет реплику пользователя
    и реплику-ответ бота, т.е. своеобразный элемент диалога.
    """
    __tablename__ = 'conversation'

    id = Column(Integer, Sequence('id'), primary_key=True, autoincrement=True)
    purchases = relationship('Purchase', back_populates='conversation')
    status = Column(ChoiceType(ConversationStatus), default=ConversationStatus.open)
    bot_message_id = Column(Integer)

    @property
    def purchases_count(self):
        return len(self.purchases)


class ExpenseCategory(Base):
    """
    Возможные статьи расходов.
    """
    __tablename__ = 'expense_category'

    id = Column(Integer, Sequence('id'), primary_key=True, autoincrement=True)
    name = Column(ChoiceType(EXPENSES))
