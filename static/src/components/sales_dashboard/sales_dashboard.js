/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { loadJS } from "@web/core/assets";

export class SalesDashboard extends Component {
    static template = "sales_dashboard.SalesDashboard";
    static components = { Layout };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            activeTab: "main",
            dateRange: "today",
            kpis: {
                total_sales: 0,
                total_orders: 0,
                avg_order: 0,
                net_sales: 0,
                discount_amount: 0,
                total_returns: 0,
                return_count: 0,
                total_margin: 0,
                margin_percent: 0,
                prev_total_sales: 0,
                prev_total_orders: 0,
                sales_growth: 0,
            },
            branches: [],
            employees: [],
            posData: [],
            customers: [],
            payments: [],
            hourly: [],
        });

        this.chartRefs = {
            branchChart: useRef("branchChart"),
            paymentChart: useRef("paymentChart"),
            hourlyChart: useRef("hourlyChart"),
            employeeChart: useRef("employeeChart"),
        };
        this.chartInstances = {};

        // Bind methods
        this.onTabChange = this.onTabChange.bind(this);
        this.onDateRangeChange = this.onDateRangeChange.bind(this);

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData("all");
        });

        onMounted(() => {
            this.renderCharts();
        });

        onWillUnmount(() => {
            this.destroyCharts();
        });
    }

    async loadData(section = "all") {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "sales.dashboard",
                "get_dashboard_data",
                [this.state.dateRange, section],
                {}
            );

            if (data.kpis) this.state.kpis = data.kpis;
            if (data.branches) this.state.branches = data.branches;
            if (data.employees) this.state.employees = data.employees;
            if (data.pos) this.state.posData = data.pos;
            if (data.customers) this.state.customers = data.customers;
            if (data.payments) this.state.payments = data.payments;
            if (data.hourly) this.state.hourly = data.hourly;
        } catch (error) {
            console.error("Dashboard load error:", error);
            this.notification.add("خطأ في تحميل البيانات", { type: "danger" });
        }
        this.state.loading = false;
    }

    async onDateRangeChange(ev) {
        const newRange = ev.target.value;
        this.state.dateRange = newRange;
        await this.loadData("all");
        this.destroyCharts();
        setTimeout(() => this.renderCharts(), 100);
    }

    async onTabChange(ev) {
        const tab = ev.currentTarget.dataset.tab;
        if (!tab) return;
        this.state.activeTab = tab;
        await this.loadData(tab);
        this.destroyCharts();
        setTimeout(() => this.renderCharts(), 100);
    }

    destroyCharts() {
        Object.values(this.chartInstances).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.chartInstances = {};
    }

    renderCharts() {
        if (this.state.activeTab === "main" || this.state.activeTab === "branches") {
            this.renderBranchChart();
        }
        if (this.state.activeTab === "main") {
            this.renderPaymentChart();
            this.renderHourlyChart();
        }
        if (this.state.activeTab === "employees") {
            this.renderEmployeeChart();
        }
    }

    renderBranchChart() {
        const canvas = this.chartRefs.branchChart?.el;
        if (!canvas || !this.state.branches.length) return;

        const ctx = canvas.getContext("2d");
        this.chartInstances.branch = new Chart(ctx, {
            type: "bar",
            data: {
                labels: this.state.branches.map(b => b.name),
                datasets: [{
                    label: "المبيعات",
                    data: this.state.branches.map(b => b.total_sales),
                    backgroundColor: [
                        "#714B67", "#017E84", "#F9A825", "#E53935",
                        "#43A047", "#1E88E5", "#8E24AA"
                    ],
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => this.formatCurrency(ctx.raw)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (v) => this.formatCompactNumber(v)
                        }
                    }
                }
            }
        });
    }

    renderPaymentChart() {
        const canvas = this.chartRefs.paymentChart?.el;
        if (!canvas || !this.state.payments.length) return;

        const ctx = canvas.getContext("2d");
        this.chartInstances.payment = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: this.state.payments.map(p => p.method),
                datasets: [{
                    data: this.state.payments.map(p => p.amount),
                    backgroundColor: [
                        "#714B67", "#017E84", "#F9A825", "#E53935",
                        "#43A047", "#1E88E5", "#8E24AA", "#FF7043"
                    ],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "right",
                        labels: { boxWidth: 12, padding: 15 }
                    }
                }
            }
        });
    }

    renderHourlyChart() {
        const canvas = this.chartRefs.hourlyChart?.el;
        if (!canvas || !this.state.hourly.length) return;

        const ctx = canvas.getContext("2d");
        this.chartInstances.hourly = new Chart(ctx, {
            type: "line",
            data: {
                labels: this.state.hourly.map(h => h.hour),
                datasets: [{
                    label: "المبيعات بالساعة",
                    data: this.state.hourly.map(h => h.amount),
                    borderColor: "#714B67",
                    backgroundColor: "rgba(113, 75, 103, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: "#714B67",
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: (v) => this.formatCompactNumber(v) }
                    }
                }
            }
        });
    }

    renderEmployeeChart() {
        const canvas = this.chartRefs.employeeChart?.el;
        if (!canvas || !this.state.employees.length) return;

        const ctx = canvas.getContext("2d");
        const topEmployees = this.state.employees.slice(0, 10);

        this.chartInstances.employee = new Chart(ctx, {
            type: "bar",
            data: {
                labels: topEmployees.map(e => e.name),
                datasets: [{
                    label: "المبيعات",
                    data: topEmployees.map(e => e.total_sales),
                    backgroundColor: "#017E84",
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        ticks: { callback: (v) => this.formatCompactNumber(v) }
                    }
                }
            }
        });
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat("ar-SA", {
            style: "currency",
            currency: "SAR",
            minimumFractionDigits: 2
        }).format(amount || 0);
    }

    formatNumber(num) {
        return new Intl.NumberFormat("ar-SA").format(num || 0);
    }

    formatCompactNumber(num) {
        return new Intl.NumberFormat("ar-SA", {
            notation: "compact",
            compactDisplay: "short"
        }).format(num || 0);
    }

    getGrowthClass(growth) {
        if (growth > 0) return "text-success";
        if (growth < 0) return "text-danger";
        return "text-muted";
    }

    getGrowthIcon(growth) {
        if (growth > 0) return "fa-arrow-up";
        if (growth < 0) return "fa-arrow-down";
        return "fa-minus";
    }
}

registry.category("actions").add("sales_dashboard", SalesDashboard);
