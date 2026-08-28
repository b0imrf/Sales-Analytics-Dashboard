# -*- coding: utf-8 -*-
{
    "name": "Sales Analytics Dashboard",
    "version": "18.0.1.0.0",
    "category": "Sales/Dashboard",
    "summary": "Modern Sales Dashboard with Branches, Employees, POS & Customers Analytics",
    "description": """
        Advanced Sales Dashboard for Odoo 18
        =====================================
        - Main Sales KPIs (Daily/Weekly/Monthly/Yearly)
        - Branch-wise Sales Analytics
        - Employee & Cashier Performance
        - POS Analytics
        - Customer Analytics
        - Modern OWL-based UI with Chart.js
    """,
    "author": "Marouf Alakthire",
    "website": "https://github.com/b0imrf",
    "depends": ["base", "web", "sale", "point_of_sale", "account", "hr"],
    "data": [
        "security/sales_dashboard_security.xml",
        "security/ir.model.access.csv",
        "views/res_branch_views.xml",
        "views/pos_config_views.xml",
        "views/sale_order_views.xml",
        "views/sales_dashboard_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sales_dashboard/static/src/components/sales_dashboard/*",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
