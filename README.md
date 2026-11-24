# Amazon E-Commerce Sales & Analytics Data Pipeline (ETL)

An end-to-end Data Engineering pipeline simulating Amazon-scale order processing, data lake landing, dimensional modeling (Star Schema), and advanced SQL analytics.

## Architecture Overview

```
[Raw Sources: Orders, Customers, Products] 
      │ (JSON Extraction)
      ▼
[Bronze Layer / Data Lake Landing Zone] (data/raw/)
      │ 
      ▼ (Python Transformation: Deduplication, Null Imputation, Schema Validation)
[Silver Layer / Cleaned & Normalized Data]
      │
      ▼ (Dimensional Modeling: Star Schema)
[Gold Layer / Analytical Warehouse] (data/warehouse/amazon_data_warehouse.db)
      │
      ├── dim_customers (SCD Type 1)
      ├── dim_products
      ├── dim_date
      └── fact_orders (Grain: 1 row per order item)
      │
      ▼
[Advanced Analytical Queries] (Window Functions, CTEs, MoM Growth, Cohorts)
```

## Tech Stack
* **Language:** Python 3 (Native ETL scripts)
* **Storage / Data Lake:** Parquet / JSON landing zone (AWS S3 compatible)
* **Warehouse & Modeling:** Relational Star Schema (SQLite / PostgreSQL / AWS Redshift compatible)
* **Data Transformation:** Data quality checks, deduplication, schema enforcement
* **Analytics:** Advanced SQL (CTEs, `DENSE_RANK()`, `LAG()`, running totals, cohort retention)

## How to Run

1. **Generate Raw Landing Zone Data:**
   ```bash
   python generate_raw_data.py
   ```

2. **Execute ETL Pipeline:**
   ```bash
   python etl_pipeline.py
   ```

3. **Run Advanced Analytical Reports:**
   ```bash
   python run_analytics.py
   ```
