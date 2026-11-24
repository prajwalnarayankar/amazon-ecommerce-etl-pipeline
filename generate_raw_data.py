"""
Raw Data Generator for Amazon E-Commerce Pipeline
Generates synthetic raw data with realistic real-world characteristics:
- Missing fields (nulls)
- Duplicate transactions
- Varying order statuses (Completed, Cancelled, Returned)
- Timestamps spanning several months
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

def generate_mock_data(num_orders=5000, output_dir="data/raw"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    random.seed(42)

    categories = {
        "Electronics": ["Echo Dot", "Fire TV Stick", "Kindle Paperwhite", "Noise Canceling Headphones", "USB-C Hub"],
        "Home & Kitchen": ["Air Fryer", "Espresso Machine", "Robot Vacuum", "Blender", "Cookware Set"],
        "Books": ["Atomic Habits", "Designing Data-Intensive Apps", "Python Crash Course", "Clean Code"],
        "Fashion": ["Running Shoes", "Cotton T-Shirt", "Leather Wallet", "Backpack", "Winter Jacket"]
    }
    
    cities = [
        ("Bengaluru", "Karnataka", "South"),
        ("Hyderabad", "Telangana", "South"),
        ("Chennai", "Tamil Nadu", "South"),
        ("Noida", "Uttar Pradesh", "North"),
        ("Mumbai", "Maharashtra", "West"),
        ("Delhi", "Delhi", "North")
    ]

    # 1. Generate Customers
    customers = []
    for i in range(1, 501):
        city, state, region = random.choice(cities)
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "customer_name": f"Customer_{i}",
            "email": f"user{i}@example.com" if random.random() > 0.05 else None,  # intentional null
            "city": city,
            "state": state,
            "region": region,
            "signup_date": (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 300))).strftime("%Y-%m-%d")
        })

    # 2. Generate Products
    products = []
    prod_id = 1
    for cat, items in categories.items():
        for item in items:
            products.append({
                "product_id": f"PROD_{prod_id:03d}",
                "product_name": item,
                "category": cat,
                "unit_price": round(random.uniform(299, 14999), 2),
                "supplier": f"Supplier_{random.randint(1, 10)}"
            })
            prod_id += 1

    # 3. Generate Orders & Order Items
    orders = []
    start_date = datetime(2025, 6, 1)

    for i in range(1, num_orders + 1):
        order_date = start_date + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))
        cust = random.choice(customers)
        prod = random.choice(products)
        qty = random.randint(1, 5)
        status = random.choices(["COMPLETED", "CANCELLED", "RETURNED"], weights=[0.85, 0.10, 0.05])[0]
        payment_method = random.choice(["Amazon Pay", "UPI", "Credit Card", "Net Banking", "Cash on Delivery"])
        
        order = {
            "order_id": f"ORD_{i:06d}",
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "quantity": qty,
            "unit_price": prod["unit_price"],
            "total_amount": round(qty * prod["unit_price"], 2),
            "order_status": status,
            "payment_method": payment_method,
            "order_timestamp": order_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.append(order)

    # Inject intentional duplicates and anomalies (to test pipeline cleaning)
    for _ in range(25):
        orders.append(random.choice(orders)) # duplicate orders
    
    # Write to raw files (simulating S3 Bronze Landing Zone)
    with open(f"{output_dir}/customers.json", "w") as f:
        json.dump(customers, f, indent=2)
    with open(f"{output_dir}/products.json", "w") as f:
        json.dump(products, f, indent=2)
    with open(f"{output_dir}/orders.json", "w") as f:
        json.dump(orders, f, indent=2)

    print(f"Generated {len(customers)} customers, {len(products)} products, and {len(orders)} orders in {output_dir}/")

if __name__ == "__main__":
    generate_mock_data()
