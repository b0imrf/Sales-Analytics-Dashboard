# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class SalesDashboardController(http.Controller):

    @http.route("/sales_dashboard/get_data", type="json", auth="user")
    def get_dashboard_data(self, date_range="today", section="all", **kw):
        """API endpoint for dashboard data"""
        Dashboard = request.env["sales.dashboard"]
        data = Dashboard.get_dashboard_data(date_range, section)
        return data
