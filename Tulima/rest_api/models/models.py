# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLinesEdit(models.Model):
    _inherit = 'sale.order.line'

    product_id = fields.Many2one(comodel_name="product.product", string="Product Variant", required=False, )
    product_template_id = fields.Many2one(comodel_name="product.template", string="Product", required=False, )
    authorized_transaction_ids = fields.Many2many('payment.transaction',  string='Authorized Transactions', copy=False, readonly=True)
    # transaction_ids = fields.Many2many('payment.transaction', 'sale_order_transaction_rel', 'sale_order_id', 'transaction_id',
    #                                    string='Transactions', copy=False, readonly=True)


class SaleOrderEdit(models.Model):
    _inherit = 'sale.order'

    delivery_status1 = fields.Selection([('quot_created','Quotation Created'),('order_created','Order Created'),('order_invoiced','Order Invoiced'),
                                        ('order_confirmed','Order Confirmed'),
                                        ('order_delivered','Order Delivered'),('ordered_cancelled','Order Cancelled')],
                    string="Delivery Status",
                    copy=False,store=True,readonly=True,
                    default='quot_created')
    is_taxcloud = fields.Char()
    is_taxcloud_configured = fields.Char()

    # {
    #     "jsonrpc": "2.0",
    #     "method": "call",
    #     "id": "1",
    #     "params": {
    #         "context": {},
    #         "model": "sale.order",
    #         "method": "create",
    #         "args": [
    #             {
    #                 "partner_id": 10,
    #                 "partner_invoice_id": 10,
    #                 "partner_shipping_id": 10,
    #                 "validity_date": false,
    #                 "date_order": "2023-02-06 17:50:41",
    #                 "pricelist_id": 1,
    #                 "payment_term_id": false,
    #                 "order_line": [
    #                     [
    #                         0,
    #                         "virtual_974",
    #                         {
    #                             "sequence": 10,
    #                             "product_id": 2232,
    #                             "product_template_id": 2303,
    #                             "name": "[101485] PURE AERO + U NCV\nPURE AERO + U NCV",
    #                             "product_uom_qty": 1,
    #                             "product_uom": 1,
    #                             "price_unit": 1314.29,
    #                             "tax_id": [
    #                                 [
    #                                     6,
    #                                     false,
    #                                     [
    #                                         11
    #                                     ]
    #                                 ]
    #                             ],
    #                             "discount": 2
    #                         }
    #                     ],
    #                     [
    #                         0,
    #                         "virtual_984",
    #                         {
    #                             "sequence": 10,
    #                             "product_id": 2246,
    #                             "product_template_id": 2317,
    #                             "name": "[101439] PD TOUR UNSTRUNG NO COVER\nPD TOUR UNSTRUNG NO COVER",
    #                             "product_uom_qty": 1,
    #                             "product_uom": 1,
    #                             "customer_lead": 0,
    #                             "price_unit": 1133.33,
    #                             "tax_id": [
    #                                 [
    #                                     6,
    #                                     false,
    #                                     [
    #                                         11
    #                                     ]
    #                                 ]
    #                             ],
    #                             "discount": 0
    #                         }
    #                     ]
    #                 ]
    #             }
    #         ],
    #         "kwargs": {}
    #     }
    # }
    # @api.model
    # def create(self, vals):
    #     print("lllllllllll", vals)
    #     return super(SaleOrderEdit, self).create(vals)


    def return_order(self, order_id):
        current_order = self.env['sale.order'].search([('id', '=',order_id)])
        if current_order:
            if current_order.invoice_ids:
                for rec in current_order.invoice_ids:
                    current_invoice = self.env['account.move'].search([('id', '=', rec.id)])
                    if current_invoice.state == 'draft':
                        test = current_invoice.button_cancel()
                        current_invoice.state == 'cancel'
                        current_order.delivery_status1 = 'ordered_cancelled'
                        current_order.state = 'cancel'
                        print('in if')
                    elif current_invoice.state == 'posted':
                        test = current_invoice.action_reverse()
                        print('in elif')
                        current_invoice.state == 'cancel'
                        current_order.delivery_status1 = 'ordered_cancelled'
                        current_order.state = 'cancel'
                    else:
                        test = current_invoice.action_reverse()
                        current_invoice.state == 'cancel'
                        current_order.delivery_status1 = 'ordered_cancelled'
                        current_order.state = 'cancel'
                        print('in else')
                    return test
            else:
                current_order.state = 'cancel'
                current_order.delivery_status1 = 'ordered_cancelled'
        else:
            print('no sale order')

    def action_confirm_with_id(self, id):
        current_order  = self.env['sale.order'].search([('id', '=', id)])
        if current_order:
            current_order.state = 'sale'
            current_order.delivery_status1 = 'order_created'

    def get_order_status(self, id):
        current_order  = self.env['sale.order'].search([('id', '=', id)])
        if current_order:
            d_s = ''
            if current_order.delivery_status1 == 'quot_created':
                d_s = 'Quotation Created'
            if current_order.delivery_status1 == 'order_created':
                d_s = 'Order Created'
            if current_order.delivery_status1 == 'order_invoiced':
                d_s = 'Order Invoiced'
            if current_order.delivery_status1 == 'order_delivered':
                d_s = 'Order Delivered'
            if current_order.delivery_status1 == 'ordered_cancelled':
                d_s = 'Order Cancelled'
            data = {
                'status': "200",
                'message': "success",
                'data': d_s,
            }
        else:
            data = {
                'status': "400",
                'message': "No Sale Order",
                'data': '',
            }
        return data




class OrderDone(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        picks = self.env['stock.picking'].browse(self._context.get('active_ids', []))
        for order in picks:
            order.sale_id.delivery_status1 = 'order_delivered'
        return super(OrderDone, self).process()


class OrderPayment(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'


    def create_invoices(self):
        print("invooooooooooooooo", self)

        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
            order.delivery_status1 = 'order_invoiced'
        return super(OrderPayment, self).create_invoices()

class PARTNER(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        print("lllllllllll", vals)
        return super(PARTNER, self).create(vals)


class AttributeLineId(models.Model):
    _inherit = 'product.template.attribute.line'

    color_code = fields.Char(string="Color Code", required=False, )


class ProductAttribute(models.Model):
    _inherit = 'product.attribute.value'

    color_code = fields.Char(string="Color Code", required=False, )


class ProductColoCode(models.Model):
    _inherit = 'product.template'

    color_code = fields.Char(string="Color Code", required=False, )

    # @api.model
    # def create(self, vals):
    #     picture_public = {'public': True}
    #     vals.update(picture_public)
    #     return super().create(vals)

class ProductIMAG(models.Model):
    _inherit = 'product.product'

    # @api.model
    # def create(self, vals):
    #     picture_public = {'public': True}
    #     vals.update(picture_public)
    #     return super().create(vals)

class ReturnOrder(models.Model):
    _name = 'return.order'

    state = fields.Selection(string="State", selection=[('pending', 'Pending'), ('received', 'Received'), ], required=False, )
    order_name = fields.Char(string="Order Name", required=False,)
    order_id = fields.Integer(string="Order Id", required=False,)
    reason = fields.Text(string="Reason", required=False, )
    rma_number = fields.Char(string="RMA Number", required=False, )
    magento_order_number = fields.Char(string="Magento Order Number", required=False, )

    def accept_return_order(self):
        self.state = 'received'