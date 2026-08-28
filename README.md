# 📊 Sales Analytics Dashboard for Odoo 18

![Version](https://img.shields.io/badge/version-18.0.1.0.0-blue)
![Odoo](https://img.shields.io/badge/Odoo-18-714B67?logo=odoo)
![License](https://img.shields.io/badge/License-LGPL--3-green)
![JavaScript](https://img.shields.io/badge/UI-OWL_&_Chart.js-yellow)

> **An integrated sales management and analytics module** that combines data from `sale.order` and `pos.order` into a single, interactive dashboard. It includes full support for branch management, employee performance tracking, and customer analytics.

---

## 🚀 Executive Features

This module provides a comprehensive view of the organization's sales performance, empowering decision-makers with real-time, data-driven insights.

### 1. 📈 Key Performance Indicators (KPIs)
- **Total Sales** and **Net Sales**.
- **Total Orders** and **Average Order Value**.
- **Total Discounts** given and their monetary value.
- **Returns** (count and total amount) from Point of Sale.
- **Total Profit** and **Profit Margin Percentage**.
- **Intelligent period-over-period comparison** (growth/decline percentage) with visual trend icons.

### 2. 🏢 Branch Analytics
- Complete management of branches (`res.branch`) with unique codes.
- Top-performing branch ranking with interactive bar charts.
- Detailed breakdown per branch including: Sales, Orders, Discounts, Returns, Profit, and Margin.
- Automatic linking of branches to `pos.config` and `sale.order`.

### 3. 👔 Employee Performance
- Evaluate employee performance based on total sales and order count.
- Track discount usage (count and total value) per employee.
- Monitor cancelled orders and returns associated with each employee.
- Display a top 5 leaderboard with medals (🥇🥈🥉).

### 4. 🖥️ POS Analytics
- Analyze each Point of Sale device's performance (Sales, Orders, Average Ticket).
- Cash audit: Display **Expected Cash** vs. **Actual Cash** and calculate **Cash Differences** directly from POS sessions.

### 5. 👥 Customer Analytics
- Identify the top 50 customers based on total purchases.
- Display customer details (Name, City, Order Count, Average Order, and Last Purchase Date).
- Helps design loyalty programs and targeted marketing campaigns for high-spending customers.

### 6. ⏱️ Temporal & Payment Analysis
- **Hourly Sales Distribution** (to identify peak hours) from POS data.
- **Payment Method Distribution** (Cash, Card, Transfer, etc.) visualized with an interactive Doughnut chart.
- **Flexible Date Filters**: Today, This Week, This Month, This Year, or All Time.

---

## 🛠️ Detailed Technical Report


#### A. `res.branch` Model (Branch Management)
- **Type**: `models.Model`
- **Purpose**: Stores branch data and links it to the company (`res.company`).
- **Main Fields**:
  - `name` (Char, Required, Translate)
  - `code` (Char, Unique)
  - `active` (Boolean)
  - `company_id` (Many2one, Default = current company)
- **Constraints**: SQL uniqueness constraint on `code`.
- **Relations**:
  - `One2many` to `pos.config` (`branch_id`).
  - This field is inherited in `pos.order` (as `related`) and `sale.order`.

#### B. `sales.dashboard` Model (Transient Analytics Model)
- **Type**: `models.TransientModel` (Does not persist data permanently; ideal for dashboards).
- **Dependencies**: Relies on `sale.order`, `pos.order`, `res.branch`, and `res.users`.
- **Core Methods**:
  - `get_main_kpis()`: Calculates main KPIs by merging both data sources.
  - `get_branch_sales()`: Aggregates sales by branch.
  - `get_employee_sales()`: Aggregates employee performance.
  - `get_pos_analytics()`: Analyzes POS sessions and cash differences.
  - `get_customer_analytics()`: Analyzes top customers.
  - `get_payment_methods()`: Payment method distribution (POS only).
  - `get_hourly_sales()`: Hourly sales distribution (POS only).
  - `get_dashboard_data()`: The main method that aggregates all data based on the selected date range and section.

#### C. Inherited Models (Extensions)
- **`pos.config`**: Adds a `branch_id` field with a `domain` filtering branches by the current company.
- **`pos.order`**: Adds a `branch_id` field as a **`related`** field with **`store=True`** and **`index=True`** for optimized query performance.
- **`sale.order`**: Adds a `branch_id` field with a similar `domain`.

---

### 3. API Endpoint (Controller)

- **Route**: `/sales_dashboard/get_data`
- **Type**: `type="json"`, `auth="user"`
- **Parameters**:
  - `date_range` (string): "today", "week", "month", "year", "all".
  - `section` (string): "all", "main", "branches", "employees", "pos", "customers".
- **Logic**: Calls `sales.dashboard.get_dashboard_data()` and returns the result as JSON to feed the OWL frontend.

---

### 4. User Interface (OWL JavaScript)

#### A. Technologies Used
- **`@odoo/owl`**: Odoo 18's modern UI framework.
- **`useState`**: For reactive state management.
- **`useService("orm")`**: To call remote ORM methods.
- **`loadJS`**: Dynamically loads `Chart.js` from the backend assets.

#### B. State Management
```javascript
this.state = useState({
  loading: true, activeTab: "main", dateRange: "today",
  kpis: {...}, branches: [], employees: [], posData: [],
  customers: [], payments: [], hourly: []
});

### 1. Module Structure
