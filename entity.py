# coding: utf-8
from constants import OLD_BELARUSSIAN_RUBLE_CODE, NEW_BELARUSSIAN_RUBLE_CODE


class SimpleExpenseMatch:

    def __init__(
            self,
            position,
            note,
            price,
            currency,
            kind,
    ):
        self.position = position
        self.note = note
        self.kind = kind
        self._price = price
        self._currency = currency

    @property
    def price(self):
        return self._price.replace("ю", ".").replace(",", ".")

    @property
    def currency(self):
        if not self._currency or self._currency == NEW_BELARUSSIAN_RUBLE_CODE:
            return OLD_BELARUSSIAN_RUBLE_CODE
        else:
            return self._currency.upper()
