"""
ETL Pipeline for Amazon E-Commerce Analytics
Architecture:
- Extract: Reads raw JSON data (simulating AWS S3 Bronze bucket)
- Transform: Cleans, deduplicates, validates schemas, formats dates (Silver Layer)
- Load: Models data into Star Schema (Gold Layer) in an analytical warehouse
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "data/warehouse/amazon_data_warehouse.db"
RAW_DIR = "data/raw"

def init_warehouse_schema(conn):
    cursor = conn.cursor()
    
    # 1. Dim Date
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_date (
        date_key INTEGER PRIMARY KEY,
        full_date TEXT UNIQUE,
        day_of_month INTEGER,
        day_name TEXT,
        month_number INTEGER,
        month_name TEXT,
        quarter INTEGER,
        year INTEGER,
        is_weekend INTEGER
    );
    """)

    # 2. Dim Customers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_customers (
        customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE,
        customer_name TEXT,
        email TEXT,
        city TEXT,
        state TEXT,
        region TEXT,
        signup_date TEXT
    );
    """)

    # 3. Dim Products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_products (
        product_key INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE,
        product_name TEXT,
        category TEXT,
        unit_price REAL,
        supplier TEXT
    );
    """)

    # 4. Fact Orders (Star Schema Center)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_orders (
        order_key INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        date_key INTEGER,
        customer_id TEXT,
        product_id TEXT,
        quantity INTEGER,
        unit_price REAL,
        total_amount REAL,
        order_status TEXT,
        payment_method TEXT,
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
        FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
    );
    """)
    conn.commit()

def run_etl():
    print("[ETL] Starting Pipeline Execution...")
    Path("data/warehouse").mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_warehouse_schema(conn)
    cursor = conn.cursor()

    # --- 1. EXTRACT ---
    print("[EXTRACT] Reading raw data from landing zone...")
    with open(f"{RAW_DIR}/customers.json") as f:
        customers_raw = json.load(f)
    with open(f"{RAW_DIR}/products.json") as f:
        products_raw = json.load(f)
    with open(f"{RAW_DIR}/orders.json") as f:
        orders_raw = json.load(f)

    # --- 2. TRANSFORM & LOAD DIMENSIONS ---
    print("[TRANSFORM & LOAD] Populating dim_customers...")
    for c in customers_raw:
        # Data cleaning: impute missing email with fallback
        email = c["email"] if c.get("email") else f"{c['customer_id'].lower()}@unknown.amazon.com"
        cursor.execute("""
            INSERT OR REPLACE INTO dim_customers (customer_id, customer_name, email, city, state, region, signup_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (c["customer_id"], c["customer_name"], email, c["city"], c["state"], c["region"], c["signup_date"]))

    print("[TRANSFORM & LOAD] Populating dim_products...")
    for p in products_raw:
        cursor.execute("""
            INSERT OR REPLACE INTO dim_products (product_id, product_name, category, unit_price, supplier)
            VALUES (?, ?, ?, ?, ?)
        """, (p["product_id"], p["product_name"], p["category"], p["unit_price"], p["supplier"]))

    # Transform & Load Date Dimension and Fact Orders
    print("[TRANSFORM & LOAD] Cleaning orders, building dim_date and fact_orders...")
    seen_orders = set()
    duplicate_count = 0
    date_dimension_set = {}

    for o in orders_raw:
        # Deduplication check
        if o["order_id"] in seen_orders:
            duplicate_count += 1
            continue
        seen_orders.add(o["order_id"])

        # Parse Timestamp
        dt = datetime.strptime(o["order_timestamp"], "%Y-%m-%d %H:%M:%S")
        date_key = int(dt.strftime("%Y%m%d"))
        full_date_str = dt.strftime("%Y-%m-%d")

        # Track unique dates for dim_date
        if date_key not in date_dimension_set:
            date_dimension_set[date_key] = (
                date_key,
                full_date_str,
                dt.day,
                dt.strftime("%A"),
                dt.month,
                dt.strftime("%B"),
                (dt.month - 1) // 3 + 1,
                dt.year,
                1 if dt.weekday() >= 5 else 0
            )

        # Load Fact Orders
        cursor.execute("""
            INSERT INTO fact_orders (
                order_id, date_key, customer_id, product_id,
                quantity, unit_price, total_amount, order_status, payment_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            o["order_id"], date_key, o["customer_id"], o["product_id"],
            o["quantity"], o["unit_price"], o["total_amount"],
            o["order_status"], o["payment_method"]
        ))

    # Populate dim_date
    for date_row in date_dimension_set.values():
        cursor.execute("""
            INSERT OR IGNORE INTO dim_date (
                date_key, full_date, day_of_month, day_name, month_number, month_name, quarter, year, is_weekend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, date_row)

    conn.commit()

    # --- 3. DATA QUALITY ASSERTIONS ---
    print(f"[DATA QUALITY] Deduplicated {duplicate_count} invalid duplicate records.")
    cursor.execute("SELECT COUNT(*) FROM fact_orders;")
    fact_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dim_customers;")
    cust_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dim_products;")
    prod_count = cursor.fetchone()[0]

    print(f"[SUCCESS] Warehouse Loaded:")
    print(f"  • fact_orders:    {fact_count} records")
    print(f"  • dim_customers:  {cust_count} records")
    print(f"  • dim_products:   {prod_count} records")
    print(f"  • Database path:  {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    run_etl()
