# -*- coding: utf-8 -*-

from odoo import models, fields, api
from num2words import num2words


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    picking_list_ref = fields.Char(string='Packing List Ref')
    shipping_details = fields.Text(string='Shipping Details')
    shipping_instruction = fields.Text(string='Shipping Instruction')


    def compute_amount_in_word(self,amount):
        if self.env.user.lang == 'en_US':
            num_word = str(self.currency_id.amount_to_text(amount)) + ' only'
            return num_word
        elif self.env.user.lang == 'ar_001':
            num_word = num2words(amount, to='currency', lang=self.env.user.lang)
            num_word = str(num_word) + ' فقط'
            return num_word

class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    # total tax amount
    line_tax_amount = fields.Float(compute='_compute_line_tax_amount')

    def _compute_line_tax_amount(self):
        for rec in self:
            tot_tax = sum(rec.tax_ids.mapped('amount'))
            rec.line_tax_amount = tot_tax * rec.price_subtotal / 100

    line_discount_amount = fields.Float(compute='_compute_line_discount_amount')

    def _compute_line_discount_amount(self):
        for rec in self:
            price_total = rec.price_unit * rec.quantity
            rec.line_discount_amount = rec.discount * price_total / 100