# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    name_ar = fields.Char(string='Arabic Name')
    po_box = fields.Char(string='PO Box')
