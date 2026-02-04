# ===============================
#    Mini Project - Customer & Sales System
#    Description:
#       This program implements a console-based retail management system.
#       It supports user login/registration, product search, cart management,
#       checkout, and order tracking for customers, and product updates/reports
#       for sales users.
# ===============================


import sqlite3
import os
import sys
import datetime as dt
import getpass
from dataclasses import dataclass


#   Store basic user information after login or registration.
@dataclass
class User:
    uid: int        #   user id
    name: str       #   customer name or sales name
    role: str       #   customer or sales
    psw:   str      #   user password

#   Store session information for the currently logged-in user.
#   Each login creates one session record in the database.
@dataclass
class SessionInf:
    cid: int
    sessionNo: int

#   This class handles all SQL-related operations for the system.
#   It provides helper methods for login, registration, session tracking,
#   product management, shopping cart, and order processing.
#   Each method directly communicates with the connected SQLite database.
class dbFunctions:
    
    #   Initialize and connect to the SQLite database.
    #    Args:
    #        path (str): Path to the SQLite database file.
    #    Raises:
    #           FileNotFoundError: If the specified database file does not exist.
    def __init__(self, path: str):
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Database file not found: {path}")
        self.path = path

        #   Connect to database and configure row_factory for dictionary-like access
        try:
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row     # Fetch rows as dict-like objects
        except sqlite3.Error as e:
            print("\n[X] SQL Error in connect to databse!\n")
            print(e)


    #   Close the current database connection.
    def close(self):

        try:
            self.conn.close()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in close database!\n")
            print(e)
    
    #   Commit all pending changes to the database.
    def commit(self):
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in update database!\n")
            print(e)

    #   Retrieve the next available user ID.
    #   Returns:
    #           int: Next uid (max(uid)+1) or 1 if table is empty.
    def get_max_uid(self):

        try:
            cur = self.conn.execute("SELECT MAX(uid) FROM users;")
            rs = cur.fetchone()[0]
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_max_uid()\n")
            print(e)
        
        if rs is None:
            uid = 1
        else:
            uid = rs + 1
        return uid

    #   Retrieve the next available session number for a customer.
    #   Args:
    #       cid (int): Customer ID.
    #   Returns:
    #           int: Next session number (max+1) or 1 if first login.
    def get_max_sessionNo(self,cid):

        try:
            cur = self.conn.execute("SELECT MAX(sessionNo) FROM sessions WHERE cid = ?;",(cid,))
            rs = cur.fetchone()[0]
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_max_sessionNo()\n")
            print(e)

        if rs is None:
            sessionNo = 1
        else:
            sessionNo = rs + 1
        return sessionNo
    
   
    #   Retrieve the next available order number.
    #   Returns:
    #           int: Next order number (max+1) or 1 if table is empty.
    def get_max_orderNo(self):

        try:
            cur = self.conn.execute("SELECT MAX(ono) FROM orders;")
            rs = cur.fetchone()[0]
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_max_orderNo()\n")
            print(e)
        
        if rs is None:
            ono = 1
        else:
            ono = rs + 1
        return ono
   
    #   Get basic user information (uid, password, role).
    #   Args:
    #       uid (int): User ID.
    #   Returns:
    #           sqlite3.Row: A row containing user info or None if not found.
    def get_user_inf(self,uid):

        try:
            cur = self.conn.execute("SELECT uid, pwd, role FROM users WHERE uid = ?;", (uid,))
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_user_inf()\n")
            print(e)
        return cur.fetchone()
    
    #   Get customer name by customer ID.
    #   Args:
    #       uid (int): Customer ID.
    #   Returns:
    #           sqlite3.Row: A row containing customer info or None if not found.
    def get_customer_inf(self,uid):

        try:
            cur = self.conn.execute("SELECT name FROM customers WHERE cid = ?;", (uid,))
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_customer_inf()\n")
            print(e)
        return cur.fetchone()
    
    #   Verify user credentials.
    #   Args:
    #       uid (int): User ID to verify.
    #   Returns:
    #           User: A User object with uid, name, role, and password (plain text).
    def login_verify(self,uid):
        
        #   Get related user information according to entered uid
        rs = self.get_user_inf(uid)

        #   If uid does not have related user
        if rs is None:
            return None

        pw = rs["pwd"]              #   Plain-text password from DB
        role = rs["role"].lower()
        name = 'Sales'              #   Default for salesperson

        #   Retrieve customer name if role is 'customer'
        if role == 'customer':
            #   Get customer information
            rs2 = self.get_customer_inf(uid)
            name = rs2["name"]

        return User(uid = uid, name = name, role = role, psw = pw)
    
    #   Check if an email already exists in the customers table.
    #   Args:
    #       email (str): Email address to check.
    #   Returns:
    #           sqlite3.Row or None: Existing customer record if found.
    def check_email(self,email):
        
        try:
            cur = self.conn.execute("SELECT cid FROM customers WHERE LOWER(email) = ?;", (email,))
        except sqlite3.Error as e:
            print("\n[X] SQL Error in check_email()\n")
            print(e)

        return cur.fetchone()
    
    #   Register a new customer by inserting into both 'users' and 'customers'.
    #   Args:
    #       userName (str): Customer name.
    #       email (str): Email address.
    #       password (str): Plain-text password (per TA’s requirement).
    #   Returns:
    #           User: Newly created User object.
    def insert_customer(self,userName,email,password):

        #   Get uid
        uid = self.get_max_uid()
        role = 'customer'       #   Default set role as customer
        try:
            #   Insert user login info
            cur = self.conn.execute("INSERT INTO users (uid,pwd,role) VALUES (?,?,?);", (uid,password,role))
            #  Insert customer info
            cur = self.conn.execute("INSERT INTO customers (cid,name,email) VALUES (?,?,?);", (uid,userName,email,))
            self.commit()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in insert_customer()\n")
            print(e)
            self.conn.rollback()

        return User(uid = uid, name = userName, role = role, psw = password)

    #   Create a new session record for the given customer.
    #   The end_time remains NULL until logout.
    #   Args:
    #       cid (int): Customer ID.
    #   Returns:
    #           SessionInf: Session object with cid and sessionNo.
    def create_session(self,cid):
        
        #   Set up all required values before insert into sessions tables
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session = self.get_max_sessionNo(cid)
        try:
            cur = self.conn.execute("INSERT INTO sessions (cid,sessionNo,start_time,end_time) VALUES (?,?,?,NULL);",(cid,session,ts,))
            self.commit()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in create_session()\n")
            print(e)
            self.conn.rollback()            
        return SessionInf(cid = cid,sessionNo = session)
    
    #   Update the end_time for the specified session (called at logout).
    #   Args:
    #       sessionInformation (SessionInf): Object with cid and sessionNo.
    def update_session(self,sessionInformation):
         
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session = sessionInformation.sessionNo
        cid = sessionInformation.cid
        try:
            cur = self.conn.execute("UPDATE sessions SET end_time = ? where cid = ? AND sessionNo = ? ;",(ts,cid,session,))
            self.commit()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in update_session()\n")
            self.conn.rollback()
            print(e)

    #   Record a customer's search activity in the 'search' table.
    #   Args:
    #       search (str): Search query string.
    #       sessionInformation (SessionInf): Current session details.
    def create_search(self,search,sessionInformation):
        
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur = self.conn.execute("INSERT INTO search (cid,sessionNo,ts,query) VALUES (?,?,?,?);",(sessionInformation.cid,sessionInformation.sessionNo,ts,search))
            self.commit()
        except sqlite3.Error as e:
            print("\n[X]SQL Error in create_search()\n")
            self.conn.rollback()
            print(e)

    #   Perform a case-insensitive keyword search on products.
    #   Records the search in the database.
    #   Args:
    #       conditions (list): List of SQL WHERE conditions.
    #       params (list): List of parameters for prepared statement.
    #       sessionInformation (SessionInf): Current session info.
    #   Returns:
    #          list[sqlite3.Row]: Matching product records.
    def search_product(self,conditions,params,sessionInformation):

        words = " ".join([p.strip('%') for p in params[::2]])
        self.create_search(words,sessionInformation)
        where_clause = " AND ".join(conditions)

        sql = (
            "SELECT pid, name, category, price, stock_count "
            "FROM products "
            "WHERE " + where_clause + ";"
        )
        try:
            cur = self.conn.execute(sql, params)
            rs = cur.fetchall()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error in search_product()\n")
            print(e)
            return None   
    
    #   Retrieve detailed product information by product ID.
    #   Args:
    #       pid (int): Product ID.
    #   Returns:
    #           sqlite3.Row: Product details (name, category, price, etc.)
    def get_product_details(self,pid):

        try:
            cur = self.conn.execute("SELECT name, category, price, stock_count,descr FROM products WHERE pid = ? ;",(pid,))
            rs = cur.fetchone()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_product_details()\n")
            print(e)
            return None
        
    #   Record that the customer viewed a specific product.
    #   Args:
    #       sessionInformation (SessionInf): Current session information.
    #       pid (int): ID of the viewed product.
    def create_viewed_product(self,sessionInformation,pid):
        
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur = self.conn.execute("INSERT INTO viewedProduct (cid,sessionNo,ts,pid) VALUES (?,?,?,?);",(sessionInformation.cid,sessionInformation.sessionNo,ts,pid))
            self.commit()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in create_viewed_product()\n")
            print(e)
            self.conn.rollback()

    #   Check if the given product is already in the customer's cart.
    #   Args:
    #       sessionInformation (SessionInf): Current session details.
    #       pid (int): Product ID.
    #   Returns:
    #           sqlite3.Row or None: Existing cart record if present.
    def check_add_to_cart(self,sessionInformation,pid):

        try:
            cur = self.conn.execute("SELECT qty FROM cart WHERE cid = ? and sessionNo = ? and pid = ?;",(sessionInformation.cid,sessionInformation.sessionNo,pid,))
            rs = cur.fetchone()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error in check_add_to_cart()\n")
            print(e)
            return None
    

    #   Retrieve the current stock count for a given product.
    #   Args:
    #       pid (int): Product ID.
    #   Returns:
    #           sqlite3.Row or None: Row containing stock_count.
    def check_stock(self,pid):

        try:
            cur = self.conn.execute("SELECT stock_count FROM products WHERE pid = ?;",(pid,))
            rs = cur.fetchone()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error in check_stock()\n")
            print(e)
            return None
        
    #   Add or update a product in the customer's cart.
    #   Args:
    #       sessionInformation (SessionInf): Current session information.
    #       pid (int): Product ID.
    #       qty (int): Quantity to add or set.
    #       mode (str): 
    #           "add" – increment existing quantity (or insert new record)
    #           "set" – replace quantity with a new value
    #   Returns:
    #           bool: True if operation succeeded, False otherwise.
    def add_to_cart(self,sessionInformation,pid,qty,mode):
        
        new_qty = qty
        rs = self.check_add_to_cart(sessionInformation,pid)     #   Check if product already in cart
        rs2 = self.check_stock(pid)                             #   Get available stock
        if mode == "add":
            #   Add new item if not already in cart
            if rs is None and (rs2["stock_count"] > 0):
                try:
                    cur = self.conn.execute("INSERT INTO cart (cid,sessionNo,pid,qty) VALUES (?,?,?,?);",(sessionInformation.cid,sessionInformation.sessionNo,pid,new_qty))
                    self.commit()
                    return True
                except sqlite3.Error as e:
                    print("\n[X] SQL Error in add_to_cart() for new item add to cart\n")
                    print(e)
                    self.conn.rollback()
                    return False
            else:
                #   Item already exists; increment quantity
                new_qty = rs["qty"] + qty

        elif mode == "set":
            new_qty = qty
        #   Remove item if new quantity is 0
        if new_qty == 0:
            self.delete_cart_items(sessionInformation,pid)
            return True
        #   Update cart quantity if stock is sufficient
        if new_qty <= rs2["stock_count"]:
            try:
                cur = self.conn.execute("UPDATE cart SET qty = ? WHERE cid = ? and sessionNo = ? and pid = ? ;",(new_qty,sessionInformation.cid,sessionInformation.sessionNo,pid))
                self.commit()
            except sqlite3.Error as e:
                print("\n[X] SQL Error in add_to_cart() for update qty\n")
                print(e)
                self.conn.rollback()
            return True
        else:         
            print("\nNot enough stock!")
            return False

    #   Retrieve all items in the current customer's cart.
    #   Args:
    #       sessionInformation (SessionInf): Current session information.
    #   Returns:
    #           list[sqlite3.Row]: List of cart items joined with product info.
    def get_cart_items(self,sessionInformation):

        try:
            cur = self.conn.execute("""
                SELECT ct.pid, p.name, p.price, ct.qty, p.stock_count,
                       (p.price * ct.qty) AS total
                FROM cart ct
                JOIN products p ON ct.pid = p.pid
                WHERE ct.cid = ? AND ct.sessionNo = ?;
            """, (sessionInformation.cid, sessionInformation.sessionNo))
            rs = cur.fetchall()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error get_cart_items()\n")
            print(e)
            return None
    
    #   Delete an item from the customer's cart.
    #   Args:
    #       sessionInformation (SessionInf): Current session info.
    #       pid (int): Product ID to remove.
    #   Returns:
    #           bool: True if delete succeeded, False otherwise.
    def delete_cart_items(self,sessionInformation,pid):

        try:
            cur = self.conn.execute("DELETE FROM cart WHERE cid = ? AND sessionNo = ? AND pid = ?;", (sessionInformation.cid, sessionInformation.sessionNo,pid))
            self.commit()
            return True
        except sqlite3.Error as e:
            print("\n[X] SQL Error delete_cart_items()\n")
            print(e)
            self.conn.rollback()         
            return False 
   
    #   Generate a new order from the current customer's cart.
    #   Performs stock checks and uses a transaction to ensure consistency.
    #   Args:
    #       sessionInformation (SessionInf): Current session details.
    #       shipping_address (str): Address for shipment.
    #   Returns:
    #           int or None: The order number if successful, or None if failed.
    def create_order(self,sessionInformation,shipping_address):

        rs = self.get_cart_items(sessionInformation)
        if not rs:
            print("\n[X] Your cart is empty!")
            return None
        
        odate = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ono = self.get_max_orderNo()
        shipping_address = shipping_address

        try:
            #   Begin transaction
            if not self.conn.in_transaction:
                self.conn.execute("BEGIN IMMEDIATE;")
            #   Insert order header
            cur = self.conn.execute("INSERT INTO orders (ono,cid, sessionNo, odate, shipping_address) VALUES (?,?, ?, ?, ?);",
                (ono,sessionInformation.cid, sessionInformation.sessionNo, odate, shipping_address)
            )
            index = 1
            for row in rs:
                pid = row['pid']
                qty = row['qty']
                stock = row['stock_count']
                price = row['price']
                name = row['name']

                #   Check stock before inserting order line
                if stock < qty:
                    print("\n[X] Not enough stock for product: ", name)
                    print("\n[X] Avaliable in store: ",stock)
                    self.conn.execute("ROLLBACK;")
                    print("\n[X] Checkout cancelled. Please try again later.")
                    return None
                
                #   Insert each order line and update stock
                self.conn.execute("INSERT INTO orderlines (ono, lineNo, pid, qty, uprice) VALUES (?, ?, ?, ?, ?);",
                    (ono, index, pid, qty, price))
                self.conn.execute("UPDATE products SET stock_count = stock_count - ? WHERE pid = ?;",(qty, pid))
                index = index + 1
            #   Clear cart and commit
            self.clear_cart(sessionInformation)
            return ono
            
        except sqlite3.Error as e:
            print("\n[X] SQL Error during order creation:")
            print(e)
        
            if self.conn.in_transaction:
                self.conn.execute("ROLLBACK;")
            print("\n[X] Transaction rolled back. No changes were made.")
            return None

    def clear_cart(self,sessionInformation):
        try:
            #   Clear cart and commit
            cur = self.conn.execute( "DELETE FROM cart WHERE cid = ? AND sessionNo = ?;",(sessionInformation.cid, sessionInformation.sessionNo))
            self.commit()
            return None
        except sqlite3.Error as e:
            print("\n[X] SQL Error in clear_cart()\n")
            print(e)
            return None

    
    
    #   Retrieve detailed order information by order number .
    #   Args:
    #       ono (int): order number.
    #   Returns:
    #           sqlite3.Row: order details (product name, product category, qty,
    #                                       unit price etc.)   
    def get_order_details(self,ono):

        try:
            cur = self.conn.execute("""
                SELECT p.name, p.category, ol.qty, ol.uprice, (ol.qty * ol.uprice) AS total
                FROM orderlines ol
                JOIN products p ON ol.pid = p.pid
                WHERE ol.ono = ?;
            """, (ono,))
            rs = cur.fetchall()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_order_details()\n")
            print(e)
            return None

    #   Retrieve all orders placed by a specific customer.
    #   Args:
    #       uid (int): Customer ID.
    #   Returns:
    #           list[sqlite3.Row]: Summary of all orders with total cost.
    def get_orders(self,uid):

        try:
            cur = self.conn.execute("""SELECT o.ono, o.odate, o.shipping_address, SUM(ol.qty * ol.uprice) AS total
                FROM orders o
                JOIN orderlines ol ON o.ono = ol.ono
                WHERE o.cid = ?
                GROUP BY o.ono, o.odate, o.shipping_address
                ORDER BY o.odate DESC;
            """, (uid,))
            rs = cur.fetchall()
            return rs
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_orders()")
            print(e)
            return None
    def get_product_by_pid(self, pid):
        try:
            cur = self.conn.execute(
                "SELECT pid, name, category, price, stock_count, descr FROM products WHERE pid = ?;",
                (pid,),
            )
            return cur.fetchone()
        except sqlite3.Error as e:
            print("\n[X] SQL Error in get_product_by_pid()\n"); 
            print(e)
            return None

    def update_product_price(self, pid, new_price) -> bool:
        try:
            self.conn.execute("UPDATE products SET price = ? WHERE pid = ?;", (new_price, pid))
            self.commit()
            return True
        except sqlite3.Error as e:
            print("\n[X] SQL Error in update_product_price()\n"); 
            print(e)
            self.conn.rollback()
            return False

    def update_product_stock(self, pid, new_stock) -> bool:
        try:
            self.conn.execute("UPDATE products SET stock_count = ? WHERE pid = ?;", (new_stock, pid))
            self.commit()
            return True
        except sqlite3.Error as e:
            print("\n[X] SQL Error in update_product_stock()\n"); 
            print(e)
            self.conn.rollback()           
            return False

    def weekly_sales_metrics(self):
        """
        Weekly sales report for the last 7 days (inclusive).
        Returns dict: {orders, products, customers, avg_per_customer, total_sales}
        """
        try:
            params = ()
            q_orders = (
                "SELECT COUNT(DISTINCT o.ono) FROM orders o "
                "WHERE date(o.odate) >= date('now','-6 day') AND date(o.odate) <= date('now');"
            )
            orders = self.conn.execute(q_orders, params).fetchone()[0]

            q_products = (
                "SELECT COUNT(DISTINCT ol.pid) FROM orderlines ol "
                "JOIN orders o ON ol.ono=o.ono "
                "WHERE date(o.odate) >= date('now','-6 day') AND date(o.odate) <= date('now');"
            )
            products = self.conn.execute(q_products, params).fetchone()[0]

            q_customers = (
                "SELECT COUNT(DISTINCT o.cid) FROM orders o "
                "WHERE date(o.odate) >= date('now','-6 day') AND date(o.odate) <= date('now');"
            )
            customers = self.conn.execute(q_customers, params).fetchone()[0]

            q_total = (
                "SELECT COALESCE(SUM(ol.qty * ol.uprice),0) FROM orderlines ol "
                "JOIN orders o ON ol.ono=o.ono "
                "WHERE date(o.odate) >= date('now','-6 day') AND date(o.odate) <= date('now');"
            )
            total_sales = self.conn.execute(q_total, params).fetchone()[0]

            avg_per_customer = (total_sales / customers) if customers else 0.0
            return {
                'orders': orders,
                'products': products,
                'customers': customers,
                'avg_per_customer': round(avg_per_customer, 2),
                'total_sales': round(total_sales, 2),
            }
        except sqlite3.Error as e:
            print("\n[X] SQL Error in weekly_sales_metrics()\n"); print(e)
            return None

    def top_products_by_distinct_orders(self):
        """Top products by count of DISTINCT orders; returns top-3 including ties at rank 3."""
        try:
            rows = self.conn.execute(
                """
                SELECT p.pid, p.name, COUNT(DISTINCT ol.ono) AS cnt
                FROM orderlines ol
                JOIN products p ON p.pid = ol.pid
                GROUP BY p.pid, p.name
                ORDER BY cnt DESC, p.pid ASC;
                """
            ).fetchall()
            return self._top3_with_ties(rows, key='cnt')
        except sqlite3.Error as e:
            print("\n[X] SQL Error in top_products_by_distinct_orders()\n"); print(e)
            return []

    def top_products_by_views(self):
        """Top products by total views; returns top-3 including ties at rank 3."""
        try:
            rows = self.conn.execute(
                """
                SELECT p.pid, p.name, COUNT(*) AS views
                FROM viewedProduct v
                JOIN products p ON p.pid = v.pid
                GROUP BY p.pid, p.name
                ORDER BY views DESC, p.pid ASC;
                """
            ).fetchall()
            return self._top3_with_ties(rows, key='views')
        except sqlite3.Error as e:
            print("\n[X] SQL Error in top_products_by_views()\n"); print(e)
            return []

    @staticmethod
    def _top3_with_ties(rows, key):
        """rows: list of sqlite3.Row with numeric column `key`."""
        if not rows:
            return []
        counts = [r[key] for r in rows]
        unique_counts = sorted(set(counts), reverse=True)
        if len(unique_counts) <= 2:
            cutoff = unique_counts[-1]
        else:
            cutoff = unique_counts[2]  # 3rd distinct value
        return [dict(pid=r['pid'], name=r['name'], count=r[key]) for r in rows if r[key] >= cutoff]
