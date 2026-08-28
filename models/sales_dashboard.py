# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero

class SalesDashboard(models.TransientModel):
    _name = "sales.dashboard"
    _description = "Sales Dashboard"

    # ==================== MAIN KPIs ====================

    @api.model
    def get_main_kpis(self, date_from=None, date_to=None):
        """Return main sales KPIs from BOTH sale.order and pos.order"""

        # --- Sale Orders ---
        so_domain = [("state", "in", ["sale", "done"])]
        if date_from and date_to:
            so_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]

        sale_orders = self.env["sale.order"].search(so_domain)
        so_total = sum(sale_orders.mapped("amount_total"))
        so_count = len(sale_orders)

        # Calculate margin and discounts from order lines
        so_margin = 0
        so_discount = 0
        for order in sale_orders:
            for line in order.order_line:
                # margin = price_subtotal - (cost * qty)
                cost = line.product_id.standard_price if line.product_id else 0
                so_margin += line.price_subtotal - (cost * line.product_uom_qty)
                if line.discount > 0:
                    original = line.price_unit * line.product_uom_qty
                    so_discount += (original - line.price_subtotal)

        # --- POS Orders ---
        po_domain = [("state", "in", ["draft", "paid", "done"])]
        if date_from and date_to:
            po_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]

        pos_orders = self.env["pos.order"].search(po_domain)
        po_total = sum(pos_orders.mapped("amount_total"))
        po_count = len(pos_orders)

        # POS margin and discounts
        po_margin = 0
        po_discount = 0
        for order in pos_orders:
            for line in order.lines:
                if hasattr(line, 'margin'):
                    po_margin += line.margin
                po_discount += (line.price_unit * line.qty) - line.price_subtotal_incl

        # --- Combined ---
        total_sales = so_total + po_total
        total_orders = so_count + po_count
        avg_order = total_sales / total_orders if total_orders else 0
        net_sales = total_sales
        discount_amount = so_discount + po_discount

        # Returns (POS only)
        refund_orders = pos_orders.filtered(lambda o: o.amount_total < 0 or o.refunded_order_id)
        total_returns = abs(sum(refund_orders.mapped("amount_total")))
        return_count = len(refund_orders)

        # Profit & Margin
        total_margin = so_margin + po_margin
        margin_percent = (total_margin / total_sales * 100) if total_sales else 0

        # Comparison
        prev_kpis = self._get_comparison_data(date_from, date_to)

        return {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "avg_order": avg_order,
            "net_sales": net_sales,
            "discount_amount": discount_amount,
            "total_returns": total_returns,
            "return_count": return_count,
            "total_margin": total_margin,
            "margin_percent": margin_percent,
            "prev_total_sales": prev_kpis["total_sales"],
            "prev_total_orders": prev_kpis["total_orders"],
            "sales_growth": prev_kpis["sales_growth"],
        }

    def _get_comparison_data(self, date_from, date_to):
        if not date_from or not date_to:
            return {"total_sales": 0, "total_orders": 0, "sales_growth": 0}

        try:
            df = fields.Date.from_string(date_from)
            dt = fields.Date.from_string(date_to)
            delta = (dt - df).days + 1

            prev_df = df - timedelta(days=delta)
            prev_dt = dt - timedelta(days=delta)

            # Previous period sale orders
            prev_so = self.env["sale.order"].search([
                ("state", "in", ["sale", "done"]),
                ("date_order", ">=", prev_df),
                ("date_order", "<=", prev_dt),
            ])
            prev_so_total = sum(prev_so.mapped("amount_total"))

            # Previous period pos orders
            prev_po = self.env["pos.order"].search([
                ("state", "in", ["draft", "paid", "done"]),
                ("date_order", ">=", prev_df),
                ("date_order", "<=", prev_dt),
            ])
            prev_po_total = sum(prev_po.mapped("amount_total"))

            prev_sales = prev_so_total + prev_po_total
            prev_count = len(prev_so) + len(prev_po)

            # Current period
            curr_so = self.env["sale.order"].search([
                ("state", "in", ["sale", "done"]),
                ("date_order", ">=", df),
                ("date_order", "<=", dt),
            ])
            curr_po = self.env["pos.order"].search([
                ("state", "in", ["draft", "paid", "done"]),
                ("date_order", ">=", df),
                ("date_order", "<=", dt),
            ])
            curr_sales = sum(curr_so.mapped("amount_total")) + sum(curr_po.mapped("amount_total"))

            growth = ((curr_sales - prev_sales) / prev_sales * 100) if prev_sales else 0

            return {
                "total_sales": prev_sales,
                "total_orders": prev_count,
                "sales_growth": round(growth, 2),
            }
        except Exception:
            return {"total_sales": 0, "total_orders": 0, "sales_growth": 0}

    # ==================== BRANCH SALES ====================

    @api.model
    def get_branch_sales(self, date_from=None, date_to=None):
        """Return sales data grouped by branch from BOTH sources"""
        branches = self.env["res.branch"].search([])
        result = []

        for branch in branches:
            # Sale orders for this branch
            so_domain = [("state", "in", ["sale", "done"]), ("branch_id", "=", branch.id)]
            if date_from and date_to:
                so_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
            so_orders = self.env["sale.order"].search(so_domain)

            # POS orders for this branch
            po_domain = [("state", "in", ["draft", "paid", "done"]), ("branch_id", "=", branch.id)]
            if date_from and date_to:
                po_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
            po_orders = self.env["pos.order"].search(po_domain)

            total_sales = sum(so_orders.mapped("amount_total")) + sum(po_orders.mapped("amount_total"))
            order_count = len(so_orders) + len(po_orders)
            avg_order = total_sales / order_count if order_count else 0

            # Discounts
            discount_amount = 0
            for order in so_orders:
                for line in order.order_line:
                    if line.discount > 0:
                        original = line.price_unit * line.product_uom_qty
                        discount_amount += (original - line.price_subtotal)
            for order in po_orders:
                for line in order.lines:
                    if line.discount > 0:
                        original = line.price_unit * line.qty
                        discount_amount += (original - line.price_subtotal_incl)

            # Returns (POS only)
            refund_orders = po_orders.filtered(lambda o: o.amount_total < 0 or o.refunded_order_id)
            returns = abs(sum(refund_orders.mapped("amount_total")))

            # Profit
            so_margin = 0
            for order in so_orders:
                for line in order.order_line:
                    cost = line.product_id.standard_price if line.product_id else 0
                    so_margin += line.price_subtotal - (cost * line.product_uom_qty)

            po_margin = 0
            for order in po_orders:
                for line in order.lines:
                    if hasattr(line, 'margin'):
                        po_margin += line.margin

            profit = so_margin + po_margin
            margin_pct = (profit / total_sales * 100) if total_sales else 0

            result.append({
                "id": branch.id,
                "name": branch.name,
                "code": branch.code,
                "total_sales": total_sales,
                "order_count": order_count,
                "avg_order": avg_order,
                "net_sales": total_sales,
                "discount": discount_amount,
                "returns": returns,
                "profit": profit,
                "margin_percent": margin_pct,
                "top_products": [],
                "worst_products": [],
            })

        result.sort(key=lambda x: x["total_sales"], reverse=True)
        return result

    # ==================== EMPLOYEE SALES ====================

    @api.model
    def get_employee_sales(self, date_from=None, date_to=None):
        """Return sales data grouped by employee from BOTH sources"""
        employees = self.env["res.users"].search([("share", "=", False)])
        result = []

        for emp in employees:
            # Sale orders
            so_domain = [("state", "in", ["sale", "done"]), ("user_id", "=", emp.id)]
            if date_from and date_to:
                so_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
            so_orders = self.env["sale.order"].search(so_domain)

            # POS orders
            po_domain = [("state", "in", ["draft", "paid", "done"]), ("user_id", "=", emp.id)]
            if date_from and date_to:
                po_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
            po_orders = self.env["pos.order"].search(po_domain)

            total_sales = sum(so_orders.mapped("amount_total")) + sum(po_orders.mapped("amount_total"))
            order_count = len(so_orders) + len(po_orders)

            if not order_count:
                continue

            avg_order = total_sales / order_count

            # Discounts
            discount_count = 0
            discount_value = 0
            for order in so_orders:
                for line in order.order_line:
                    if line.discount > 0:
                        discount_count += 1
                        original = line.price_unit * line.product_uom_qty
                        discount_value += (original - line.price_subtotal)
            for order in po_orders:
                for line in order.lines:
                    if line.discount > 0:
                        discount_count += 1
                        original = line.price_unit * line.qty
                        discount_value += (original - line.price_subtotal_incl)

            # Cancelled
            cancel_so = self.env["sale.order"].search_count([
                ("state", "=", "cancel"),
                ("user_id", "=", emp.id),
            ])
            cancel_po = self.env["pos.order"].search_count([
                ("state", "=", "cancel"),
                ("user_id", "=", emp.id),
            ])

            # Returns
            refund_po = po_orders.filtered(lambda o: o.amount_total < 0 or o.refunded_order_id)
            returns = abs(sum(refund_po.mapped("amount_total")))

            result.append({
                "id": emp.id,
                "name": emp.name,
                "total_sales": total_sales,
                "order_count": order_count,
                "avg_order": avg_order,
                "discount_count": discount_count,
                "discount_value": discount_value,
                "cancelled": cancel_so + cancel_po,
                "returns": returns,
            })

        result.sort(key=lambda x: x["total_sales"], reverse=True)
        return result

    # ==================== POS ANALYTICS ====================

    @api.model
    def get_pos_analytics(self, date_from=None, date_to=None):
        """Return POS session analytics"""
        domain = [("state", "in", ["draft", "paid", "done"])]
        if date_from and date_to:
            domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]

        configs = self.env["pos.config"].search([])
        result = []

        for config in configs:
            config_domain = domain + [("config_id", "=", config.id)]
            config_orders = self.env["pos.order"].search(config_domain)

            if not config_orders:
                continue

            total_sales = sum(config_orders.mapped("amount_total"))
            order_count = len(config_orders)
            avg_order = total_sales / order_count if order_count else 0

            session_domain = [("config_id", "=", config.id)]
            if date_from:
                session_domain += [("start_at", ">=", date_from)]
            if date_to:
                session_domain += [("start_at", "<=", date_to)]

            sessions = self.env["pos.session"].search(session_domain)
            expected_cash = sum(sessions.mapped("cash_register_balance_start"))
            actual_cash = sum(sessions.mapped("cash_register_balance_end_real"))
            differences = sum(sessions.mapped("cash_register_difference"))

            result.append({
                "id": config.id,
                "name": config.name,
                "branch_name": config.branch_id.name or "",
                "total_sales": total_sales,
                "order_count": order_count,
                "avg_order": avg_order,
                "expected_cash": expected_cash,
                "actual_cash": actual_cash,
                "differences": differences,
            })

        return result

    # ==================== CUSTOMER ANALYTICS ====================

    @api.model
    def get_customer_analytics(self, date_from=None, date_to=None):
        """Return customer sales analytics from BOTH sources"""

        # Sale orders customers
        so_domain = [("state", "in", ["sale", "done"]), ("partner_id", "!=", False)]
        if date_from and date_to:
            so_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
        so_orders = self.env["sale.order"].search(so_domain)

        # POS orders customers
        po_domain = [("state", "in", ["draft", "paid", "done"]), ("partner_id", "!=", False)]
        if date_from and date_to:
            po_domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
        po_orders = self.env["pos.order"].search(po_domain)

        # Combine customers
        all_customers = so_orders.mapped("partner_id") | po_orders.mapped("partner_id")

        result = []
        for customer in all_customers:
            cust_so = so_orders.filtered(lambda o: o.partner_id == customer)
            cust_po = po_orders.filtered(lambda o: o.partner_id == customer)

            total = sum(cust_so.mapped("amount_total")) + sum(cust_po.mapped("amount_total"))
            count = len(cust_so) + len(cust_po)
            avg = total / count if count else 0

            # Last order date
            dates = []
            if cust_so:
                dates.append(max(cust_so.mapped("date_order")))
            if cust_po:
                dates.append(max(cust_po.mapped("date_order")))
            last_order = max(dates) if dates else False

            result.append({
                "id": customer.id,
                "name": customer.name,
                "total_sales": total,
                "order_count": count,
                "avg_order": avg,
                "last_order": fields.Date.to_string(last_order.date()) if last_order else "",
                "city": customer.city or "",
            })

        result.sort(key=lambda x: x["total_sales"], reverse=True)
        return result[:50]

    # ==================== PAYMENT METHODS ====================

    @api.model
    def get_payment_methods(self, date_from=None, date_to=None):
        """Return sales grouped by payment method (POS only)"""
        domain = [("state", "in", ["draft", "paid", "done"])]
        if date_from and date_to:
            domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]

        orders = self.env["pos.order"].search(domain)
        payments = {}

        for order in orders:
            for payment in order.payment_ids:
                method = payment.payment_method_id.name
                payments[method] = payments.get(method, 0) + payment.amount

        return [{"method": k, "amount": v} for k, v in sorted(payments.items(), key=lambda x: x[1], reverse=True)]

    # ==================== HOURLY SALES ====================

    @api.model
    def get_hourly_sales(self, date_from=None, date_to=None):
        """Return sales grouped by hour (POS only)"""
        domain = [("state", "in", ["draft", "paid", "done"])]
        if date_from and date_to:
            domain += [("date_order", ">=", date_from), ("date_order", "<=", date_to)]

        orders = self.env["pos.order"].search(domain)
        hours = {f"{h:02d}:00": 0 for h in range(24)}

        for order in orders:
            hour = order.date_order.hour
            hours[f"{hour:02d}:00"] += order.amount_total

        return [{"hour": k, "amount": v} for k, v in hours.items()]

    # ==================== DASHBOARD DATA COMBINED ====================

    @api.model
    def get_dashboard_data(self, date_range="today", section="all"):
        """Main method called by OWL component to get all dashboard data"""
        today = fields.Date.today()

        if date_range == "today":
            date_from = datetime.combine(today, datetime.min.time())
            date_to = datetime.combine(today, datetime.max.time())
        elif date_range == "week":
            start = today - timedelta(days=today.weekday())
            date_from = datetime.combine(start, datetime.min.time())
            date_to = datetime.combine(today, datetime.max.time())
        elif date_range == "month":
            start = today.replace(day=1)
            date_from = datetime.combine(start, datetime.min.time())
            date_to = datetime.combine(today, datetime.max.time())
        elif date_range == "year":
            start = today.replace(month=1, day=1)
            date_from = datetime.combine(start, datetime.min.time())
            date_to = datetime.combine(today, datetime.max.time())
        elif date_range == "all":
            date_from = None
            date_to = None
        else:
            date_from = datetime.combine(today, datetime.min.time())
            date_to = datetime.combine(today, datetime.max.time())

        data = {
            "date_range": date_range,
            "date_from": fields.Date.to_string(date_from) if date_from else "",
            "date_to": fields.Date.to_string(date_to) if date_to else "",
        }

        if section in ("all", "main"):
            data["kpis"] = self.get_main_kpis(date_from, date_to)
            data["payments"] = self.get_payment_methods(date_from, date_to)
            data["hourly"] = self.get_hourly_sales(date_from, date_to)

        if section in ("all", "branches"):
            data["branches"] = self.get_branch_sales(date_from, date_to)

        if section in ("all", "employees"):
            data["employees"] = self.get_employee_sales(date_from, date_to)

        if section in ("all", "pos"):
            data["pos"] = self.get_pos_analytics(date_from, date_to)

        if section in ("all", "customers"):
            data["customers"] = self.get_customer_analytics(date_from, date_to)

        return data
