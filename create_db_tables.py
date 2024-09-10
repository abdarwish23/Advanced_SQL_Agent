import sqlite3
import csv
import os
from faker import Faker
import random

# Set up Faker for generating random names, addresses, etc.
fake = Faker()

# Path to the SQLite database file
db_file = "ecommerce.db"

# Create or connect to SQLite database
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# Create directory to store CSV files
csv_dir = "csv_files"
os.makedirs(csv_dir, exist_ok=True)

# SQL Queries to create tables
create_tables = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    city TEXT,
    country TEXT,
    registration_date TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT,
    category TEXT,
    stock_quantity INTEGER,
    price REAL,
    supplier_id INTEGER
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT,
    contact_name TEXT,
    contact_phone TEXT,
    address TEXT,
    country TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    order_status TEXT,
    order_date TEXT,
    total_amount REAL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price_per_item REAL
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    payment_method TEXT,
    payment_date TEXT,
    payment_status TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    product_id INTEGER,
    rating INTEGER,
    review_text TEXT,
    review_date TEXT
);

CREATE TABLE IF NOT EXISTS shopping_carts (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS cart_items (
    cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
);
"""
cur.executescript(create_tables)

# Function to generate fake data
def populate_data():
    # Insert Suppliers
    for _ in range(10):
        cur.execute(
            "INSERT INTO suppliers (supplier_name, contact_name, contact_phone, address, country) VALUES (?, ?, ?, ?, ?)",
            (fake.company(), fake.name(), fake.phone_number(), fake.address(), fake.country())
        )

    # Insert Customers
    for _ in range(100):
        cur.execute(
            "INSERT INTO customers (first_name, last_name, email, phone, address, city, country, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fake.first_name(), fake.last_name(), fake.email(), fake.phone_number(), fake.address(), fake.city(), fake.country(), fake.date())
        )

    # Insert Products
    for i in range(100):
        cur.execute(
            "INSERT INTO products (product_name, category, stock_quantity, price, supplier_id) VALUES (?, ?, ?, ?, ?)",
            (f"Product {i+1}", f"Category {random.randint(1, 10)}", random.randint(10, 100), round(random.uniform(5, 100), 2), random.randint(1, 10))
        )

    # Insert Orders
    for _ in range(100):
        cur.execute(
            "INSERT INTO orders (customer_id, order_status, order_date, total_amount) VALUES (?, ?, ?, ?)",
            (random.randint(1, 100), random.choice(['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']), fake.date_time_this_year(), round(random.uniform(20, 500), 2))
        )

    # Insert Order Items
    for _ in range(200):  # Assuming each order has 2 items on average
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price_per_item) VALUES (?, ?, ?, ?)",
            (random.randint(1, 100), random.randint(1, 100), random.randint(1, 5), round(random.uniform(5, 100), 2))
        )

    # Insert Payments
    for i in range(100):
        cur.execute(
            "INSERT INTO payments (order_id, payment_method, payment_date, payment_status) VALUES (?, ?, ?, ?)",
            (i+1, random.choice(['Credit Card', 'PayPal', 'Bank Transfer']), fake.date_time_this_year(), random.choice(['Completed', 'Pending', 'Failed']))
        )

    # Insert Reviews
    for _ in range(100):
        cur.execute(
            "INSERT INTO reviews (customer_id, product_id, rating, review_text, review_date) VALUES (?, ?, ?, ?, ?)",
            (random.randint(1, 100), random.randint(1, 100), random.randint(1, 5), fake.sentence(), fake.date_time_this_year())
        )

    # Insert Shopping Carts
    for _ in range(50):
        cur.execute(
            "INSERT INTO shopping_carts (customer_id, created_at, updated_at) VALUES (?, ?, ?)",
            (random.randint(1, 100), fake.date_time_this_year(), fake.date_time_this_year())
        )

    # Insert Cart Items
    for _ in range(150):
        cur.execute(
            "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
            (random.randint(1, 50), random.randint(1, 100), random.randint(1, 5))
        )

# Call the function to populate data
populate_data()

# Commit changes
conn.commit()

# Function to export each table to CSV
def export_to_csv(table_name):
    csv_file = os.path.join(csv_dir, f"{table_name}.csv")
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header (column names)
        writer.writerow([desc[0] for desc in cur.description])
        # Write rows
        writer.writerows(rows)

# List of tables to export
tables = ['customers', 'products', 'suppliers', 'orders', 'order_items', 'payments', 'reviews', 'shopping_carts', 'cart_items']

# Export each table to CSV
for table in tables:
    export_to_csv(table)

# Close connection
conn.close()

print(f"Database and CSV files created in: {os.getcwd()}")