# --- END new sale helper function ---------------------------------------------
  
#   This class contains all menu and interaction logic for a customer user.
#   It connects to dbFunctions for database operations such as:
#       - Searching products
#       - Managing cart 
#       - Placing and viewing orders
#       - Recording viewed items and sessions

#   This class contains all menu and interaction logic for a customer user.
#   It connects to dbFunctions for database operations such as:
#       - Searching products
#       - Managing cart 
#       - Placing and viewing orders
#       - Recording viewed items and sessions
class customerFunctions:

    #   Initialize the customer session when the user logs in.
    #   Args:
    #       user (User): Logged-in user information.
    #       db (dbFunctions): Active database connection handler.
    def __init__(self, user:User,db:dbFunctions):
        self.userinf = user
        self.db = db
        self.sessionInformation = None
#        cid = user.uid
    
    #   Display the main customer menu and handle user input.
    #   Allows access to product search, cart management, and orders.

    def check_session(self):
        if self.sessionInformation is None:
            self.sessionInformation = self.db.create_session(self.userinf.uid)

    def customer_logout(self):
        print("\n[...] Logging out")
        if self.sessionInformation is not None:
            self.db.update_session(self.sessionInformation)
            self.db.clear_cart(self.sessionInformation) 
        print("\n [✓] You have been logged out successfully!")
        self.sessionInformation = None
        
        return "Logout"
  
    def customer_page(self):

        print("\n\n\n========= Main Menue (Customer)  =========")
        print("\n[✓] Welcome back,",self.userinf.name)

        while True:
            print("\n========= Please select what you want to do =========")
            print("1. Search products")
            print("2. View cart")
            print("3. My orders")
            print("4. Logout")
            print("5. Exit program")
            print("===========================")

            choice = input("Please enter your choice: ").strip()
            if choice == "1":
                result = self.customer_search()
                if result == "Logout":
                    return "Logout"
            elif choice == "2":
                result = self.customer_view_Cart()
                if result == "Logout":
                    return "Logout"
            elif choice == "3":
                result = self.customer_previous_order()
                if result == "Logout":
                    return "Logout"
            elif choice == "4":
                return self.customer_logout()
            elif choice == "5":
                if self.sessionInformation is not None:
                    self.db.clear_cart(self.sessionInformation)
                    self.db.update_session(self.sessionInformation)
                print("\n[...] Exiting program.Thank you for using our program!")
                sys.exit(1)
            else:
                print("\n[X] Invalid input!Please select 1,2,3,4 or 5")

    #   Prompt customer to enter keywords and perform product search.
    #   The keywords are stored in the search table for tracking.
    def customer_search(self):

        while True:
            search = input("\nPlease enter keywords:").strip().lower()
            if not search:
                search = input("\n[X] Keywords can not be empty:\n").strip().lower()
            else:
                break
        #   Build WHERE conditions dynamically for multi-word searches
        
        #   Automatically create a session for this customer
        self.check_session()

        conditions = []
        params = []
        keywords = search.split()

        for k in keywords:
            conditions.append("(LOWER(name) LIKE ? OR LOWER(descr) LIKE ?)")
            params = params + [f"%{k}%"] * 2
        rs = self.db.search_product(conditions, params, self.sessionInformation)
        if not rs:
            print("\n[!] There is no result according to the keyword:",search)
            return None
        frm = 'products'
        return self.show_product_orders(rs,frm)

    #   Display paginated results for products or orders.
    #   Supports navigation (Next / Previous / Back / Exit).
    #   Args:
    #       result (list): List of products or orders to display.
    #       frm (str): "products" or "orders" to determine display mode.
    def show_product_orders(self,result,frm):

        frm = frm
        page = 0 
        product_per_page = 5

        #   Check if the result can be divided by 5
        total_page = ( len(result) // product_per_page )

        if len(result) % product_per_page != 0:
            total_page = total_page + 1
        self.display_products_orders(page,product_per_page,result,frm)
        
        while True:

            print("===========================")

            choice = input("[N]ext\t\t [P]rev\t\t [#]Select \t\t [B]ack\t\t [L]ogout\t\n ").strip().upper()

            if choice.isdigit():
                if int(choice) <= 0 or int(choice) > 5:
                    print("\nInvalid Number! Please enter 1 to 5 to see Details!\n")
                else:
                    index = ( page * product_per_page ) + int(choice) - 1
                    res = self.product_orders_details(index,result,frm)
                    if res == "Logout":
                        return "Logout"
                    self.display_products_orders(page, product_per_page, result, frm)
            elif choice == "N":
                if page < (total_page - 1):
                    page = page + 1
                    self.display_products_orders(page, product_per_page, result, frm)
                else:
                    self.display_products_orders(page, product_per_page, result, frm)
                    print("\n[X] This is the last page!")
            elif choice == "P":
                if page >= 1:
                    page = page - 1
                    self.display_products_orders(page, product_per_page, result, frm)
                else:
                    self.display_products_orders(page, product_per_page, result, frm)
                    print("\n[X] This is the first page!")
            elif choice == "B":
                print("\n[......] Backing to Search Page")
                return None
            elif choice == "L":
                return self.customer_logout()
            else:
                print("\n[X] Invalid input!")

    #   Show summary of products or orders for the current page.
    #   Args:
    #       page (int): Current page index.
    #       product_per_page (int): Number of records per page.
    #       result (list): Data rows to display.
    #       frm (str): 'products' or 'orders'.
    def display_products_orders(self,page,product_per_page,result,frm):
        
        start_index = page * product_per_page
        end_index = start_index + product_per_page
        count = 1
        print("\n\n")
        order_total = 0
        if frm == "products":
            for row in result[start_index:end_index]:
                print(count,"Product Name:\t\t",row['name'])
                print("\n  Product Price:\t",row['price'])
                print("\n  Product Stock:\t",row['stock_count'])
                print("\n")
                count = count + 1
            print("Current Page number:", (page + 1))
        elif frm == "orders":
            for row in result[start_index:end_index]:
                print(count,". Order number:\t\t",row['ono'])
                print("\n    Date:\t\t",row['odate'])
                print("\n    Shipping:\t\t",row['shipping_address'])
                print("\n    Total:\t\t",row['total'])
                print("\n")
                count = count + 1
            print("Current Page number:", (page + 1))
                 
    #   Display detailed information for a selected product or order.
    #   Args:
    #       index (int): Index of selected item in result list.
    #       result (list): Search or order results.
    #       frm (str): Indicates display type ('products' or 'orders').
    def product_orders_details(self,index,result,frm):

        if index >= 0 and index < len(result):        
            if frm == "products":
                pid = result[index]["pid"]
                rs2 = self.db.get_product_details(pid)
                if rs2 is None:
                    print("\n[!] We do not have this product in store!")
                    return None
                
                #   Record as viewed
                self.db.create_viewed_product(self.sessionInformation,pid)
                    #   Display product details
                print("\n  Product Name:\t\t",rs2['name'])
                print("\n  Product Price:\t",rs2['price'])
                print("\n  Product Stock:\t",rs2['stock_count'])
                print("\n  Product description:\t",rs2['descr'])
                        
                #   Offer to add to cart
                while True:
                    choice = input("\nDo you want to add this product into your cart? (Y/N):").strip().upper()
                    if choice == "Y":
                        if rs2['stock_count'] <= 0:
                            print("\nSorry! This product is now out of stock.")
                        else:
                            qty = 1
                            mode = 'add'
                            flag = self.db.add_to_cart(self.sessionInformation, pid, qty,mode)
                            if flag:
                                print("\n[✓] Added to cart Sucessfully!")
                            else:
                                print("\n[X] Added to cart failed")
                        break
                    elif choice == "N":
                        break
                    elif choice == "L":
                        return self.customer_logout()    # return "Logout"
                    else:
                        print("\n[X] Invalid input!Please enter Y/N!")
                
                opt = self.customer_options_bak_or_logout() 
                if opt == "Logout":
                    return "Logout"
                return None
                            
            elif frm == "orders":
                ono = result[index]["ono"]
                rs = self.db.get_order_details(ono)
                if not rs:
                    print(f"\n[X] No details found for order number ",ono)
                    return None
                
                odate = result[index]["odate"]
                shipping_address = result[index]["shipping_address"]
                print("\n======= Order details =======")
                print("\nOrder number:",ono,"\tDate:", odate)
                print("Shipping Address:\t ",shipping_address)
                print("\n")
                print(f"{'Product Name':25}{'Category':20}{'Qty':>8}{'Unit Price':>15}{'Total':>15}")
                print("---------------------------------------------------------------------------------------")
            
                order_total = 0
                for row in rs:
                    print(f"{row['name']:25}{row['category']:20}{row['qty']:>8}{row['uprice']:>15.2f}{row['total']:>15.2f}")
                    order_total = row['total'] + order_total
                print("---------------------------------------------------------------------------------------")
                print(f"{'Order Total:':>70}{order_total:>15.2f}")
                print("=======================================================================================")
                
                opt = self.customer_options_bak_or_logout() 
                if opt == "Logout":
                    return "Logout"
                return None
            
        else:
            print("\n[X] Number out of range! Check items in current page!")
            return None
    
    #   Display options after an action is completed.
    #   Allows user to go back or quit the program.
    def customer_options_bak_or_logout(self):

        print("\nOptions:")
        while True:
            choice = input("\n[B]ack    [L]ogout: ").strip().upper()
            if choice == "B":
                print("\n[...] Returning to previous page...\n")
                return "Back"                      # go back to list
            elif choice == "L":
                return self.customer_logout()    # will return "Logout"
            else:
                print("\n[X] Invalid input! Enter B or L only.")

    #   Display all items currently in the customer's shopping cart.
    #   Also calculates and prints the total cost of all items.
# customerFunctions: show cart with 1..n numbering, per-item subtotal, and total
    def display_cart(self):
        rs = self.db.get_cart_items(self.sessionInformation)
        if not rs:
            print("\n=============== Your Shopping Cart ===============")
            print("(empty)")
            return

        print("\n=============== Your Shopping Cart ===============")
        print(f"{'#':>2}  {'Product Name':25} {'Qty':>5} {'Price':>10} {'Subtotal':>12}")
        print("-" * 60)
        total_price = 0.0
        for i, row in enumerate(rs, start=1):
            subtotal = float(row['total'])
            total_price += subtotal
            print(f"{i:>2}  {row['name'][:25]:25} {row['qty']:>5} {row['price']:>10.2f} {subtotal:>12.2f}")
        print("-" * 60)
        print(f"{'Total:':>46} {total_price:>12.2f}")


    #   Allow the customer to update the quantity of a specific item in the cart.
    #   Args:
    #       SessionInformation (SessionInf): Current session info.
    #       rs (list): List of cart items retrieved from the database.
    def update_cart_items(self,SessionInformation,rs):
        
        if not rs:
            print("\n Your shopping cart now is empty!")
            self.customer_options()
            return
        #   Choose which item to update
        while True:
            index = input("Which product your want to update?(Please enter #):").strip()
            if not index.isdigit():
                print("\n[X] Invalid number!Please enter again!")
                continue
            index = int(index)
            if index <= len(rs) and index >= 1:
                entered = rs[index -1]
                pid = entered['pid']
                stock = entered['stock_count']
                break
            else:
                print("[X] Invalid number!Please enter again!")
        
        #   Enter the new quantity
        while True:
            qty_str = input(f"Enter new quantity (0 to remove, max {stock}): ").strip()
            if not qty_str.isdigit():  
                print("\n[X] Invalid number! Please enter a non-negative integer.")
                continue

            qty = int(qty_str)
            if qty > stock:
                print(f"[!] Not sufficient qty in store! Max allowed is {stock}.")
                continue

            print("\n[......] Updating!")
            break
       # Update or remove item
        mode = 'set'
        removed = (qty == 0)
        flag = self.db.add_to_cart(self.sessionInformation, pid, qty, mode)
        if flag:
            if removed:
                print("\n[✓] Item removed from your cart!")
            else:
                print("\n[✓] Quantity updated successfully!")
        else:
            print("\n[X] Update failed. Please try again.")

        
    #   Remove an item completely from the customer's cart.
    #   Args:
    #       SessionInformation (SessionInf): Current session information.
    #       rs (list): List of current cart items.# customerFunctions: remove an item by its list number (1..n), with robust input checking
    def remove_cart_items(self, SessionInformation: SessionInf, rs: list):
        if not rs:
            print("\nYour shopping cart now is empty!")
            self.customer_options()
            return None

        # Show a compact numbered list for removal
        print("\nWhich item do you want to remove?")
        print(f"{'#':>2}  {'Product Name':25} {'Qty':>5}")
        print("-" * 40)
        for i, row in enumerate(rs, start=1):
            print(f"{i:>2}  {row['name'][:25]:25} {row['qty']:>5}")
        print("-" * 40)

        # Keep prompting until a valid number or 'B' is entered
        while True:
            choice = input(f"Enter item number to remove (1..{len(rs)}), or B to go back: ").strip().upper()
            if choice == "B":
                print("\n[......] Returning to previous page...")
                return
            if not choice.isdigit():
                print("\n[X] Invalid input! Please enter a number or 'B'.")
                continue
            idx = int(choice)
            if not (1 <= idx <= len(rs)):
                print(f"\n[X] Out of range! Please enter 1..{len(rs)}.")
                continue
            pid = rs[idx - 1]['pid']  # Map list index to the actual product id
            break

        # Perform deletion and report result
        ok = self.db.delete_cart_items(self.sessionInformation, pid)
        if ok:
            print("\n[✓] Item removed from your cart!")
        else:
            print("\n[X] Delete failed. Please try again.")
        # Return to the prior menu; View Cart will refresh on next entry
        opt = self.customer_options_bak_or_logout() 
        if opt == "Logout":
            return "Logout"
        return None


    #   Process checkout for all items currently in the cart.
    #   Prompts for a shipping address and confirms the order.
    #   Args:
    #       SessionInformation (SessionInf): Current session information.
    def check_out(self,SessionInformation):
        rs = self.db.get_cart_items(self.sessionInformation)
        if not rs:
            print("\nYour shopping cart is empty now!")
            return None
        
        print("\n\n========= Check out ========= ")
        while True:
            shipping_address = input("Please enter your shipping address:").strip()
            if not shipping_address:
                print("\n[X] Shipping adress can not be empty!")
            else:
                break
            
        while True:
            choice = input("Please confirm check out?(Y/N)").strip().upper()
            if choice == "Y":
                print("\n[......] Generating your order")
                ono = self.db.create_order(self.sessionInformation,shipping_address)
                if ono:
                    print("\n[✓] Place order sucessfull! Your order number is:",ono)
                    opt = self.customer_options_bak_or_logout() 
                    if opt == "Logout":
                        return "Logout"
                    return None
                else:
                    print("\n[X] Place order failed! Please check out again later!")
                    opt = self.customer_options_bak_or_logout() 
                    if opt == "Logout":
                        return "Logout"
                    return None
            elif choice == "N":
                print("\n[......] Cancelling your check out")
                print("\n[......] Backing to Main Menue")               
                return None
            else:
                print("\n[X] Invalid enter!Please enter Y/N")
            
        return None

    #   Display the customer's shopping cart and handle menu options:
    #   - Update quantity
    #   - Remove item
    #   - Checkout
    #   - Return to main menu
    def customer_view_Cart(self):

        
        self.check_session()
        while True:
            rs = self.db.get_cart_items(self.sessionInformation)
            if not rs:
                print("\nYour cart is empty!")
                opt = self.customer_options_bak_or_logout() 
                if opt == "Logout":
                    return "Logout"
                return None
            else:
                self.display_cart()

            print("\nOption:")
            print("\n[U]pdate    [R]emove    [C]heck out    [B]ack    [L]ogout:")
            print("===========================")

            choice = input("\nPlease enter your choice:").strip().upper()
            if choice == "U":
                self.update_cart_items(self.sessionInformation,rs)
            elif choice == "R":
                res = self.remove_cart_items(self.sessionInformation,rs)
                if res == "Logout":
                    return "Logout"
            elif choice == "C":
                res = self.check_out(self.sessionInformation)
                if res == "Logout":
                    return "Logout"
            elif choice == "B":
                return None
            elif choice == "L":
                return self.customer_logout()
            else:
                print("\n[X] Invalid input!")
    
    #   Display all previous orders placed by the current customer.
    #   Allows viewing detailed contents of any past order.
    def customer_previous_order(self):

        self.check_session()
        rs = self.db.get_orders(self.userinf.uid)
        if not rs:
            print ("\n[!] You have not place any order!")
            return
        frm = 'orders'
        return self.show_product_orders(rs,frm)
        
class SalesFunctions:   

    def __init__(self, user:User,db:dbFunctions):
        self.userinf = user
        self.db = db


    def sales_page(self):
        while True:
            print("\n\n\n========= Main Menue (Sales) =========")
            print("\n========= Please select what you want to do =========")
            print("1. Update product information")
            print("2. Weekly sales report (last 7 days)")
            print("3. Top products (by distinct orders & by views)")
            print("4. Logout")
            print("5.Exit program")
            print("===========================")
            choice = input("Please enter your choice: ").strip()
            if choice == "1":
                self.update_product_flow()
            elif choice == "2":
                self.show_weekly_report()
            elif choice == "3":
                self.show_top_products()
            elif choice == "4":
                print("\nSee you next time!")
                return 
            elif choice =="5":
                print("\nExting program......")
                sys.exit(0)  
            else:
                print("\n[X] Invalid input! Please select 1,2,3,4")

    def update_product_flow(self):
        # --- PID: loop until a valid integer pid that exists; allow 'q' to cancel ---
        while True:
            pid_in = input("Enter product id to view/update (q to cancel): ").strip().lower()
            if pid_in == "q":
                print("[...] Cancelled.")
                return
            if not pid_in.isdigit():
                print("[X] pid must be a positive integer. Try again.")
                continue
            pid = int(pid_in)
            row = self.db.get_product_by_pid(pid)
            if row is None:
                print("[X] No such product. Try another pid.")
                continue
            break

        print("\nCurrent product info:")
        print(f"PID: {pid}\nName: {row['name']}\nCategory: {row['category']}\n"
            f"Price: {row['price']}\nStock: {row['stock_count']}\nDescr: {row['descr']}")

        # --- Update price: loop until valid float >= 0 or blank to skip; 'q' cancels whole flow ---
        while True:
            np = input("Enter new price (blank to skip, q to cancel): ").strip().lower()
            if np == "":
                break  # skip price update
            if np == "q":
                print("[...] Cancelled."); return
            try:
                npv = float(np)
                if npv < 0:
                    print("[X] Price cannot be negative. Try again.")
                    continue
                if self.db.update_product_price(pid, npv):
                    print("[✓] Price updated.")
                break
            except ValueError:
                print("[X] Invalid price (must be a number). Try again.")

        # --- Update stock: loop until valid non-negative integer or blank to skip; 'q' cancels ---
        while True:
            ns = input("Enter new stock (integer, blank to skip, q to cancel): ").strip().lower()
            if ns == "":
                break  # skip stock update
            if ns == "q":
                print("[...] Cancelled."); return
            if ns.isdigit():
                nsv = int(ns)
                if self.db.update_product_stock(pid, nsv):
                    print("[✓] Stock updated.")
                break
            else:
                print("[X] Invalid stock (must be a non-negative integer). Try again.")

    def show_weekly_report(self):
        metrics = self.db.weekly_sales_metrics()
        if not metrics:
            print("[X] Could not compute weekly sales metrics.")
            return
        print("\n===== Weekly Sales Report (last 7 days inclusive) =====")
        print(f"Distinct orders:           {metrics['orders']}")
        print(f"Distinct products sold:    {metrics['products']}")
        print(f"Distinct customers:        {metrics['customers']}")
        print(f"Avg spent per customer:    {metrics['avg_per_customer']}")
        print(f"Total sales amount:        {metrics['total_sales']}")

    def show_top_products(self):
        print("\n===== Top by Distinct Orders (with ties at rank 3) =====")
        ords = self.db.top_products_by_distinct_orders()
        if not ords:
            print("(no data)")
        else:
            for i, r in enumerate(ords, start=1):
                print(f"{i}. PID {r['pid']}  {r['name']}  orders={r['count']}")

        print("\n===== Top by Views (with ties at rank 3) =====")
        views = self.db.top_products_by_views()
        if not views:
            print("(no data)")
        else:
            for i, r in enumerate(views, start=1):
                print(f"{i}. PID {r['pid']}  {r['name']}  views={r['count']}")
# --- END SalesFunctions --------------------------------------------------

#   Handle login for existing users.
#   Prompts for:
#       - User ID (integer)
#       - Password (masked via getpass)
#   Validates credentials from the `users` table and directs the user
#   to either the Customer or Sales menu based on role.
#   Args:
#       db (dbFunctions): Active database connection handler.
def login(db:dbFunctions):

    #   --- Step 1: Prompt for valid integer user ID ---
    while True:
        try:
            userID = int(input("\nPlease enter UserID:").strip())
            break
        except ValueError:
            print("\n[X]Invalid ID. UserID must be Integer!")
        #   --- Step 2: Retrieve stored user record ---
    rs_user = db.login_verify(userID)
    if not rs_user:
        print("\n[X] User Does not Exist!Please sign up first!\n")
        return None

    #   --- Step 3: Prompt for non-empty password (masked input) ---
    while True:
        password = getpass.getpass("\nPlease enter Password: ").strip()
        if not password:
            print("\n[X] Password cannot be empty!")
        else:
            break
    
    #   --- Step 4: Compare entered password (plain text) ---
    #   According to updated TA instructions: passwords are not hashed,
    #   but password input must be masked (getpass).
    if password == rs_user.psw:
        return rs_user
    else:
        print("[X] Password is not correct!")
        return None
 
 #  Register a new customer account.
 #  Prompts for name, email, and password.
 #  Ensures email uniqueness, creates new user and customer records,and then launches the customer menu.
 #  Args:
 #      db (dbFunctions): Active database connection handler.
def register(db:dbFunctions):
    
    #   --- Step 1: Get user information ---
    while True:
        userName = input("\nPlease enter your name:").strip()
        if not userName:
            print("\n[X] userName cannot be empty!")
        else:
            break 
    while True:
        email = input("\nPlease enter email address:").strip().lower() 
        if not email:
            print("\n[X] email cannot be empty!")
        elif "@" not in email:
            print("\n[X] PLease enter correct email!")        	
        else:
            break 

    while True:
        password = getpass.getpass("\nPlease enter Password: ").strip()
        if not password:
            print("\n[X] password cannot be empty!")
        else:
            break 
    
    #   --- Step 2: Check if email already exists ---
    if db.check_email(email):
        print("\n[X] This email address already registered!\n")
        return
    #   --- Step 3: Insert customer into database ---
    rs_user = db.insert_customer(userName,email,password)
    print("\n[✓] Sign up sucessfully!\n")
    print("\nPlease remember your user id is :\n",rs_user.uid)
    print("\n[......] Loading customer page\n")
    return rs_user

#Program entry point.
#   Displays the initial login / registration menu and controls
def main():
    print(">>> Program started successfully!")

    #   ---- Read database path from command line argument ----
    if len(sys.argv) < 2:
        print("\n[X] Missing database file name!")
        sys.exit(1)

    db_path = sys.argv[1]
    print(f"\n[✓] Connected to database: {db_path}")  
    db = dbFunctions(db_path)

    #   --- Display login / registration screen ---
    while True:

        print("\n========= Login Page =========")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        print("===========================")

        choice = input("Please enter your choice: ").strip()

        if choice == "1":
            #   Existing user login
            user = login(db)
            if not user:
                continue

            if user.role == "customer":
                cust = customerFunctions(user,db)
                result = cust.customer_page()
                if result == "Logout":
                   # cust.customer_logout()
                    continue
            elif user.role == "sales":
                sales = SalesFunctions(user,db)
                result = sales.sales_page()
                if result == "Logout":
                    continue

        elif choice == "2":
           #    New user registration
           reg_user = register(db)
           if reg_user:
                cust = customerFunctions(reg_user,db)
                result = cust.customer_page()
                if result == "Logout":
                    #cust.customer_logout()
                    continue
        elif choice == "3":
            #   Exit program gracefully
            print("\n[...] Exiting program. Thank you for useing this program!")
            break
        else:
            print("\n[X] Invalid input!Please select 1,2,3")

if __name__ == "__main__":

    main()

    


    