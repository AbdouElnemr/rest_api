# -*- coding: utf-8 -*-


from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"


    # receipt_header = fields.Html(string='Receipt Header',
    #                              help="A short text that will be inserted as a header in the printed receipt.")
    # receipt_footer = fields.Html(string='Receipt Footer',
    #                              help="A short text that will be inserted as a footer in the printed receipt.")

