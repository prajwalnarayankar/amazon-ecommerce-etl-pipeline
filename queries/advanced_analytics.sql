-- =====================================================================
-- AMAZON DATA ENGINEERING ANALYTICAL QUERIES
-- Demonstrating: CTEs, Window Functions, Star Schema Joins, Aggregations
-- =====================================================================

-- 1. TOP 3 HIGHEST SELLING PRODUCTS IN EACH CATEGORY (DENSE_RANK)
WITH CategoryProductSales AS (
    SELECT 
        p.category,
        p.product_name,
        SUM(f.quantity) AS total_units_sold,
        ROUND(SUM(f.total_amount), 2) AS total_revenue,
        DENSE_RANK() OVER (
            PARTITION BY p.category 
            ORDER BY SUM(f.total_amount) DESC
        ) AS rank_in_category
    FROM fact_orders f
    JOIN dim_products p ON f.product_id = p.product_id
    WHERE f.order_status = 'COMPLETED'
    GROUP BY p.category, p.product_name
)
SELECT category, rank_in_category, product_name, total_units_sold, total_revenue
FROM CategoryProductSales
WHERE rank_in_category <= 3
ORDER BY category, rank_in_category;


-- 2. MONTH-OVER-MONTH (MoM) REVENUE GROWTH RATE (LEAD / LAG & WINDOW FUNCTIONS)
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


-- 3. RUNNING TOTAL (CUMULATIVE REVENUE) BY REGION
SELECT 
    c.region,
    d.full_date,
    ROUND(SUM(f.total_amount), 2) AS daily_revenue,
    ROUND(SUM(SUM(f.total_amount)) OVER (
        PARTITION BY c.region 
        ORDER BY d.full_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS cumulative_region_revenue
FROM fact_orders f
JOIN dim_customers c ON f.customer_id = c.customer_id
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.order_status = 'COMPLETED'
GROUP BY c.region, d.full_date
ORDER BY c.region, d.full_date
LIMIT 20;


-- 4. CUSTOMER RETENTION & FREQUENCY DISTRIBUTION
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
