from odoo import http, _
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessError, AccessDenied, ValidationError
from odoo.http import request, Response
import re

#
#     "partner_id": 10,
#     "partner_invoice_id": 10,
#     "partner_shipping_id": 10,
#     "validity_date": false,
#     "date_order": "2023-02-06 17:50:41",
#     "pricelist_id": 1,
#     "payment_term_id": false,
#     "order_line": [
#         {
#             "product_id": 2232,
#             "product_template_id": 2303,
#             "product_uom_qty": 1,
#             "product_uom": 1,
#             "price_unit": 1314.29,
#             "tax_id": 11,
#             "discount": 2
#         },
#         {
#             "product_id": 2246,
#             "product_template_id": 2317,
#             "product_uom_qty": 1,
#             "product_uom": 1,
#             "customer_lead": 0,
#             "price_unit": 1133.33,
#             "tax_id": 11,
#             "discount": 0
#         }
#     ],
#     "customer": {
#         "name": "Mohamed Salah",
#          "email": "abdouelnemr91",
#         "street": "Shebin Elkom",
#         "street2": "Sharkia",
#         "city": "Cairo",
#         "zip": "4566",
#         "phone": "01066666666",
#         "mobile": "7987987987"
#     }
# }

regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')


def email_validate(email):
    if re.fullmatch(regex, email):
        return True
    else:
        raise ValidationError(_("Invalid Email"))


