# -*- coding: utf-8 -*-
##########################################################################
# Author      : Nevioo Technologies (<https://nevioo.com/>)
# Copyright(c): 2020-Present Nevioo Technologies
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
##########################################################################
{
    "name":  "POS Order Customer Info",
    "summary": "Allow pos users to enter the customer details \
                at the time of payment and same details will be available on pos receipt and pos order.",
    "category":  "Point Of Sale",
    "version":  "14.0.1.1",
    "sequence":  1,
    "license": 'OPL-1',
    "images": ['static/description/Banner.png'],
    "author":  "Nevioo Technologies",
    "website":  "www.nevioo.com",
    "depends":  ['point_of_sale'],
    'data': [
        'views/template.xml',
        'views/pos_order_view.xml',
            ],
    'qweb': ['static/src/xml/ni_pos_customer_detail.xml','static/src/xml/pos_receipt_view.xml'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
}
