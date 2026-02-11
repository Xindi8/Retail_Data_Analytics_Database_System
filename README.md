# Retail Data Analytics Database System

It is a console-based retail management system that simulates a small online store.

In this system, users can register or log in, then customers can search products by keywords, view product details, add items to a cart, update quantities, and checkout to create an order with a shipping address. Customers can also view past orders and see order details.


There is also a sales role that can update product price and stock, generate a weekly sales report, and show top products by orders and by views.

The system records user sessions, search history, and viewed products, so it can support reports later. For checkout, I also used a transaction to make sure stock updates and order creation stay consistent — if stock is not enough, it rolls back safely.
## Setup

### 1) Create & activate virtual environment (Windows PowerShell)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies
```bash
python -m pip install -r requirements.txt
```
4) Run the app

From the project root:
```bash
python -m src.app data/store.db
```

## The Excel sheet contains all tables in this system
<img width="1005" height="68" alt="image" src="https://github.com/user-attachments/assets/b427c0d5-4324-42f5-ae66-0bc5ad43a875" />

