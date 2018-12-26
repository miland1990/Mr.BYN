# coding: utf-8
from constants import CURRENCY_DEFAULT, NEW_BELARUSSIAN_RUBLE_CODE


class SimpleExpenseMatch:

    def __init__(
            self,
            position,
            note,
            price,
            currency,
    ):
        self.position = position
        self.note = note
        self._price = price
        self._currency = currency

    @property
    def price(self):
        return self._price.replace("ю", ".").replace(",", ".")

    @property
    def currency(self):
        if not self._currency or self._currency == NEW_BELARUSSIAN_RUBLE_CODE:
            return CURRENCY_DEFAULT
        else:
            return self._currency.upper()
