# coding: utf-8
from sqlalchemy import Column, Integer, Sequence, ForeignKey, TIMESTAMP, Float, String
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import ChoiceType, CurrencyType

from database import Base
from constants import EXPENSES


class Purchase(Base):
    """
    Логическая трата, которых может быть несколько в сообщении пользователя.
    """
    __tablename__ = 'purchase'

    KIND_SIMPLE = 1
    KIND_SMS = 2

    STATUS_OPEN = 1
    STATUS_DUPLICATED = 2
    STATUS_CLOSED = 3

    KIND_CHOICES = (
        ('1', 'simple'),
        ('2', 'sms'),
    )
    STATUS_CHOICES = (
        ('1', 'new'),
        ('2', 'duplicated'),
        ('3', 'closed'),
    )

    id = Column(Integer, Sequence('id'), primary_key=True, autoincrement=True)
    kind = Column(ChoiceType(KIND_CHOICES), default=KIND_SIMPLE)
    user_message_id = Column(Integer)
    status = Column(ChoiceType(STATUS_CHOICES), default=STATUS_OPEN)
    position = Column(Integer)
    currency = Column(CurrencyType, default='BYR')  # BYN еще не стал известным
    user_id = Column(Integer)
    epoch = Column(TIMESTAMP())
    prise = Column(Float(asdecimal=True))  # напиши правильно
    expense_id = Column(Integer, ForeignKey('expsense.id'))
    conversation_id = Column(Integer, ForeignKey('conversation.id'))
    note = Column(String(200))
    conversation = relationship('Conversation', back_populates='purchases')

    @property
    def bot_message_id(self):
        """
        Предвычесленный id резульирующего сообщения, описывающего реакцию бота на каждое из введенных логических трат.
        """
        return self.user_message_id + self.position


class Conversation(Base):
    """
    Пользователь может ввести в одном сообщении как одну трату, так и несколько 
    (несколько скопированных sms, либо несколько трат в одной строке). За кулисами
    сообщение разбивается на отдельные траты. Данная модель определяет реплику пользователя
    и реплику-ответ бота, т.е. своеобразный элемент диалога.
    """
    __tablename__ = 'conversation'

    STATUS_OPEN = 1
    STATUS_CLOSED = 2

    STATUS_CHOICES = (
        ('1', 'open'),
        ('2', 'closed'),
    )

    id = Column(Integer, Sequence('id'), primary_key=True, autoincrement=True)
    purchases = relationship('Purchase', back_populates='conversation')  # реплика пользователя
    status = Column(ChoiceType(STATUS_CHOICES), default=STATUS_OPEN)

    @property
    def bot_message_id(self):
        """
        Предвычесленный id результирующего сообщения, подводящего итог всех расходов в сообщении.
        """
        return self.purchases[-1].user_message_id + len(self.purchases) + 1


class Expense(Base):
    """
    Возможные статьи расходов.
    """
    __tablename__ = 'expsense'

    id = Column(Integer, Sequence('id'), primary_key=True, autoincrement=True)
    name = Column(ChoiceType(EXPENSES))
