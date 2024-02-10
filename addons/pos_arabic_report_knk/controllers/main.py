# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import json

from odoo import http
from odoo.http import request


class PosMirrorController(http.Controller):

    @http.route('/get_img_qr_code', type='http', auth="user", methods=['POST'], csrf=False)
    def get_qrcode_img(self, **kwargs):
        qrocde_id = request.env['qr.generator']

        company_name = kwargs.get('company_name')
        vat = kwargs.get('vat')
        date_invoice = kwargs.get('date_invoice')
        amount_total = kwargs.get('amount_total')
        amount_tax = kwargs.get('amount_tax')
        currency_symbol = kwargs.get('currency_symbol')

        data = ""
        if company_name:
            data = str(company_name) + "\n"
        if vat:
            data += str(vat) + "\n"
        if date_invoice:
            data += str(date_invoice) + "\n"
        if amount_total:
            data += str(str(amount_total) + " " + str(currency_symbol)) + "\n"
        if amount_tax:
            data += str(str(amount_tax) + " " + str(currency_symbol)) + "\n"

        return json.dumps({'qr_code_img': qrocde_id.get_qr_code(data)})