class ProductsApi(http.Controller):
    @http.route('/web/session/authenticate', type="json", auth='none', methods=["POST"], website=True)
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()

    @http.route('/get_all_taxes', type="json", auth='user', csrf=False, methods=["GET"])
    def get_all_taxes(self, **data):
        all_taxes = request.env['account.tax'].search([])
        data = {}
        taxes = []
        for rec in all_taxes:
            vals = {
                'id': rec.id,
                'name': rec.name,
            }
            taxes.append(vals)
        if taxes:
            data = {
                'status': "200",
                'message': "success",
                'data': taxes,
            }
        else:
            data = {
                'status': "400",
                'message': "No Taxes",
                'data': taxes,
            }
        return data

    @http.route('/create_order', type="json", auth='user', csrf=False, methods=["POST"])
    def create_order(self, **data):
        order_partner = ''
        shipping = request.env['delivery.carrier'].search([])[0]
        print('pppppppppp', shipping)
        if data['customer']:
            print('1', " data['customer']")
            customer = request.env['res.partner'].search([('email', '=', data['customer']['email'])])
            if customer:
                order_partner = customer
                print("found")
            else:
                if email_validate(data['customer']['email']):
                    order_partner = request.env['res.partner'].create({
                        "active": True,
                        "company_type": "person",
                        "name": data['customer']['name'],
                        "type": "contact",
                        "street": data['customer']['street'],
                        "street2": data['customer']['street2'],
                        "city": data['customer']['city'],
                        "zip": data['customer']['zip'],
                        "phone": data['customer']['phone'],
                        "mobile": data['customer']['mobile'],
                        "email": data['customer']['email'],
                    })
            order_lines = []
            st_product = request.env['product.product'].search([])

            for rec in data['order_line']:
                print('2', " data['order_line']")

                if rec['product_id'] in st_product.ids:
                    print('3', " data['order_line']")
                    curr_prod = request.env['product.product'].search([('id', '=', rec['product_id'])])
                    order_lines.append(
                        (0, 0, {
                            'name': curr_prod.name,
                            'product_id': rec['product_id'],
                            'product_uom_qty': rec['product_uom_qty'],
                            'product_uom': rec['product_uom'],
                            'price_unit': curr_prod.lst_price,

                            # 'discount': rec['discount']
                        }),

                    )
            order = request.env['sale.order'].create({
                "partner_id": order_partner.id,
                "partner_invoice_id": order_partner.id,
                "partner_shipping_id": order_partner.id,
                # "payment_method_id": data['payment_method'],
                "date_order": data['date_order'],
                "ecom_sale_order_id": data['ecom_sale_order_id'],
                "pricelist_id": 1,
                "payment_term_id": 1,
                'order_line': order_lines,
                'picking_policy': 'direct',
            })
            order.action_confirm()
            order.delivery_status1 = 'order_confirmed'
        # delivery = float(data['cod_fee'])
        # order.order_line.filtered(lambda l: 'delivery charges' in l.product_id.name).price_unit
        base_url = 'https://babolat.linaegypt.com/'

        URL = base_url + 'report/pdf/sale.report_saleorder/' + str(order.id)
        final = {
            "order_id": order.id,
            "ecom_sale_order_id": order.ecom_sale_order_id,
            "increment_id": order.name,
            "order_date": order.date_order,
            "status": order.delivery_status1,
            "currency": order.currency_id.name,
            "totals": {
                "subtotal": order.amount_untaxed,
                "tax": order.amount_tax,
                # "shipping": data['cod_fee'],
                "grand_total": round(order.amount_total, 2),
            },
            'items_list': data['order_line'],
            'customer': {
                "name": order_partner.name,
                "street": order_partner.street,
                "street2": order_partner.street2,
                "city": order_partner.city,
                "zip": order_partner.zip,
                "phone": order_partner.phone,
                "mobile": order_partner.mobile,
                "email": order_partner.email,
            },
            "payment": {
                "method": order.payment_term_id.name,
            },
            "shipping": {
                "carrier": {
                    "carrier_name": shipping.name,
                    "tracking_number": order.id,
                    "awb_link": URL,
                }
            }
        }
        return final

    @http.route('/get_payment_terms', type="json", auth='user', csrf=False, methods=["GET"])
    def get_payment_terms(self, **data):

        all_payment_terms = request.env['account.payment.term'].search([])

        data = {}
        payment_terms = []
        for rec in all_payment_terms:
            vals = {
                'id': rec.id,
                'name': rec.name,
            }
            payment_terms.append(vals)
        if payment_terms:
            data = {
                'status': "200",
                'message': "success",
                'data': payment_terms,
            }
        else:
            data = {
                'status': "400",
                'message': "No Payment Terms",
                'data': payment_terms,
            }
        return data

    @http.route('/get_pricelists', type="json", auth='user', csrf=False, methods=["GET"])
    def get_pricelists(self, **data):

        all_price_lists = request.env['product.pricelist'].search([])

        data = {}
        price_lists = []
        for rec in all_price_lists:
            vals = {
                'id': rec.id,
                'name': rec.name,
            }
            price_lists.append(vals)
        if price_lists:
            data = {
                'status': "200",
                'message': "success",
                'data': price_lists,
            }
        else:
            data = {
                'status': "400",
                'message': "No Price lists",
                'data': price_lists,
            }
        return data

    @http.route('/get_all_customers', type="json", auth='user', csrf=False, methods=["GET"])
    def get_all_customers(self, **data):

        all_customers = request.env['res.partner'].search([])

        data = {}
        customers = []
        for rec in all_customers:
            vals = {
                'id': rec.id,
                'name': rec.name,
            }
            customers.append(vals)
        if customers:
            data = {
                'status': "200",
                'message': "success",
                'data': customers,
            }
        else:
            data = {
                'status': "400",
                'message': "No Customers",
                'data': customers,
            }
        return data

    @http.route('/get_pos_payment_method', type="json", auth='user', csrf=False, methods=["GET"])
    def get_pos_payment_method(self, **data):

        payment_methods = request.env['pos.payment.method'].search([])

        data = {}
        p_methods = []
        for rec in payment_methods:
            vals = {
                'id': rec.id,
                'name': rec.name,
            }
            p_methods.append(vals)
        if p_methods:
            data = {
                'status': "200",
                'message': "success",
                'data': p_methods,
            }
        else:
            data = {
                'status': "400",
                'message': "No Customers",
                'data': p_methods,
            }
        return data

    # @http.route('/get_line_variants', type="json", auth='user', csrf=False, methods=["GET"])
    # def get_line_variants(self, **data):
    #
    #     all_product_variants = request.env['product.variant'].search([])
    #
    #     data = {}
    #     p_line_variants = []
    #     for rec in all_product_variants:
    #         vals = {
    #             'id': rec.id,
    #             'name': rec.name,
    #         }
    #         p_line_variants.append(vals)
    #     if p_line_variants:
    #         data = {
    #             'status': "200",
    #             'message': "success",
    #             'data': p_line_variants,
    #         }
    #     else:
    #         data = {
    #             'status': "400",
    #             'message': "Error ",
    #             'data': p_line_variants,
    #         }
    #     return data

    @http.route('/return_order', type="json", auth='user', csrf=False, methods=["POST"])
    def return_order(self, **data):

        curr_order = request.env['sale.order'].search([('ecom_sale_order_id', '=', data['rma_lines'][0]['ecom_sale_order_id'])])[0]
        all_returned_order = request.env['return.order'].search([])

        if curr_order.name in all_returned_order.mapped('order_name'):
            current_returned_order = request.env['return.order'].search([('order_name', '=', curr_order.name)])
            return {
                'status': "400",
                'message': "Failed",
                'data': "This order is already returned and it's status is "+ current_returned_order.state
            }
        else:
            return_order = request.env['return.order'].create({
                "state": "pending",
                "order_name": curr_order.name,
                "order_id": curr_order.id,
                "reason": data['rma_lines'][0]['reason'],
                "rma_number": data['rma_number'],
                "magento_order_number": data['rma_lines'][0]['magento_order_number'],
            })
            if curr_order.invoice_ids:
                for rec in curr_order.invoice_ids:
                    current_invoice = self.env['account.move'].search([('id', '=', rec.id)])
                    if current_invoice.state == 'draft':
                        test = current_invoice.button_cancel()
                        current_invoice.state == 'cancel'
                        curr_order.delivery_status1 = 'ordered_cancelled'
                        curr_order.state = 'cancel'
                        print('in if')
                    elif current_invoice.state == 'posted':
                        test = current_invoice.action_reverse()
                        print('in elif')
                        current_invoice.state == 'cancel'
                        curr_order.delivery_status1 = 'ordered_cancelled'
                        curr_order.state = 'cancel'
                    else:
                        test = current_invoice.action_reverse()
                        current_invoice.state == 'cancel'
                        curr_order.delivery_status1 = 'ordered_cancelled'
                        curr_order.state = 'cancel'
                        print('in else')
                    # return test
            else:
                curr_order.state = 'cancel'
                curr_order.delivery_status1 = 'ordered_cancelled'

        if return_order:
            return {
                'status': "200",
                'message': "success",
                'data': "You Request Accepted"
            }
        else:
            return {
                'status': "400",
                'message': "Failed",
                'data': "ERROR"
            }

    @http.route('/get_all_products', type="json", auth='public', csrf=False, methods=["GET"])
    def get_all_products(self, **data):

        st_product = request.env['product.product'].search([])

        page_number = int(data.get('page_number', 1))
        per_page = int(data.get('per_page', 10))

        offset = 0 if page_number <= 1 else (page_number - 1) * per_page
        all_products = request.env['product.product'].search(
            [], order="id asc", offset=offset, limit=per_page
        )
        data = {}
        products = []
        for rec in all_products:

            base_url = 'https://babolat.linaegypt.com/'

            image_url_1920 = base_url + 'web/image?' + 'model=product.product&id=' + str(rec.id) + '&field=image_1920'

            # print(image_url_1920)

            variants = []
            for line in rec.attribute_line_ids:
                if line.value_ids.attribute_id.name == "Color":
                    variants.append({
                        'name': line.attribute_id.name,
                        'values': line.value_ids.mapped('name')[0],
                        'color_code': line.color_code,
                    })
                else:
                    variants.append({
                        'name': line.attribute_id.name,
                        'values': line.value_ids.mapped('name')[0],
                    })

            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'sales_price': rec.list_price,
                # 'hs_code': rec.hs_code_id.local_code,
                'product_category_id': rec.categ_id.id,
                'product_category_name': rec.categ_id.name,
                'internal_ref': rec.default_code,
                'barcode': rec.barcode,
                'weight': rec.weight,
                'volume': rec.volume,
                'product_variants': variants,
                'on_hand': rec.qty_available,
                'image': image_url_1920,
            }
            products.append(vals)
        if products:
            data = {
                'status': "200",
                'message': "success",
                'data': products,
                'page_number': page_number if page_number > 0 else 1,
                'per_page': per_page,
                'total_products': len(st_product),

            }
        else:
            data = {
                'status': "400",
                'message': "No Products",
                'data': products,
                'page_number': page_number if page_number > 0 else 1,
                'per_page': per_page,
                'total_products': len(st_product),

            }

        return data
