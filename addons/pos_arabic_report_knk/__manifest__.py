# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).
{
    'name': "POS Arabic Report",
    'version': '14.0.1.0',
    'summary': """POS Arabic Report Module is the Pos Receipt Layout which is printed in english as well as Arabic language to ensure customer's ease of readability and displays content in proper format ready to use for commerical purpose.| POS Receipt | Arabic POS Receipt | Invoice Receipt In POS | Multi language POS Receipt | Arabic POS Report | POS Arabic Invoice Report""",
    'description': """
        POS Arabic Report:
    ->This Module allows user to use custom pos receipt for better format.
    ->Dual Language Report, it Prints Report in English As Well As Arabic Language Report.
    ->Customized Header and Footer to display additional information regarding company and their details in Arabic language.
    """,
    'license': 'OPL-1',
    'author': "Kanak Infosystems LLP.",
    'website': "https://www.kanakinfosystems.com",
    'category': 'Sales/Point Of Sale',
    'depends': [
        'point_of_sale',
    ],
    'images': ['static/description/banner.jpg'],
    'data': [
        'views/assets.xml',
        'views/res_company.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
