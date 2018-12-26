# coding: utf-8
from constants import UI_CANCEL_INDEX, RE_SIMPLE
from entity import SimpleExpenseMatch


class SimpleExpenseInputUsecase:

    def __init__(
            self,
            session,
            dao,
            speaker,
            statist,
            text_maker,
            message_text,
    ):
        self.session = session
        self.dao = dao
        self.speaker = speaker
        self.statist = statist
        self.text_maker = text_maker
        self.message_text = message_text

    def execute(self):

        matched_expenses = []
        for position, match in enumerate(RE_SIMPLE.finditer(self.message_text), start=1):
            matched_expenses.append(
                SimpleExpenseMatch(
                    position=position,
                    note=match.group('note'),
                    price=match.group('price'),
                    currency=match.group('currency'),
                )
            )

        uncategorized_purchases = 0
        for purchase in self.dao.create_purchases(matched_expenses):
            if purchase.expense:
                self.speaker.send_simple_input_message(
                    text=self.text_maker.get_purchase_auto_message_report(
                        purchase_id=purchase.id,
                        price=purchase.rounded_price,
                        currency_code=purchase.currency_code,
                        note=purchase.note,
                        category_name=purchase.category_name,
                    )
                )
            else:
                uncategorized_purchases += 1
                text = self.text_maker.set_purchase_expense(
                    price=purchase.rounded_price,
                    currency_code=purchase.currency_code,
                    note=purchase.note,
                )
                self.speaker.send_choose_expense_category_message(
                    text=text,
                    position=purchase.position,
                )
        self.speaker.send_simple_input_message(text=self.text_maker.get_conversation_intermediate_report(
            groupped_stats=self.statist.get_current_month_stats(),
            uncategorized_purchases=uncategorized_purchases)
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

    def execute(self, expense):

        if expense == UI_CANCEL_INDEX:
            self.dao.delete_current_purchase()
            self.speaker.edit_purchase_bot_message(
                new_text=self.text_maker.get_delete_purchase_report(
                    price=self.dao.purchase.rounded_price,
                    currency_code=self.dao.purchase.currency,
                    note=self.dao.purchase.note,
                ),
                purchase_message_id=self.dao.purchase.bot_message_id
            )
            self.speaker.edit_conversation_bot_message(
                new_text=self.text_maker.get_conversation_intermediate_report(
                    groupped_stats=self.statist.get_current_month_stats(),
                    uncategorized_purchases=self.dao.conversation_open_purchases_count
                ),
            )
        else:
            self.dao.set_purchase_category(expense=expense)
            self.speaker.edit_purchase_bot_message(
                new_text=self.text_maker.get_purchase_unique_message_report(
                    purchase_id=self.dao.purchase.id,
                    price=self.dao.purchase.rounded_price,
                    currency_code=self.dao.purchase.currency_code,
                    note=self.dao.purchase.note,
                    category_name=self.dao.purchase.category_name,
                ),
                purchase_message_id=self.dao.purchase.bot_message_id
            )
            if self.dao.is_conversation_open:
                self.dao.close_conversation()
                self.speaker.edit_conversation_bot_message(
                    new_text=self.text_maker.get_month_stat_report(
                        groupped_stats=self.statist.get_current_month_stats()
                    ),
                )
            else:
                self.speaker.edit_conversation_bot_message(
                    new_text=self.text_maker.get_conversation_intermediate_report(
                        self.statist.get_current_month_stats(),
                        self.dao.conversation_open_purchases_count
                    ),
                )
            self.dao.close_purchase()
