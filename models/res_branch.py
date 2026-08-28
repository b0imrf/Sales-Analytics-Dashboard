# -*- coding: utf-8 -*-
from odoo import models, fields

class ResBranch(models.Model):
    _name = "res.branch"
    _description = "Branch"
    _order = "name"

    name = fields.Char(string="Branch Name", required=True, translate=True)
    code = fields.Char(string="Branch Code")
    active = fields.Boolean(default=True)
    pos_config_ids = fields.One2many("pos.config", "branch_id", string="POS Configs")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Branch code must be unique!"),
    ]
