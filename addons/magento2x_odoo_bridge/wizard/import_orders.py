# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.exceptions import UserError,RedirectWarning, ValidationError
from odoo.addons.odoo_multi_channel_sale.tools import chunks,get_hash_dict,wk_cmp_dict,ensure_string as ES
from odoo.addons.magento2x_odoo_bridge.tools.const import CHANNELDOMAIN
OrderStatus = [
    ('all','All'),
    ('canceled','Canceled'),
    ('closed','Closed'),
    ('complete','Complete'),
    ('processing','Processing'),
    ('holded','On Hold'),
    ('pending','Pending'),
    ('pending_payment','Pending Payment'),
]

class ImportOrders(models.TransientModel):
    _inherit = ['import.orders']
    _name = 'import.magento2x.orders'
    _description = 'import.magento2x.orders'
    status = fields.Selection(
        OrderStatus,
        required=1,
        default='all'
    )
    def import_products(self,product_tmpl_ids):
        product_tmpl_ids = [str(pt) for pt in product_tmpl_ids]
        mapping_obj = self.env['channel.product.mappings']
        domain = [('store_variant_id', 'in',product_tmpl_ids)]
        channel_id = self.channel_id
        mapped = channel_id._match_mapping(mapping_obj,domain).mapped('store_variant_id')
        product_tmpl_ids=list(set(product_tmpl_ids)-set(mapped))
        if len(product_tmpl_ids):
            feed_domain = [('store_id', 'in',product_tmpl_ids)]
            product_feeds = channel_id.match_product_feeds(domain=feed_domain,limit=0).mapped('store_id')
            product_tmpl_ids=list(set(product_tmpl_ids)-set(product_feeds))
            if len(product_tmpl_ids):
                feed_domain = [('store_id', 'in',product_tmpl_ids)]
                product_variant_feeds = channel_id.match_product_variant_feeds(domain=feed_domain,limit=0).mapped('store_id')
                product_tmpl_ids=list(set(product_tmpl_ids)-set(product_variant_feeds))
        message=''
        if len(product_tmpl_ids):
            message='For order product imported %s'%(product_tmpl_ids)
            try:
                import_product_obj=self.env['import.magento2x.products']
                vals =dict(
                    channel_id=channel_id.id,
                    operation= 'import',
                )
                import_product_id=import_product_obj.create(vals)
                context = dict(self._context)
                context['get_date']= False
                import_product_id.with_context(context).import_now()
                self._cr.commit()
            except Exception as e:
                message = "Error while  order product import %r"%(e)
                # mapped = self.channel_id._match_mapping(mapping_obj,domain)
            return message
    def update_shipping_info(self,order_items,order_data,price):
        name = 'Magento %s'%(order_data.get('shipping_description'))
        order_items+=[dict(
            product_id=name,
            price=price,
            qty_ordered=1,
            name=name,
            line_source ='delivery',
            description=name,
            tax_amount ='0',
        )]
        return order_items
    def get_discount_line_info(self,price):
        name = '%s discount'%(price)
        return dict(
            product_id=name,
            price='%s'%(abs(float(price))),
            qty_ordered=1,
            name=name,
            line_source ='discount',
            description=name,
            tax_amount ='0',
        )
    def magento2x_get_tax_line(self,item):
        tax_percent = float(item.get('tax_percent'))
        tax_type = 'percent'
        name = '{}_{} {} % '.format(self.channel_id.channel,self.channel_id.id,tax_percent)
        return {
            'rate':tax_percent,
            'name':name,
            'include_in_price':self.channel_id.magento2x_default_tax_type== 'include'and True or False,
            'tax_type':tax_type
        }
    def magento2x_get_order_line_info(self,order_item):
        product_id=order_item.get('product_id')
        line_price_unit = order_item.get('price')
        original_price = order_item.get('original_price')
        if order_item.get('line_source') not in ['discount','delivery']:
            if self.channel_id.magento2x_default_tax_type=='include'  :
                line_price_unit =  order_item.get('price_incl_tax') and order_item.get('price_incl_tax') or order_item.get('price')
        #if original_price and (line_price_unit!=original_price):
        #    line_price_unit = original_price
        line=None
        line_product_default_code = order_item.get('sku')
        if product_id:
            line_product_id=None
            line_variant_ids= product_id

            if order_item.get('line_source') not in ['discount','delivery']:
                line_product_id=self.channel_id.match_product_mappings(line_variant_ids=product_id).store_product_id
                if not line_product_id:
                    line_product_id = self.channel_id.match_product_feeds(product_id).store_id
                    if not line_product_id:
                        variant_feeds = self.channel_id.match_product_variant_feeds(product_id)
                        # if variant_feeds:
                        line_variant_ids =variant_feeds.store_id
                        line_product_id =variant_feeds.feed_templ_id.store_id
                line=dict(
                    line_product_uom_qty = order_item.get('qty_ordered'),
                    line_variant_ids =line_variant_ids,
                    line_product_id=line_product_id,
                    line_product_default_code=line_product_default_code,
                    line_name = order_item.get('name'),
                    line_price_unit=line_price_unit ,
                    line_source = order_item.get('line_source','product'),
                )
            else:
                line=dict(
                    line_product_uom_qty = order_item.get('qty_ordered'),
                    line_variant_ids =line_variant_ids,
                    line_product_id=line_product_id,
                    line_product_default_code=line_product_default_code,
                    line_name = order_item.get('name'),
                    line_price_unit=line_price_unit ,
                    line_source = order_item.get('line_source','product'),
                )
        return line

    @staticmethod
    def manage_configurable_items(items):
        return list(filter(lambda i:i.get('product_type')!='configurable',items))

    def magento2x_get_discount_amount(self,order_item):
        discount_amount = 0
        if order_item.get('line_source') not in ['delivery','discount']:
            qty_ordered = float(order_item.get('qty_ordered'))
            discount_amount = float(order_item.get('original_price'))*qty_ordered-float(order_item.get('price'))*qty_ordered
            code_discount_amount = float(order_item.get('discount_amount','0'))
            if code_discount_amount:
                discount_amount += code_discount_amount
        return discount_amount

    def magento2x_get_order_item(self,order_item):
        res = None
        parent_item = order_item.get('parent_item')
        if parent_item and parent_item.get('product_type')=='configurable':
            res = parent_item
            res['product_id'] = order_item.get('product_id')
            res['name'] = order_item.get('name')
        else:
            res = order_item
        return res

    def magento2x_get_discount_order_line(self,order_item):
        #discount_amount = self.magento2x_get_discount_amount(order_item)
        discount_amount = float(order_item.get('discount_amount','0'))
        if discount_amount:
            discount_data = self.get_discount_line_info(discount_amount)
            discount_line=self.magento2x_get_order_line_info(discount_data)
            if float(order_item.get('tax_percent','0.0')):
                discount_data['tax_percent'] = order_item.get('tax_percent','0.0')
                discount_line['line_taxes'] = [self.magento2x_get_tax_line(discount_data)]
            return discount_line

    def magento2x_get_order_line(self,order_id,carrier_id,order_data):
        data=dict()
        order_items=order_data.get('items')

        order_items = self.manage_configurable_items(order_items)
        message=''
        default_tax_type = self.channel_id.magento2x_default_tax_type
        lines=[]
        if order_items:
            shipping_amount= order_data.get('shipping_incl_tax')

            if carrier_id and float(shipping_amount):
                order_items= self.update_shipping_info(
                    order_items,order_data,shipping_amount
                )

            size = len(order_items)
            for order_item in order_items:
                order_item = self.magento2x_get_order_item(order_item)
                line=self.magento2x_get_order_line_info(order_item)
                if float(order_item.get('tax_percent','0.0')):
                    line['line_taxes'] = [self.magento2x_get_tax_line(order_item)]
                #discount_amount  = self.magento2x_get_discount_amount(order_item)
                #if discount_amount:
                #   line['discount']=discount_amount
                lines += [(0, 0, line)]
                discount_line  =self.magento2x_get_discount_order_line(order_item)
                if discount_line:
                    lines += [(0, 0, discount_line)]
                elif size==1:
                    data.update(line)
                    lines=[]

        data['line_ids'] = lines
        data['line_type'] = len(lines) >1 and 'multi' or 'single'
        return dict(
            data=data,
            message=message
            )
    def get_mage_invoice_address(self,item,customer_email):
        name = item.get('firstname')
        if item.get('lastname'):
            name+=' %s'%(item.get('lastname'))
        email = item.get('email') or customer_email
        street = item.get('street')
        invoice_street= invoice_street2=''
        if len(street):
            invoice_street = item.get('street')[0]
            if len(street)>1:
                invoice_street2 = ' '.join(item.get('street')[1:])

        return dict(
            invoice_name=name,
            invoice_email=email,
            invoice_street=invoice_street,
            invoice_street2=invoice_street2,
            invoice_phone=item.get('telephone'),
            invoice_city=item.get('city'),
            invoice_country_id=item.get('country_id'),
            invoice_partner_id=item.get('customer_address_id') or '0',
            invoice_zip=item.get('postcode'),
            invoice_state_name=item.get('region'),
        )
    def get_mage_shipping_address(self,item,customer_email):
        name = item.get('firstname')
        if item.get('lastname'):
            name+=' %s'%(item.get('lastname'))
        email = item.get('email') or customer_email
        street = item.get('street')
        shipping_street= shipping_street2=''
        if len(street):
            shipping_street = item.get('street')[0]
            if len(street)>1:
                shipping_street2 = ' '.join(item.get('street')[1:])


        return dict(
            shipping_name=name,
            shipping_email=email,
            shipping_street=shipping_street,
            shipping_street2=shipping_street2,

            shipping_phone=item.get('telephone'),
            shipping_city=item.get('city'),
            shipping_country_id=item.get('country_id'),
            shipping_zip=item.get('postcode'),
            invoice_state_name=item.get('region'),
        )
    def get_order_vals(self,sdk,increment_id,status,order_data):
        message = ''
        channel_id =self.channel_id
        pricelist_id = channel_id.pricelist_name
        if order_data.get('items'):
            item = order_data
            customer_name = item.get('customer_firstname')
            if item.get('customer_lastname'):
                customer_name+=" %s"%(item.get('customer_lastname'))
            customer_email=item.get('customer_email')
            vals = dict(
                order_state = status,
                partner_id=item.get('customer_id') or '0' ,
                customer_is_guest = int(item.get('customer_is_guest')),
                currency = item.get('order_currency_code'),
                customer_name=customer_name,
                customer_email=customer_email,
                payment_method = item.get('payment').get('method'),
            )
            shipping = item.get('extension_attributes',{}).get('shipping_assignments',{})[0].get('shipping')
            shipping_method = shipping.get('method')
            shipping_mapping_id = self.env['shipping.feed'].get_shiping_carrier_mapping(
                channel_id, shipping_method
            )
            if shipping_mapping_id:
                vals['carrier_id']= shipping_mapping_id.shipping_service_id
            line_res= self.magento2x_get_order_line(
                increment_id,
                shipping_mapping_id.odoo_shipping_carrier,item
            )
            if line_res.get('data'):
                vals.update(line_res.get('data'))
            billing_address=item.get('billing_address') or {}
            shipping_address = shipping.get('address')
            billing_hash = channel_id.get_magento2x_address_hash(billing_address)
            shipping_hash = channel_id.get_magento2x_address_hash(shipping_address or {})
            same_shipping_billing = billing_hash==shipping_hash
            vals['same_shipping_billing'] =same_shipping_billing
            billing_address['customer_address_id'] = billing_hash
            billing_addr_vals = self.get_mage_invoice_address(billing_address,customer_email)
            vals.update(billing_addr_vals)
            if shipping_address and not(same_shipping_billing):
                shipping_add_vals = self.get_mage_shipping_address(shipping_address,customer_email)
                shipping_add_vals['shipping_partner_id'] = shipping_hash
                vals.update(shipping_add_vals)
            if not vals.get('customer_name'):
                vals['customer_name'] = vals.get('invoice_name') or vals.get('shipping_name')
            return vals
        else:
            message+=res.get('message')

    def _magento2x_update_order_feed(self,sdk,mapping,entity_id,increment_id,status,data):
        vals =self.get_order_vals(sdk,increment_id,status,data)
        mapping.write(dict(line_ids=[(5,0)]))
        vals['state'] = 'update'
        mapping.write(vals)
        return mapping

    def _magento2x_create_order_feed(self,sdk,entity_id,increment_id, status, data):
        vals =self.get_order_vals(sdk,increment_id,status,data)
        vals['store_id'] =increment_id
        vals['store_source'] =entity_id
        vals['name'] =increment_id
        feed_obj = self.env['order.feed']
        feed_id = self.channel_id._create_feed(feed_obj, vals)
        return feed_id

    def _magento2x_import_order(self, sdk, entity_id, increment_id,status, data):
        feed_obj = self.env['order.feed']
        match = self.channel_id._match_feed(
            feed_obj, [('store_id', '=', increment_id)])
        update =False
        if match :
            self._magento2x_update_order_feed( sdk, match, entity_id, increment_id, status, data)
            update=True
        else:
            match= self._magento2x_create_order_feed(sdk, entity_id, increment_id, status, data)
        return dict(
            feed_id=match,
            update=update
        )
    def _magento2x_import_orders_status(self,sdk,store_id,channel_id):

        message = ''
        update_ids = []
        order_state_ids = channel_id.order_state_ids
        default_order_state = order_state_ids.filtered('default_order_state')
        store_order_ids = channel_id.match_order_mappings(
            limit=None).filtered(lambda item:item.order_name.state=='draft'
            ).mapped('store_order_id')
        if not store_order_ids:
            message += 'No order mapping exits'
        else:
            for store_order_id_chunk in chunks(store_order_ids,channel_id.api_record_limit):
                params = {
                    "searchCriteria[filter_groups][0][filters][0][field]": 'increment_id',
                    "searchCriteria[filter_groups][0][filters][0][value]": ','.join(map(str,store_order_id_chunk)),
                    "searchCriteria[filter_groups][0][filters][0][condition_type]": 'in',
                }
                params['fields'] ='items[store_id,payment,increment_id,status]'
                fetch_data=sdk.get_orders(params=params)
                data = fetch_data.get('data') or {}
                message += fetch_data.get('message')
                if not data:
                    continue
                items = data.get('items',[])
                for item in items:
                    if item.get('store_id')!=store_id: continue
                    res = channel_id.set_order_by_status(
                        channel_id= channel_id,
                        store_id = item.get('increment_id'),
                        status = item.get('status'),
                        order_state_ids = order_state_ids,
                        default_order_state = default_order_state,
                        payment_method =item.get('payment',{}).get('method')
                    )
                    order_match = res.get('order_match')
                    if order_match:update_ids +=[order_match]
                self._cr.commit()
        time_now = fields.Datetime.now()
        all_imported , all_updated = 1,1
        if all_updated and len(update_ids):
            channel_id.update_order_date = time_now
        if not channel_id.import_order_date:
            channel_id.import_order_date = time_now
        return dict(
            update_ids=update_ids,
        )


    def _magento2x_import_orders(self,sdk,store_id,channel_id):
        message = ''
        category_ids = []
        order_state_ids = channel_id.order_state_ids
        default_order_state = order_state_ids.filtered('default_order_state')

        feed_obj = self.env['order.feed']
        create_ids = self.env['order.feed']
        update_ids = self.env['order.feed']
        operation = self.operation
        page_size = channel_id.api_record_limit#
        page_len = channel_id.api_record_limit#
        current_page = 1
        import_products = False
        while page_len==page_size:
            if page_len==page_size==1 and current_page==2:break
            fetch_data = channel_id._fetch_magento2x_order_data(
                sdk=sdk,
                store_id=store_id,
                current_page = current_page,
                page_size = page_size,
                operation = operation,
                update_date = channel_id.update_order_date,#
                import_date = channel_id.import_order_date#
            )
            data = fetch_data.get('data') or {}
            msz = fetch_data.get('message','')
            message+=msz
            current_page+=1
            if (not data) or msz:
                break

            items = data.get('items',[])
            page_len = len(items)
            product_ids = []
            for order_item in items:
                for product_item in order_item.get('items'):
                    product_ids+=[product_item.get('product_id')]

            if not (import_products and len(product_ids)):
                import_products = self.import_products(product_ids)
            for item in items:
                if item.get('store_id')!=store_id: continue
                increment_id = item.get('increment_id')
                entity_id = item.get('entity_id')
                status = item.get('status')
                match = self.channel_id._match_feed(
                    feed_obj, [('store_id', '=', increment_id),('state','!=','error')])
                if match and operation=='import':
                    res = channel_id.set_order_by_status(
                        channel_id= channel_id,
                        store_id = increment_id,
                        status = status,
                        order_state_ids = order_state_ids,
                        default_order_state = default_order_state,
                        payment_method =item.get('payment',{}).get('method')
                    )
                    order_match = res.get('order_match')
                    if order_match:update_ids +=match
                else:
                    import_res =   self._magento2x_import_order(sdk,entity_id,increment_id,status, item)
                    feed_id = import_res.get('feed_id')
                    if  import_res.get('update'):
                        update_ids+=feed_id
                    else:
                        create_ids+=feed_id
            self._cr.commit()
        time_now = fields.Datetime.now()
        all_imported , all_updated = 1,1
        if operation == 'import':
            if all_imported and len(create_ids):
                channel_id.import_order_date = time_now
            if not channel_id.update_order_date:
                channel_id.update_order_date = time_now
        else:
            if all_updated and len(update_ids):
                channel_id.update_order_date = time_now
            if not channel_id.import_order_date:
                channel_id.import_order_date = time_now
        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
            message = message,
        )

    def import_now(self):
        create_ids,update_ids,map_create_ids,map_update_ids=[],[],[],[]
        message=''
        for record in self:
            channel_id=record.channel_id
            store_id =channel_id.get_magento2x_store_config(channel_id,'id')
            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message+=res.get('message')
            else:
                feed_res=record._magento2x_import_orders(sdk, store_id, channel_id)
                message+=feed_res.get('message','')
                post_res = self.post_feed_import_process(channel_id,feed_res)
                create_ids+=post_res.get('create_ids')
                update_ids+=post_res.get('update_ids')
                map_create_ids+=post_res.get('map_create_ids')
                map_update_ids+=post_res.get('map_update_ids')
                if len(create_ids):channel_id.set_channel_date('import','order')
                if len(update_ids):channel_id.set_channel_date('update','order')
        message+=self.env['multi.channel.sale'].get_feed_import_message(
            'order',create_ids,update_ids,map_create_ids,map_update_ids
        )
        return self.env['multi.channel.sale'].display_message(message)
    @api.model
    def _cron_magento2x_import_orders(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            vals =dict(
                channel_id=channel_id.id,
                source='all',
                operation= 'import',
            )
            obj=self.create(vals)
            obj.import_now()
    @api.model
    def _cron_magento2x_import_orders_status(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            message = ''
            import_res = None
            vals =dict(
                channel_id=channel_id.id,
                source='all',
                operation= 'import',
            )
            obj=self.create(vals)
            store_id =channel_id.get_magento2x_store_config(channel_id,'id')
            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message+=res.get('message')
            else:
                import_res = obj._magento2x_import_orders_status(sdk,store_id,channel_id)
