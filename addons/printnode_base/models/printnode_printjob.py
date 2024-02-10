# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class PrintNodePrintJob(models.Model):
    """ PrintNode Job entity
    """

    _name = 'printnode.printjob'
    _description = 'PrintNode Job'

    printnode_id = fields.Integer('Direct Print ID')

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        ondelete='cascade',
    )

    description = fields.Char(
        string='Label',
        size=64
    )
