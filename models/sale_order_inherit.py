# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    branch_id = fields.Many2one("res.branch", string="Branch", domain="[('company_id', '=', company_id)]")
