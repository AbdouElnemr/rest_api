# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging
import itertools
import binascii
import requests
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.addons.odoo_multi_channel_sale.tools import chunks, extract_item, MapId,IndexItems
from odoo.addons.magento2x_odoo_bridge.tools.const import InfoFields,CHANNELDOMAIN
from odoo.exceptions import  UserError,RedirectWarning, ValidationError
Page_Limit  = 150
Status = [
    ('all', 'All'),
    ('1', 'True'),
    ('0', 'False'),
]

Type  =[
    ('all','All'),
    ('configurable','Configurable Product'),
    ('simple','Simple Product'),
]
OdooType = [
    ('simple','product'),
    ('configurable','product'),
    ('downloadable','service'),#digital
    ('grouped','service'),
    ('virtual','service'),
    ('bundle','service'),
]

class Importmagento2xProducts(models.TransientModel):
    _inherit = ['import.templates']
    _name = "import.magento2x.products"
    _description = "import.magento2x.products"
    magento2x_type = fields.Selection(Type,
        required=1,
        string = 'Product Type',
        default='all'
    )

    @staticmethod
    def _extract_magento2x_categories(item):
        category_ids=[]
        custom_attributes=dict(IndexItems(items=item.get('custom_attributes'),skey='attribute_code'))
        if custom_attributes:
            extract_item_data = custom_attributes.get('category_ids',{}).get('value')
            category_ids+=extract_item_data
        return category_ids

    @staticmethod
    def _import_magento2x_categories(channel_id,obj):
        message=''
        try:
            vals =dict(
                channel_id=channel_id.id,
                source='all',
                operation= 'import',
            )
            import_category_id=obj.create(vals)
            import_category_id.import_now()
        except Exception as e:
            message += "Error while  order product import %s"%(e)
        return message

    @api.model
    def _magento2x_create_product_categories(self,channel_id,category_ids):
        mapping_obj = self.env['channel.category.mappings']
        domain = [('store_category_id', 'in',list(set(category_ids)))]
        mapped = channel_id._match_mapping(mapping_obj,domain).mapped('store_category_id')
        category_ids=list(set(category_ids)-set(mapped))
        if len(category_ids):
            obj=self.env['import.magento2x.categories']
            self._import_magento2x_categories(channel_id,obj)

    @classmethod
    def get_magento2x_product_varinats_data(cls,sdk,product_link_item):
        product_item =sdk.get_products(sku = product_link_item.get('sku')).get('data')
        if not (product_item):
            params = {
                "searchCriteria[filter_groups][0][filters][0][field]": 'entity_id',
                "searchCriteria[filter_groups][0][filters][0][value]": str(product_link_item.get('id')),
                "searchCriteria[filter_groups][0][filters][0][condition_type]": 'in',
            }
            product_item_by_id=(sdk.get_products(params=params).get('data') or {}).get('items') or []
            if product_item_by_id and len(product_item_by_id):
                product_item = product_item_by_id[0]
        return  product_item

    @classmethod
    def get_magento2x_product_varinats(cls,sdk,channel_id,product_data,
            extension_attributes,attributes_list):
        res=[]
        debug = channel_id.debug == 'enable'
        channel_obj_id = channel_id.id
        api_record_limit = channel_id.api_record_limit
        configurable_product_options = extension_attributes.get('configurable_product_options')
        for product_link_ids in chunks(extension_attributes.get('configurable_product_links'),api_record_limit):
            params = {
                "searchCriteria[filter_groups][0][filters][0][field]": 'entity_id',
                "searchCriteria[filter_groups][0][filters][0][value]": ','.join(map(str,product_link_ids)),
                "searchCriteria[filter_groups][0][filters][0][condition_type]": 'in',
            }
            params["fields"]='items[id,sku]'
            if debug:
                _logger.info("=config-simple=%r =%r=%r "%(
                    product_link_ids,product_data['sku'],
                    len(extension_attributes.get('configurable_product_links'))))
            product_link_data=sdk.get_products(params=params).get('data')
            if product_link_data and product_link_data.get('items'):
                for product_link_item in product_link_data.get('items'):
                    product_item = cls.get_magento2x_product_varinats_data(sdk,product_link_item)
                    if (product_item):
        	            vals = cls.get_magento2x_product_vals(
        	                sdk,channel_id,
        	                product_id = product_item.get('id'),
        	                product_data = product_item,
        	                attributes_list = attributes_list,
        	                configurable_product_options = configurable_product_options
        	            )
        	            vals['channel_id']=channel_obj_id
        	            res+=[(0,0,vals)]
            # break
        return res
    @staticmethod
    def get_magento2x_product_name_value(custom_attributes,product_data,
        attributes_list,configurable_product_options):
        custom_attributes_value  = list(map(lambda i:i.get('value'),product_data.get('custom_attributes')))
        name_value_lists = []
        for options in configurable_product_options:
            attribute_id = options.get('attribute_id')
            for value in options.get('values'):
                value_index = value.get('value_index')
                if str(value_index) in custom_attributes_value:
                    filter_attr = None
                    for attr_list in  attributes_list:
                        if attr_list.get('attribute_id')== int(attribute_id):
                            filter_attr =attr_list
                            break

                    if filter_attr:
                        value_name = value_index
                        attr_options = filter_attr.get('options')
                        for option in attr_options:
                            if (option.get('value')  not in [False,None,'']) and int(option.get('value').strip())==value_index:
                                value_name = option.get('label')
                        name_value={
                            'name': options.get('label'),
                            'attrib_name_id': attribute_id,
                            'price': 0,
                            'attrib_value_id':value_index,
                            'value': value_name,
                        }
                        name_value_lists+=[name_value]
        return name_value_lists

    @classmethod
    def get_magento2x_product_vals(cls,sdk,channel_id,product_id,product_data,
        attributes_list=None,
        configurable_product_options=None):
        attributes_list = attributes_list or dict()
        configurable_product_options = configurable_product_options or list()
        type_id=product_data.get('type_id')
        default_code = product_data.get('sku')
        vals = dict(
            name=product_data.get('name'),
            default_code=default_code,
            type = dict(OdooType).get(type_id,'service'),
            store_id=product_id,
            weight = product_data.get('weight'),
            list_price = product_data.get('price'),
            standard_price = product_data.get('cost'),
        )

        custom_attributes=dict(IndexItems(items=product_data.get('custom_attributes'),skey='attribute_code'))
        category_ids=custom_attributes.get('category_ids',{}).get('value',[])
        vals['extra_categ_ids'] = ','.join(category_ids)
        vals['description_sale'] =  extract_item(custom_attributes.get('description'),'value')


        extension_attributes = product_data.get('extension_attributes',{})
        if extension_attributes and len(extension_attributes) and extension_attributes.get('stock_item').get('qty'):
            vals['qty_available'] = int(extension_attributes.get('stock_item').get('qty'))

        if type_id == 'configurable':
            feed_variants =cls.get_magento2x_product_varinats(sdk,channel_id,product_data,
                extension_attributes,attributes_list)
                #extension_attributes  is IMP
            if feed_variants:
                vals['feed_variants']=feed_variants

        else:
            if attributes_list:
                vals['name_value']=cls.get_magento2x_product_name_value(
                                        custom_attributes,product_data,
                                        attributes_list,configurable_product_options
                                    )
        media=product_data.get('media_gallery_entries',[])
        if len(media):
            res_img= channel_id._magento2x_get_product_images_vals(sdk,channel_id,media)
            vals['image'] = res_img.get('image')
            vals['image_url'] = res_img.get('image_url')
        return vals

    @staticmethod
    def _magento2x_update_product_feed(channel_id,match,vals):
        vals['state']='update'
        match.write(dict(feed_variants=[(5,0,0)]))
        return match.write(vals)

    @staticmethod
    def _magento2x_create_product_feed(channel_id, feed_obj,vals):
        return channel_id._create_feed(feed_obj, vals)

    @classmethod
    def _magento2x_import_product(cls, sdk,feed_obj,channel_id,operation,
        product_id,product_data,attributes_list):
        match = channel_id.match_product_feeds(product_id)
        update=False

        if match:
            vals =cls.get_magento2x_product_vals(sdk,channel_id,product_id,
                product_data,attributes_list=attributes_list)
            vals['store_id'] = product_id
            update = cls._magento2x_update_product_feed(channel_id,match,vals)
        else:
            vals =cls.get_magento2x_product_vals(sdk,channel_id,product_id,
                product_data,attributes_list=attributes_list)
            vals['store_id'] = product_id
            match = cls._magento2x_create_product_feed(channel_id, feed_obj,vals)
        return dict(
            feed_id=match,
            update=update
        )
    def magento2x_import_products(self,sdk,feed_obj,
            channel_id,attributes_list,
            type_id='configurable',condition_type='neq'):
        message = ''
        category_ids = []
        create_ids = self.env['product.feed']
        update_ids = self.env['product.feed']
        page_size = self.api_record_limit
        page_len = self.api_record_limit
        operation = self.operation
        debug = channel_id.debug == 'enable'
        current_page = 1
        magento2x_type = 'simple' if condition_type=='neq' else 'configurable'
        while page_len==page_size:
            if page_len==page_size==1 and current_page==2:break
            fetch_data = channel_id._fetch_magento2x_product_data(
                sdk=sdk,
                type_id = type_id,
                condition_type = condition_type,
                current_page = current_page,
                page_size = page_size,
                operation = operation,
                update_date = self._context.get('get_date',1) and  self.update_product_date ,
                import_date =  self._context.get('get_date',1) and self.import_product_date,
                fields = 'items[id,sku]'
            )
            products = fetch_data.get('data') or {}
            msz = fetch_data.get('message','')
            message+=msz
            current_page+=1
            if (not products) or msz:
                break

            page_len = len(products)
            if debug:
                _logger.info("@@@@=%r %r =%r==%r"%(
                    magento2x_type,current_page,page_len,page_size)
                )
            message+= fetch_data.get('message','')
            for product_id,item in products.items():
                if magento2x_type=='simple':# Simple Product Import
                    match_variant_feed  =  channel_id.match_product_variant_feeds(product_id)
                    if match_variant_feed :#Match config child product
                        if debug:
                            _logger.info("match=child simple  %r  %r  "%(
                                product_id,match_variant_feed))
                        continue
                    match_feed  =  channel_id.match_product_feeds(product_id)
                    if match_feed and operation!='update':#Match simple  product
                        if debug:
                            _logger.info("match= simple %r  %r  "%(
                                product_id,match_feed))
                        continue
                product_data = sdk.get_products(item.get('sku')).get('data')
                if not product_data:
                    _logger.info("=NOT product_data==%r==="%(item))
                    #raise Warning(item)
                else:
                    category_ids+=self._extract_magento2x_categories(product_data)

                    import_res =   self._magento2x_import_product(sdk,feed_obj,channel_id,
                                            operation,product_id,product_data,
                                            attributes_list=attributes_list)
                    feed_id = import_res.get('feed_id')
                    if  import_res.get('update') :
                        if operation=='update':
                            update_ids+=feed_id
                        elif operation=='import' and magento2x_type=='configurable':
                            pass
                    else:
                        create_ids+=feed_id
                    self._cr.commit()
        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
            category_ids = category_ids,
            message = message
        )
    def _magento2x_import_products(self,sdk,channel_id):
        message = ''
        category_ids = []
        feed_obj = self.env['product.feed']
        create_ids = self.env['product.feed']
        update_ids = self.env['product.feed']
        operation = self.operation
        debug = channel_id.debug == 'enable'

        attributes_res = channel_id._fetch_magento2x_product_attributes(sdk)
        message+=attributes_res.get('message','')
        attributes_res_data = attributes_res.get('data')
        attributes_list = attributes_res_data and attributes_res_data.get('items')
        magento2x_type = self.magento2x_type
        import_config = self.magento2x_import_products(sdk,feed_obj,channel_id,
            attributes_list, type_id='configurable', condition_type='eq'
            )
        if debug:
            _logger.info("==DONE import_config ==%r===="%(import_config))
        create_ids+=import_config.get('create_ids')
        update_ids+=import_config.get('update_ids')
        category_ids+=import_config.get('category_ids')
        message+=import_config.get('message')
        import_simple = self.magento2x_import_products(sdk,feed_obj,channel_id,
            attributes_list, type_id='configurable', condition_type='neq'
        )
        if debug:
            _logger.info("==DONE import_simple==%r===="%(import_simple))
        create_ids+=import_simple.get('create_ids')
        update_ids+=import_simple.get('update_ids')
        category_ids+=import_simple.get('category_ids')
        message+=import_simple.get('message')

        if len(category_ids):
            self._magento2x_create_product_categories(channel_id,category_ids)
        time_now = fields.Datetime.now()
        all_imported , all_updated = 1,1
        if operation == 'import':
            if all_imported and len(create_ids):
                channel_id.import_product_date = time_now
            if not channel_id.update_product_date:
                channel_id.update_product_date = time_now
        else:
            if all_updated and len(update_ids):
                channel_id.update_product_date = time_now
            if not channel_id.import_product_date:
                channel_id.import_product_date = time_now
        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
            message=message,
        )
    def import_now(self):
        create_ids,update_ids,map_create_ids,map_update_ids =[],[],[],[]
        message=''
        for record in self:
            channel_id = record.channel_id
            operation = record.operation

            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message += sdk.get('message')
            else:
                feed_res=record._magento2x_import_products(sdk,channel_id)
                post_res = self.post_feed_import_process(channel_id,feed_res)
                create_ids+=post_res.get('create_ids')
                update_ids+=post_res.get('update_ids')
                map_create_ids+=post_res.get('map_create_ids')
                map_update_ids+=post_res.get('map_update_ids')
        message+=self.env['multi.channel.sale'].get_feed_import_message(
            'product',create_ids,update_ids,map_create_ids,map_update_ids
        )
        return self.env['multi.channel.sale'].display_message(message)
    @api.model
    def _cron_magento2x_import_products(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            vals =dict(
                channel_id=channel_id.id,
                source='all',
                operation= 'import',
            )
            obj=self.create(vals)
            obj.import_now()
