# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductInherit(models.Model):
    _inherit = 'product.template'

    origin_char = fields.Char(string='Origin',)
    brand_char = fields.Char(string='Brand',)
    color_char = fields.Char(string='Color',)
    size_char = fields.Char(string='Size',)
