# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging
import itertools
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.addons.magento2x_odoo_bridge.tools.const import CHANNELDOMAIN
CategoryInfoFields = [
]
Boolean = [

    ('all', 'True/False'),
    ('1', 'True'),
    ('0', 'False'),
]
Source = [
    ('all', 'All'),
    ('parent_categ_id', 'Parent ID'),
]


class Importmagento2xCategories(models.TransientModel):
    _inherit = ['import.categories']
    _name = "import.magento2x.categories"
    _description = "import.magento2x.categories"
    @api.model
    def _get_parent_categ_domain(self):
        res = self._get_ecom_store_domain()
        return res

    source = fields.Selection(Source, required=1, default='all')
    parent_categ_id = fields.Many2one(
        'channel.category.mappings',
        'Parent Category',
        domain = _get_parent_categ_domain
    )
    @staticmethod
    def _magento2x_update_category_feed(match,vals,**kwargs):
        vals['state']='update'
        return match.write(vals)
    @staticmethod
    def _magento2x_create_category_feed(feed_obj,channel_id,  vals,**kwargs):
        return channel_id._create_feed(feed_obj, vals)
    @classmethod
    def _magento2x_import_category(cls, feed_obj,channel_id, category_id, data,**kwargs):
        match = channel_id._match_feed(
            feed_obj, [('store_id', '=', category_id)])
        update =False
        if match:
            update=cls._magento2x_update_category_feed( match,data)
        else:
            match= cls._magento2x_create_category_feed(feed_obj,channel_id,  data)
        return dict(
            feed_id=match,
            update=update
        )
    @staticmethod
    def magento2x_extract_categ_data(data,**kwargs):
        parent_id = int(data.get('parent_id'))
        if parent_id == 1:
            parent_id = None
        return [(
            data.get('id'),
            dict(
            name=data.get('name'),
            store_id=data.get('id'),
            parent_id=parent_id and parent_id or None
            )
        )]
    @classmethod
    def magento2x_get_product_categ_data(cls,data,**kwargs):
        res=[]
        child =len(data.get('children_data'))
        index = 0
        while len(data.get('children_data'))>0:
            item = data.get('children_data')[index]
            res +=cls.magento2x_get_product_categ_data(item)
            res+=cls.magento2x_extract_categ_data(data.get('children_data').pop(index))
        return res
    @classmethod
    def _magento2x_import_categories(cls,feed_obj,channel_id, items,**kwargs):
        create_ids=[]
        update_ids=[]
        categ_items=dict(cls.magento2x_get_product_categ_data(items)+cls.magento2x_extract_categ_data(items))
        for category_id,item in categ_items.items():
            import_res =   cls._magento2x_import_category(feed_obj,channel_id,category_id, item)
            feed_id = import_res.get('feed_id')
            if  import_res.get('update'):
                update_ids.append(feed_id)
            else:
                create_ids.append(feed_id)
        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
        )


    def import_now(self):
        create_ids,update_ids,map_create_ids,map_update_ids=[],[],[],[]
        message=''
        feed_obj = self.env['category.feed']
        for record in self:
            channel_id=record.channel_id
            if channel_id.magento2x_is_child_store:
                default_store_id = channel_id.magneto2x_default_store_id
                if not default_store_id:
                    message+='No parent channel set in configurable .'
                record.write(dict(channel_id=default_store_id.id))
                channel_id = default_store_id
            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message+=res.get('message')
            else:
                fetch_res =sdk.get_categories()
                categories = fetch_res.get('data') or {}
                message+= fetch_res.get('message','')
                if not categories:
                    message+="Category data not received."
                else:
                    feed_res=record._magento2x_import_categories(feed_obj,channel_id,categories)
                    post_res = self.post_feed_import_process(channel_id,feed_res)
                    create_ids+=post_res.get('create_ids')
                    update_ids+=post_res.get('update_ids')
                    map_create_ids+=post_res.get('map_create_ids')
                    map_update_ids+=post_res.get('map_update_ids')
        message+=self.env['multi.channel.sale'].get_feed_import_message(
            'category',create_ids,update_ids,map_create_ids,map_update_ids
        )
        return self.env['multi.channel.sale'].display_message(message)

    @api.model
    def _cron_magento2x_import_categories(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            vals =dict(
                channel_id=channel_id.id,
                source='all',
                operation= 'import',
            )
            obj=self.create(vals)
            obj.import_now()
