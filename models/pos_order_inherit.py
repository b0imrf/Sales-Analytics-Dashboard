# -*- coding: utf-8 -*-
from odoo import models, fields

class PosOrder(models.Model):
    _inherit = "pos.order"

    branch_id = fields.Many2one(
        "res.branch", 
        string="Branch", 
        related="session_id.config_id.branch_id", 
        store=True,
        index=True,
    )
