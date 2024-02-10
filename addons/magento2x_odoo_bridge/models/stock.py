# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    You should have received a copy of the License along with this program.
#    If not, see <https://store.webkul.com/license.html/>
#################################################################################
from itertools import groupby
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

# store_product_id
# store_variant_id
class StockMove(models.Model):
    _inherit = "stock.move"
    @api.model
    def sync_magento2x_item(self,channel_id,mapping,product_qty,sdk):
        result = {'data': {}, 'message': ''}
        store_id = mapping.store_product_id
        sku = mapping.default_code
        item = sdk.get_products(sku)
        product_data = item.get('data') or dict()
        qty_available = 0
        extension_attributes = product_data.get('extension_attributes')
        if extension_attributes and extension_attributes.get('stock_item').get('qty'):
            qty_available = int(extension_attributes.get('stock_item').get('qty'))
            qty_available += product_qty
        if qty_available:
            data=dict(
                sku = mapping.default_code,
                extension_attributes=dict(
                    stock_item=dict(
                       qty= qty_available,
                       is_in_stock= qty_available >0 and 1 or 0,
                    )
                ),
            )
            res=sdk.post_products(data,sku=mapping.default_code)
            result.update(res)
        return result

    @api.model
    def sync_magento2x_items(self,mappings,product_qty,source_loc_id,dest_loc_id):
        mapping_items = groupby(mappings, lambda item: item.channel_id)
        message=''
        for channel_id,mapping_item in groupby(mappings, lambda item: item.channel_id):
            product_qty = channel_id.location_id.id == dest_loc_id and product_qty or -(product_qty)
            product_mapping =list(mapping_item)
            items=[]
            for  m in product_mapping:items += [('product_id',m.store_product_id)]
            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message+=res.pop('message')
            else:
                for mapping in product_mapping:
                    sync_res = self.sync_magento2x_item(channel_id,mapping,product_qty,sdk)
                    message+=sync_res.get('message')
        return True
    def multichannel_sync_quantity(self, pick_details):

        product_id = pick_details.get('product_id')
        product_qty = pick_details.get('product_qty')
        source_loc_id = pick_details.get('source_loc_id')
        dest_loc_id = pick_details.get('location_dest_id')
        channel_ids = pick_details.get('channel_ids')
        product_obj = self.env['product.product'].browse(pick_details.get('product_id'))
        channels = self.env['multi.channel.sale'].search(
            [('id','in',channel_ids),('channel','=','magento2x'),('auto_sync_stock','=',True)],
        )
        mappings = product_obj.channel_mapping_ids.filtered(
            lambda m:m.channel_id in channels
            and m.channel_id.location_id.id in [source_loc_id,dest_loc_id]
        )
        if mappings:
            self.sync_magento2x_items(mappings,product_qty,source_loc_id,dest_loc_id)
        return super(StockMove,self).multichannel_sync_quantity(pick_details)
