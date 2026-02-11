from src.domain.models import User, SessionInf
from src.db.repository import dbFunctions
import sys



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
        print("\n[✓] Welcome back,",self.userin4f.name)

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
        