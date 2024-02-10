# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class exportmagento2xcategories(models.TransientModel):
    _inherit = ['export.categories']
    _name = "export.categories"

    @api.model
    def magento2x_get_category_data(self, category_id, channel_id):
        store_parent_id = 2
        if category_id.parent_id:
            store_parent_id = self.channel_id.match_category_mappings(
                odoo_category_id =category_id.parent_id.id
            ).store_category_id
        data = {
          "parent_id": int(store_parent_id),
          "name": category_id.name,
          "is_active": True,

        }
        return data


    @api.model
    def magento2x_create_category_data(self, sdk, category_id,  channel_id):
        mapping_obj = self.env['channel.category.mappings']
        result=dict(
            mapping_id=None,
            message=''
        )
        mapping_id = None
        data_res = self.magento2x_get_category_data(
            category_id = category_id,
            channel_id = channel_id,
        )
        categories_res =sdk.post_categories(data_res)
        data = categories_res.get('data')
        if not data:
            result['message']+=categories_res.get('message')
            return result
        else:
            store_id  =data.get('id')
            mapping_id = channel_id.create_category_mapping(
                erp_id=category_id,
                store_id=store_id,
                leaf_category=True if not category_id.child_id else False
            )
            result['mapping_id'] = mapping_id

        return result

    @api.model
    def magento2x_update_category_data(self,sdk,channel_id,category_id):
        mapping_obj = self.env['channel.category.mappings']
        result=dict(
            mapping_id=None,
            message=''
        )
        mapping_id = None
        match = self.channel_id.match_category_mappings(
            odoo_category_id =category_id.id
        )
        if not match:
            result['message']+='Mapping not exits for category %s [%s].'%(category_id.name,category_id.id)
        else:
            category_data = self.magento2x_get_category_data(
                category_id = category_id,
                channel_id = channel_id
            )
            data =sdk.post_categories(
                data = category_data,
                category_id = match.store_category_id
            )
            msz = data.get('message','')
            if msz: result['message']+='While Category %s Update %s'%(category_data.get('name'),data.get('message',''))
            mapping_id=match
            match.need_sync='no'
        result['mapping_id']=mapping_id
        return result



    @api.model
    def magento2x_post_categories_data(self,sdk,channel_id,category_ids):
        message = ''
        create_ids = self.env['channel.category.mappings']
        update_ids = self.env['channel.category.mappings']

        operation = self.operation
        category_dict = dict()
        status = True
        for category_id in category_ids.sorted('id'):
            category_obj_id = category_id.id
            message += '<br/>==>For Category %s [%s] Operation (%s) <br/>'%(category_id.name,category_obj_id,operation)
            try:
                sync_vals = dict(
                    status ='error',
                    action_on ='category',
                    action_type ='export',
                    odoo_id = category_obj_id
                )
                post_res = dict()
                if operation == 'export':
                    post_res=self.magento2x_create_category_data(sdk,category_id,channel_id)
                    if post_res.get('mapping_id'):
                        create_ids+=post_res.get('mapping_id')
                else:
                    post_res=self.magento2x_update_category_data(sdk,channel_id,category_id)
                    if post_res.get('mapping_id'):
                        update_ids+=post_res.get('mapping_id')
                msz = post_res.get('message')
                if status and msz:
                    status = False
                if post_res.get('mapping_id'):
                    sync_vals['status'] = 'success'
                    message +='<br/> Category ID[%s]  Operation(%s) done.'%(category_obj_id,operation)
                    sync_vals['ecomstore_refrence'] =post_res.get('mapping_id').store_category_id
                sync_vals['summary'] = msz or '%s %sed'%(category_id.name,operation)
                channel_id._create_sync(sync_vals)
                if msz:message += '%r' % msz
            except Exception as e:
                message += ' %r' % e
        self._cr.commit()
        return dict(
            status  = status,
            message=message,
            update_ids=update_ids,
            create_ids=create_ids,

        )


    def magento2x_export_categories(self):
        message = ''
        ex_create_ids,ex_update_ids,create_ids,update_ids= [],[],[],[]
        for record in self:
            channel_id = record.channel_id
            res =channel_id.get_magento2x_sdk()
            sdk = res.get('sdk')
            if not sdk:
                message+=res.get('message')
            else:
                exclude_res=record.exclude_export_data(
                    record.category_ids,channel_id,record.operation,model='category'
                )
                categories=exclude_res.get('object_ids')

                if not len(categories):
                    message+='No category filter for %s over magento'%(record.operation)
                else:
                    post_res=record.magento2x_post_categories_data(sdk,channel_id,categories)
                    create_ids+=post_res.get('create_ids')
                    update_ids+=post_res.get('update_ids')
                    message+=post_res.get('message')
        message+=self.env['multi.channel.sale'].get_operation_message_v1(
            obj = 'product category',
            obj_model = '',
            operation = 'exported',
            obj_ids = create_ids
        )
        message+=self.env['multi.channel.sale'].get_operation_message_v1(
            obj = 'product category',
            obj_model = '',
            operation = 'updated',
            obj_ids = update_ids
        )
        return self.env['multi.channel.sale'].display_message(message)
