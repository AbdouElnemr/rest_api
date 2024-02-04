# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderEdit(models.Model):
    _inherit = 'sale.order'

    delivery_status = fields.Selection([('quot_created','Quotation Created'),('order_created','Order Created'),('order_invoiced','Order Invoiced'),
                                        ('order_delivered','Order Delivered'),('ordered_cancelled','Order Cancelled')],
                    string="Delivery Status",
                    copy=False,store=True,readonly=True,
                    default="quot_created")

    @api.model
    def create(self, vals):
        print("lllllllllll", vals)
        return super(SaleOrderEdit, self).create(vals)


    def return_order(self, order_id):
        current_order = self.env['sale.order'].search([('id', '=',order_id)])
        if current_order:
            if current_order.invoice_ids:
                for rec in current_order.invoice_ids:
                    current_invoice = self.env['account.move'].search([('id', '=', rec.id)])
                    if current_invoice.state == 'draft':
                        test = current_invoice.button_cancel()
                        current_invoice.state == 'cancel'
                        current_order.delivery_status = 'ordered_cancelled'
                        current_order.state = 'cancel'
                        print('in if')
                    elif current_invoice.state == 'posted':
                        test = current_invoice.action_reverse()
                        print('in elif')
                        current_invoice.state == 'cancel'
                        current_order.delivery_status = 'ordered_cancelled'
                        current_order.state = 'cancel'
                    else:
                        test = current_invoice.action_reverse()
                        current_invoice.state == 'cancel'
                        current_order.delivery_status = 'ordered_cancelled'
                        current_order.state = 'cancel'
                        print('in else')
                    return test
            else:
                current_order.state = 'cancel'
                current_order.delivery_status = 'ordered_cancelled'
        else:
            print('no sale order')

    def action_confirm_with_id(self, id):
        current_order  = self.env['sale.order'].search([('id', '=', id)])
        if current_order:
            current_order.state = 'sale'
            current_order.delivery_status = 'order_created'

    def get_order_status(self, id):
        current_order  = self.env['sale.order'].search([('id', '=', id)])
        if current_order:
            d_s = ''
            if current_order.delivery_status == 'quot_created':
                d_s = 'Quotation Created'
            if current_order.delivery_status == 'order_created':
                d_s = 'Order Created'
            if current_order.delivery_status == 'order_invoiced':
                d_s = 'Order Invoiced'
            if current_order.delivery_status == 'order_delivered':
                d_s = 'Order Delivered'
            if current_order.delivery_status == 'ordered_cancelled':
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
            order.sale_id.delivery_status = 'order_delivered'
        return super(OrderDone, self).process()


class OrderPayment(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'


    def create_invoices(self):
        print("invooooooooooooooo", self)

        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
            order.delivery_status = 'order_invoiced'
        return super(OrderPayment, self).create_invoices()

class PARTNER(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        print("lllllllllll", vals)
        return super(PARTNER, self).create(vals)
