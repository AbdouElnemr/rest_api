# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import fields, models, api

class Feed(models.Model):
    _inherit = ['wk.feed']
    @api.model
    def get_extra_categ_ids(self, store_categ_ids,channel_id):
        if channel_id.channel=='magento2x' and channel_id.magneto2x_default_store_id:
            channel_id = channel_id.magneto2x_default_store_id
        return super(Feed,self).get_extra_categ_ids(store_categ_ids,channel_id)

    @api.model
    def get_order_partner_id(self, store_partner_id,channel_id):
        if channel_id.channel=='magento2x' and channel_id.magneto2x_default_store_id:
            channel_id = channel_id.magneto2x_default_store_id
        return super(Feed,self).get_order_partner_id(store_partner_id,channel_id)


class ChannelProductMappings(models.Model):
    _inherit = ['channel.product.mappings']
    @api.model
    def create(self,vals):
        if (vals.get('ecom_store')=='magento2x') and  vals.get('store_product_id') and (vals.get('store_variant_id')=='No Variants'):
            vals['store_variant_id'] = vals.get('store_product_id')
        return super(ChannelProductMappings,self).create(vals)
    def write(self,vals):
        if (vals.get('ecom_store')=='magento2x') and  vals.get('store_product_id') and (vals.get('store_variant_id')=='No Variants'):
            vals['store_variant_id'] = vals.get('store_product_id')
        return super(ChannelProductMappings,self).write(vals)
