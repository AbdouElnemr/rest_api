# -*- coding: utf-8 -*-
{
    'name': "POS Restaurant Kitchen Screen",
    'version': '1.0.0.1',
    'category': 'Point of Sale',
    'author': 'TL Technology',
    'price': '300',
    'live_test_url': 'http://posodoo.com/saas/public/1',
    'website': 'http://posodoo.com',
    'sequence': 0,
    'description': "Supported Kitchen Screen for Restaurant \n"
                   "Supported Automatic Manufacturing Order each POS Order Line\n"
                   "Supported Sync between POS Sessions",
    'depends': [
        'pos_retail',
    ],
    'data': [
        'PosConfig.xml',
    ],
    "currency": 'EUR',
    'application': True,
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    "license": "OPL-1"
}
