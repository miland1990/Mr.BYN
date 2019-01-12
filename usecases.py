# coding: utf-8
from constants import UI_CANCEL_INDEX, RE_SIMPLE, RE_INT
from entity import SimpleExpenseMatch


class SimpleExpenseInputUsecase:

    def __init__(
            self,
            session,
            processor,
            speaker,
            statist,
            text_maker,
            message_text,
    ):
        self.session = session
        self.processor = processor
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
        for purchase in self.processor.create_purchases(matched_expenses):
            if purchase.expense:
                self.speaker.send_new_message(
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
        self.speaker.send_new_message(text=self.text_maker.get_conversation_intermediate_report(
            grouped_stats=self.statist.get_current_month_stats(),
            uncategorized_purchases=uncategorized_purchases)
        )


class SimpleInputCallbackUsecase:

    def __init__(
            self,
            session,
            processor,
            speaker,
            text_maker,
            statist,
    ):
        self.session = session
        self.processor = processor
        self.speaker = speaker
        self.text_maker = text_maker
        self.statist = statist

    def execute(self, expense):

        if expense == UI_CANCEL_INDEX:
            self.processor.delete_current_purchase()
            self.speaker.edit_purchase_bot_message(
                new_text=self.text_maker.get_delete_purchase_report(
                    price=self.processor.purchase.rounded_price,
                    currency_code=self.processor.purchase.currency_code,
                    note=self.processor.purchase.note,
                ),
                purchase_message_id=self.processor.purchase.bot_message_id
            )
            self.speaker.edit_conversation_bot_message(
                new_text=self.text_maker.get_conversation_intermediate_report(
                    grouped_stats=self.statist.get_current_month_stats(),
                    uncategorized_purchases=self.processor.conversation_open_purchases_count
                ),
            )
        else:
            self.processor.set_purchase_category(expense=expense)
            self.speaker.edit_purchase_bot_message(
                new_text=self.text_maker.get_purchase_unique_message_report(
                    purchase_id=self.processor.purchase.id,
                    price=self.processor.purchase.rounded_price,
                    currency_code=self.processor.purchase.currency_code,
                    note=self.processor.purchase.note,
                    category_name=self.processor.purchase.category_name,
                ),
                purchase_message_id=self.processor.purchase.bot_message_id
            )
            if self.processor.is_conversation_open:
                self.processor.close_conversation()
                self.speaker.edit_conversation_bot_message(
                    new_text=self.text_maker.get_month_stat_report(
                        grouped_stats=self.statist.get_current_month_stats()
                    ),
                )
            else:
                self.speaker.edit_conversation_bot_message(
                    new_text=self.text_maker.get_conversation_intermediate_report(
                        grouped_stats=self.statist.get_current_month_stats(),
                        uncategorized_purchases=self.processor.conversation_open_purchases_count
                    ),
                )
            self.processor.close_purchase()


class PurchaseDeleteUseCase:

    def __init__(
            self,
            session,
            processor,
            speaker,
            text_maker,
            statist,
            message_text,
    ):
        self.session = session
        self.processor = processor
        self.speaker = speaker
        self.text_maker = text_maker
        self.statist = statist
        self.message_text = message_text

    def execute(self):
        purchase_ids = RE_INT.findall(self.message_text)

        for raw_purchase_id in purchase_ids:
            price, currency_code, note, purchase_id = self.processor.get_purchase_data(
                purchase_id=raw_purchase_id
            )
            if purchase_id:
                self.speaker.send_new_message(
                    text=self.text_maker.get_deleted_message_report(
                        price,
                        currency_code,
                        note,
                        purchase_id
                    )
                )
            else:
                self.speaker.send_new_message(
                    text=self.text_maker.get_not_found_purchase_report(
                        purchase_id=raw_purchase_id
                    )
                )

        if purchase_ids:
            self.processor.remove_purhcases_by_ids(purchase_ids)

            self.speaker.send_new_message(
                text=self.text_maker.get_month_stat_report(
                    grouped_stats=self.statist.get_current_month_stats()
                )
            )


class DetailedStatsUsecase:

    def __init__(
            self,
            session,
            processor,
            speaker,
            text_maker,
            statist,
            message_text,
    ):
        self.session = session
        self.processor = processor
        self.speaker = speaker
        self.text_maker = text_maker
        self.statist = statist
        self.message_text = message_text

    def execute(self):
        pass
