# coding: utf-8
from __future__ import absolute_import, unicode_literals, division, print_function

from constants import UI_CANCEL_INDEX, RE_SIMPLE
from entity import SimpleExpenseMatch


class SimpleInputUsecase:

    def __init__(
            self,
            session,
            dao,
            speaker,
            text_maker,
            statist,
            message_text,
    ):
        self.session = session
        self.dao = dao
        self.speaker = speaker
        self.text_maker = text_maker
        self.statist = statist
        self.message_text = message_text

    def execute(self):

        matched_expenses = []
        for expense_position, expense_match in enumerate(RE_SIMPLE.finditer(self.message_text), start=1):
            matched_expenses.append(
                SimpleExpenseMatch(
                    position=expense_position,
                    note=expense_match.group('note'),
                    price=expense_match.group('price'),
                    currency=expense_match.group('currency'),
                )
            )

        unchoosen_categories_count = 0
        for purchase in self.dao.create_purchases(matched_expenses):
            if purchase.expense_id:
                self.speaker.send_simple_message(
                    text=self.text_maker.get_purchase_auto_message(
                        purchase_id=purchase.id,
                        price=purchase.price,
                        currency_code=purchase.currency_code,
                        note=purchase.note,
                        category_name=purchase.category_name,
                    )
                )
            else:
                unchoosen_categories_count += 1
                text = self.text_maker.set_purchase_category(
                    price=purchase.price,
                    currency_code=purchase.currency_code,
                    note=purchase.note,
                )
                self.speaker.send_choose_category_message(
                    text=text,
                    position=purchase.position,
                )
        self.speaker.send_simple_message(text=self.text_maker.get_detailed_reply(
            groupped_stats=self.statist.get_current_month_stats(),
            unchoosen_categories_count=unchoosen_categories_count)
        )


class SimpleInputCallbackUsecase:

    def __init__(
            self,
            session,
            dao,
            speaker,
            text_maker,
            statist,
    ):
        self.session = session
        self.dao = dao
        self.speaker = speaker
        self.text_maker = text_maker
        self.statist = statist

    def execute(self, category_id):

        if category_id == UI_CANCEL_INDEX:
            self.dao.delete_current_purchase()
            self.speaker.edit_purchase_bot_message(
                new_text=self.text_maker.get_deleted_purchase_report(
                    price=self.dao.purchase.price,
                    currency_code=self.dao.purchase.currency,
                    note=self.dao.purchase.note,
                ),
                purchase_message_id=self.dao.purchase.bot_message_id
            )
            self.speaker.edit_conversation_bot_message(
                new_text=self.text_maker.get_detailed_reply(
                    groupped_stats=self.statist.get_current_month_stats(),
                    unchoosen_categories_count=self.dao.conversation_open_purchases_count
                ),
            )
        else:
            self.dao.set_purchase_category(category_id=category_id)
            self.speaker.edit_purchase_bot_message(
                new_text=self.text_maker.get_purchase_unique_message(
                    purchase_id=self.dao.purchase.id,
                    price=self.dao.purchase.price,
                    currency_code=self.dao.purchase.currency,
                    note=self.dao.purchase.note,
                    category_name=self.dao.purchase.category_name,
                ),
                purchase_message_id=self.dao.purchase.bot_message_id
            )
            if self.dao.is_conversation_open:
                self.dao.close_conversation()
                self.speaker.edit_conversation_bot_message(
                    new_text=self.text_maker.get_month_purchases_stats(
                        groupped_stats=self.statist.get_current_month_stats()
                    ),
                )
            else:
                self.speaker.edit_conversation_bot_message(
                    new_text=self.text_maker.get_detailed_reply(
                        self.statist.get_current_month_stats(),
                        self.dao.conversation_open_purchases_count
                    ),
                )
            self.dao.close_purchase()
