"""
Executes Advanced Analytical SQL Queries on Amazon Star Schema Warehouse
Prints formatted results to console (simulating Amazon Redshift BI Reports)
"""

import sqlite3

DB_PATH = "data/warehouse/amazon_data_warehouse.db"

def run_query(cursor, title, query):
    print("\n" + "="*85)
    print(f"REPORT: {title}")
    print("="*85)
    cursor.execute(query)
    headers = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Try tabulate if available, otherwise formatted plain table
    try:
        from tabulate import tabulate
        print(tabulate(rows, headers=headers, tablefmt="github"))
    except ImportError:
        # Fallback table formatting without external dependencies
        col_widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) + 3 for i, h in enumerate(headers)]
        header_str = "".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
        separator = "-" * len(header_str)
        print(header_str)
        print(separator)
        for row in rows:
            print("".join(f"{str(v):<{col_widths[i]}}" for i, v in enumerate(row)))

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query 1: Top 3 Products per Category (Dense Rank)
    q1 = """
    WITH CategoryProductSales AS (
        SELECT 
            p.category,
            p.product_name,
            SUM(f.quantity) AS total_units_sold,
            ROUND(SUM(f.total_amount), 2) AS total_revenue,
            DENSE_RANK() OVER (
                PARTITION BY p.category 
                ORDER BY SUM(f.total_amount) DESC
            ) AS rank_in_cat
        FROM fact_orders f
        JOIN dim_products p ON f.product_id = p.product_id
        WHERE f.order_status = 'COMPLETED'
        GROUP BY p.category, p.product_name
    )
    SELECT category, rank_in_cat, product_name, total_units_sold, total_revenue
    FROM CategoryProductSales
    WHERE rank_in_cat <= 3
    ORDER BY category, rank_in_cat;
    """
    run_query(cursor, "Top 3 Revenue Generating Products per Category (Window DENSE_RANK)", q1)

    # Query 2: MoM Revenue Growth
    q2 = """
    WITH MonthlyRevenue AS (
        SELECT 
            d.year,
            d.month_number,
            d.month_name,
            ROUND(SUM(f.total_amount), 2) AS monthly_sales
        FROM fact_orders f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.order_status = 'COMPLETED'
        GROUP BY d.year, d.month_number, d.month_name
    ),
    RevenueWithLag AS (
        SELECT 
            year,
            month_number,
            month_name,
            monthly_sales,
            LAG(monthly_sales, 1) OVER (ORDER BY year, month_number) AS prev_month_sales
        FROM MonthlyRevenue
    )
    SELECT 
        year,
        month_name,
        monthly_sales,
        COALESCE(prev_month_sales, 0) AS prev_month_sales,
        CASE 
            WHEN prev_month_sales IS NULL THEN 0.0
            ELSE ROUND(((monthly_sales - prev_month_sales) * 100.0 / prev_month_sales), 2)
        END AS mom_growth_pct
    FROM RevenueWithLag
    ORDER BY year, month_number;
    """
    run_query(cursor, "Month-over-Month (MoM) Growth Analysis (Window LAG)", q2)

    # Query 3: Customer Cohorts & Retention
    q3 = """
    WITH CustomerOrderCounts AS (
        SELECT 
            customer_id,
            COUNT(order_id) AS total_orders,
            ROUND(SUM(total_amount), 2) AS lifetime_spend
        FROM fact_orders
        WHERE order_status = 'COMPLETED'
        GROUP BY customer_id
    )
    SELECT 
        CASE 
            WHEN total_orders = 1 THEN '1 Time Buyer'
            WHEN total_orders BETWEEN 2 AND 4 THEN '2-4 Orders (Repeat)'
            ELSE '5+ Orders (Loyal Amazonian)'
        END AS customer_segment,
        COUNT(customer_id) AS customer_count,
        ROUND(AVG(lifetime_spend), 2) AS avg_segment_spend
    FROM CustomerOrderCounts
    GROUP BY customer_segment
    ORDER BY customer_count DESC;
    """
    run_query(cursor, "Customer Retention & Lifetime Spend Segmentation", q3)

    conn.close()

if __name__ == "__main__":
    main()
