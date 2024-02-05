# -*- coding: utf-8 -*-


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # pos_receipt_footer = fields.Html(string='Receipt Footer', compute='_compute_pos_receipt_header_footer', readonly=False, store=True)
    # pos_receipt_header = fields.Html(string='Receipt Header', compute='_compute_pos_receipt_header_footer', readonly=False, store=True)


    # pos_receipt_design = fields.Many2one(related='pos_config_id.receipt_design', string="Receipt Design",
    #                                      help="Choose any receipt design", compute='_compute_pos_is_custom_receipt',
    #                                      readonly=False, store=True)
    # pos_design_receipt = fields.Text(related='pos_config_id.design_receipt', string='Receipt XML')
    # pos_is_custom_receipt = fields.Boolean(related='pos_config_id.is_custom_receipt', readonly=False, store=True)
    #
    # @api.depends('pos_is_custom_receipt', 'pos_config_id')
    # def _compute_pos_is_custom_receipt(self):
    #     for res_config in self:
    #         if res_config.pos_is_custom_receipt:
    #             res_config.pos_receipt_design = res_config.pos_config_id.receipt_design
    #         else:
    #             res_config.pos_receipt_design = False
