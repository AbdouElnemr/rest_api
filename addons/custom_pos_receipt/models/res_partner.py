# -*- coding: utf-8 -*-

import re

from odoo import models, fields, api
import math


class Partner(models.Model):
    _inherit = "res.partner"

    trn = fields.Char(string="TRN", required=False, )
