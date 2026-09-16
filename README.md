# Retail Data Analytics Database System

This is a console-based retail management system. It works like a small online store.

Users can register or log in. After that, customers can search for products, view product details, add items to a cart, change quantities, and check out to create an order with a shipping address. Customers can also see their past orders and the details of each order.

There is also a "sales" role. This role can update product price and stock, create a weekly sales report, and show the top products by orders and by views. When the sales user asks for the top products report, the system creates an Excel file automatically.

The system also saves user sessions, search history, and viewed products. This data can be used for reports later. When a customer checks out, the system uses a database transaction. This means if there is not enough stock, nothing is saved, and the order is safely cancelled.

## Setup

### 1) Create & activate a virtual environment (Windows PowerShell)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 3) Run the app

From the project root:
```bash
python -m src.app data/store.db
```

## Excel Reporting

The system can create an Excel file with all the tables in the database.

<img width="1005" height="68" alt="image" src="https://github.com/user-attachments/assets/b427c0d5-4324-42f5-ae66-0bc5ad43a875" />

## Power BI Integration

This project also has a tool that turns the database into files ready for Power BI. This lets you build charts and dashboards from the data.

The tool only **reads** the database. It never changes any data.

### What data is exported

**Dimension tables (basic information):**
- `dim_products` — list of products
- `dim_customers` — list of customers
- `dim_date` — a calendar table, used for charts over time

**Fact tables (events and numbers):**
- `fact_orders` — one row per order, with the total order amount
- `fact_orderlines` — one row per item in an order
- `fact_views` — records of which products were viewed
- `fact_search` — records of what customers searched for
- `fact_sessions` — user login sessions, with how long each session lasted

### How to export the data

```bash
python -m src.bi.export_powerbi data/store.db
```

This reads `data/store.db` and saves CSV files into `data/powerbi_export/`.

### How to load the data into Power BI

1. Open Power BI Desktop
2. Click **Get Data** → **Folder** → choose the `data/powerbi_export` folder. This loads all the tables at once. (Or use **Text/CSV** to load them one at a time.)
3. In the **Model** view, connect the tables like this:
   - `dim_products.pid` → `fact_orderlines.pid` and `fact_views.pid`
   - `dim_customers.cid` → `fact_orders.cid`, `fact_sessions.cid`, `fact_search.cid`, `fact_views.cid`
   - `dim_date.date` → `fact_orders.odate`

With this setup, you can build charts like: sales over time, top products by revenue vs. by views, how many searches turn into purchases, and low-stock alerts.