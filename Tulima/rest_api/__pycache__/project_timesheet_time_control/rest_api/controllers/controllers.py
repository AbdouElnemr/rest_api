from odoo import http
from odoo.http import request
from odoo.http import Response
import json
import time
import base64


class ProductsApi(http.Controller):
    @http.route('/web/session/authenticate', type="json", auth='none', method='POST')
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()

    @http.route('/get_all_taxes', type="json", auth='user', csrf=False, method='GET')
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

    @http.route('/get_payment_terms', type="json", auth='user', csrf=False, method='GET')
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

    @http.route('/get_pricelists', type="json", auth='user', csrf=False, method='GET')
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


    @http.route('/get_all_customers', type="json", auth='user', csrf=False, method='GET')
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

    @http.route('/get_pos_payment_method', type="json", auth='user', csrf=False, method='GET')
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

    # @http.route('/get_line_variants', type="json", auth='user', csrf=False, method='GET')
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


    @http.route('/get_all_products', type="json", auth='user', csrf=False, method='GET')
    def get_all_products(self, **data):

        all_products = request.env['product.template'].search([])

        data = {}
        products = []
        for rec in all_products:

            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            image_url_1920 = '/web/image?' + 'model=product.template&id=' + str(rec.id) + '&field=image_1920'

            print(image_url_1920)

            variants = []
            for line in rec.attribute_line_ids:
                variants.append({
                    'name': line.attribute_id.name,
                    'values': line.value_ids.mapped('name'),
                })

            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                # 'sale_ok': rec.sale_ok,
                # 'purchase_ok': rec.purchase_ok,
                # 'standard_price': rec.standard_price,
                'sales_price': rec.list_price,
                'hs_code': rec.hs_code_id.local_code,
                'product_category_id': rec.categ_id.id,
                'product_category_name': rec.categ_id.name,
                'internal_ref': rec.default_code,
                'barcode': rec.barcode,
                # 'description_sale': rec.description_sale,
                # 'description': rec.description,
                'weight': rec.weight,
                'volume': rec.volume,
                'product_variants': variants,
                'on_hand': rec.qty_available,
                'image': image_url_1920,
                # 'origin_country': rec.origin_country_id.name,
                # 'country_state': rec.origin_state_id.name,
                # 'company': rec.company_id.name,
                # 'unit_of_measure': rec.uom_id.name,
                # 'purchase_unit_of_measure': rec.uom_po_id.name,
                # 'product_id_type': rec.wk_product_id_type
            }
            products.append(vals)
        if products:
            data = {
                'status': "200",
                'message': "success",
                'data': products,
            }
        else:
            data = {
                'status': "400",
                'message': "No Products",
                'data': products,
            }
        return data

