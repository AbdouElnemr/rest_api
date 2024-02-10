# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.addons.magento2x_odoo_bridge.tools.const import CHANNELDOMAIN
customerInfoFields = [
]
Boolean = [

    ('all', 'True/False'),
    ('1', 'True'),
    ('0', 'False'),
]
Source = [
    ('all', 'All'),
    ('partner_ids', 'Partner ID(s)'),
]


class Importmagento2xpartners(models.TransientModel):
    _inherit = ['import.partners']
    _name = "import.magento2x.partners"
    _description = "import.magento2x.partners"
    @api.model
    def _get_parent_categ_domain(self):
        mapping_obj = self.env['channel.order.mappings']
        domain = []
        ecom_store = self._get_ecom_store_domain()
        return ecom_store
    @api.model
    def _get_magento2x_group(self):
        groups=[('all','All')]
        return groups
    source = fields.Selection(Source, required=1, default='all')
    group_id = fields.Selection(
        selection = _get_magento2x_group,
        string='Group ID',
        required=1,
        default='all'
    )
    @staticmethod
    def _parse_magento2x_customer_address(channel_id,addresses,email,customer_id,**kwargs):
        res=[]
        for item in addresses:
            store_id = channel_id.get_magento2x_address_hash(item)
            name = item.get('firstname')
            if item.get('lastname'):
                name+=' %s'%(item.get('lastname'))
            _type = 'invoice'
            if item.get('default_shipping'):
                _type = 'delivery'
            street=street2=''
            street_list = item.get('street')
            if len(street_list):
                street=street_list[0]
                if len(street_list)>1:
                    street2 = street_list[1]
            vals= dict(
                name=item.get('firstname'),
                last_name = item.get('lastname'),
                email=email,
                street=street,
                street2=street2,
                phone=item.get('telephone'),
                city=item.get('city'),
                state_name=item.get('region').get('region'),
                country_id=item.get('country_id'),
                zip=item.get('postcode'),
                store_id=store_id,
                parent_id = customer_id,
                type=_type
            )
            res+=[vals]
        return res

    @classmethod
    def _magento2x_manage_address(cls,channel_id,customer_id,feed_obj,customer_data,**kwargs):
        addresses = customer_data.get('addresses')
        email = customer_data.get('email')
        if addresses:
            add_vals=cls._parse_magento2x_customer_address(channel_id,addresses,email,customer_id)
            for add_val in add_vals:
                feed_id = channel_id._create_feed(feed_obj, add_val)
                feed_obj += feed_id
        return feed_obj

    @staticmethod
    def get_customer_vals(customer_id,customer_data,**kwargs):
        email = customer_data.get('email')
        vals = dict(
            name=customer_data.get('firstname'),
            last_name = customer_data.get('lastname'),
            email=customer_data.get('email'),
            type = 'contact'
        )
        return vals
    @staticmethod
    def _magento2x_update_customer_feed(match,vals,**kwargs):
        vals['state']='update'
        return match.write(vals)
    @staticmethod
    def _magento2x_create_customer_feed(feed_obj,channel_id, customer_id, vals,**kwargs):
        vals['store_id'] =customer_id
        return  channel_id._create_feed(feed_obj, vals)
    @classmethod
    def _magento2x_import_customer(cls, feed_obj,channel_id,customer_id, data,**kwargs):
        match = channel_id._match_feed(
            feed_obj, [('store_id', '=', customer_id),('type','=','contact')])
        update =False
        vals =cls.get_customer_vals(customer_id,data)
        if match:
            update=cls._magento2x_update_customer_feed(match,vals)
        else:
            match += cls._magento2x_manage_address(channel_id,customer_id,feed_obj,data)
            match += cls._magento2x_create_customer_feed( feed_obj,channel_id, customer_id, vals)
        return dict(
            feed_id=match,
            update=update
        )

    @classmethod
    def _magento2x_import_partners(cls,feed_obj,channel_id,items,**kwargs):
        create_ids=[]
        update_ids=[]
        for item in items:
            customer_id = item.get('id')
            import_res =   cls._magento2x_import_customer(feed_obj,channel_id,customer_id, data=item,**kwargs)
            feed_id = import_res.get('feed_id')
            if  import_res.get('update'):
                update_ids.append(feed_id)
            else:
                create_ids.append(feed_id)


        time_now = fields.Datetime.now()
        if len(create_ids):
            channel_id.import_product_date = time_now
            if not channel_id.update_product_date:
                channel_id.update_product_date = time_now
        if len(update_ids):
            channel_id.update_product_date = time_now
            if not channel_id.import_product_date:
                channel_id.import_product_date = time_now
        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
        )

    def import_now(self):
        create_ids,update_ids,map_create_ids,map_update_ids=[],[],[],[]
        message=''
        feed_obj = self.env['partner.feed']
        for record in self:
            channel_id=record.channel_id

            store_id =record.channel_id.get_magento2x_store_config(channel_id,'id')
            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message+=res.get('message')
            else:
                page_size = channel_id.api_record_limit
                page_len = channel_id.api_record_limit
                current_page=1
                total_count = 100
                param = channel_id._fetch_magento2x_params(
                    operation=self.operation,
                    import_date = channel_id.import_customer_date,
                    update_date = channel_id.import_customer_date,
                    page_size=page_size,
                    current_page=current_page
                )
                partners = list()
                while page_len==page_size:
                    if current_page==total_count+1:break
                    fetch_res =sdk.get_customers(params=param)
                    partner = fetch_res.get('data') or {}
                    total_count = partner.get('total_count')
                    current_page += 1
                    param["searchCriteria[current_page]"] = current_page
                    page_len = len(partner.get('items'))
                    message+= fetch_res.get('message','')
                    partners += partner.get('items')
                if not partners:
                    message+="Partners data not received."
                else:
                    partners = dict(items=partners)
                    partners=filter(lambda i:i.get('store_id'),(partners.get('items') or []))
                    if not partners:
                        message+="Partners data not received for store ID[%s]."%(store_id)
                    else:
                        feed_res=record._magento2x_import_partners(feed_obj,channel_id,partners)
                        post_res = self.post_feed_import_process(channel_id,feed_res)
                        create_ids+=post_res.get('create_ids')
                        update_ids+=post_res.get('update_ids')
                        map_create_ids+=post_res.get('map_create_ids')
                        map_update_ids+=post_res.get('map_update_ids')
                        if len(create_ids):channel_id.set_channel_date('import','customer')
                        if len(update_ids):channel_id.set_channel_date('update','customer')
        message+=self.env['multi.channel.sale'].get_feed_import_message(
            'partner',create_ids,update_ids,map_create_ids,map_update_ids
        )
        return self.env['multi.channel.sale'].display_message(message)
    @api.model
    def _cron_magento2x_import_partners(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            vals =dict(
                channel_id=channel_id.id,
                source='all',
                operation= 'import',
            )
            obj=self.create(vals)
            obj.import_now()
