# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    company_footer = fields.Char('Footer')
    company_heading_1 = fields.Char('Heading Line 1')
    company_heading_2 = fields.Char('Heading Line 2')
    company_heading_3 = fields.Char('Heading Line 3')
    company_heading_4 = fields.Char('Heading Line 4')
    arabic_name = fields.Char('Arabic Name')


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    arabic_translate = fields.Char('Arabic Translate')
