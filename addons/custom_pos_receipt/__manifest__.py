# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'POS Custom Receipt',
    'category': 'Sales/Point of Sale',
    'summary': 'This module is used to customized receipt of point of sale when a user adds a product in the cart and validates payment and print receipt, then the user can see the client name on POS Receipt. | Custom Receipt | POS Reciept | Payment | POS Custom Receipt',
    'description': "Customized our point of sale receipt",
    'version': '16.0.2.0',
    'license': 'LGPL-3',
    'website': '',
    'author': 'Osama Ramadan.',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_partner.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            "custom_pos_receipt/static/src/js/models.js",
            "custom_pos_receipt/static/src/xml/pos.xml",
            "custom_pos_receipt/static/src/scss/pos.scss",
        ],
    },
    'installable': True,
}
