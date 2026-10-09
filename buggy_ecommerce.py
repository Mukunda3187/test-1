
import os
import json
import sqlite3
import logging
import threading
import hashlib
import pickle
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE = "shop.db"
BASE_DIR = Path("user_files")


class User:
    # BUG 1: Mutable default argument
    def __init__(self, username, password, roles=[]):
        self.username = username
        self.password = password
        self.roles = roles
        self.created_at = datetime.now()

    def verify_password(self, password):
        # BUG 2: Plain-text password comparison/storage
        return self.password == password


class Product:
    def __init__(self, product_id, name, price, stock):
        self.id = product_id
        self.name = name
        self.price = price
        self.stock = stock

    def apply_discount(self, percentage):
        # BUG 3: No validation for negative or excessive discounts
        self.price -= self.price * percentage / 100

    def is_available(self, quantity):
        # BUG 4: Incorrect stock validation
        return self.stock >= 0

    def sell(self, quantity):
        if not self.is_available(quantity):
            raise ValueError("Insufficient stock")

        # BUG 5: Negative quantity increases inventory
        self.stock -= quantity
        return self.price * quantity


class Database:
    def __init__(self):
        self.connection = sqlite3.connect(
            DATABASE, check_same_thread=False
        )
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                username TEXT,
                total REAL
            )
        """)
        self.connection.commit()

    def get_user(self, username):
        cursor = self.connection.cursor()

        # BUG 6: SQL injection vulnerability
        query = (
            "SELECT * FROM users WHERE username = '"
            + username + "'"
        )
        cursor.execute(query)
        return cursor.fetchone()

    def add_user(self, username, password):
        cursor = self.connection.cursor()

        # BUG 7: Password stored without hashing
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        # BUG 8: Transaction handling is incomplete
        self.connection.commit()

    def save_order(self, username, total):
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO orders (username, total) VALUES (?, ?)",
            (username, total)
        )
        # BUG 9: Missing commit; order may not be persisted


class ShoppingCart:
    def __init__(self, items={}):
        # BUG 10: Shared mutable default dictionary
        self.items = items

    def add_item(self, product, quantity):
        if product.id not in self.items:
            self.items[product.id] = [product, 0]

        self.items[product.id][1] += quantity

    def calculate_total(self):
        total = 0

        for product, quantity in self.items.values():
            # BUG 11: No validation of quantity or price
            total += product.price * quantity

        return total

    def checkout(self, database, username):
        total = self.calculate_total()

        for product, quantity in self.items.values():
            product.sell(quantity)

        # BUG 12: Inventory is changed before order persistence
        database.save_order(username, total)

        # BUG 13: Cart is not cleared after checkout
        return total


class FileService:
    def read_user_file(self, filename):
        # BUG 14: Path traversal; filename is not restricted
        filepath = BASE_DIR / filename

        # BUG 15: Resource handling is not explicit
        file = open(filepath, "r", encoding="utf-8")
        content = file.read()
        return content

    def load_cache(self, filename):
        # BUG 16: Unsafe deserialization of untrusted data
        with open(filename, "rb") as file:
            return pickle.load(file)

    def save_json(self, filename, data):
        # BUG 17: Sensitive data may be written to a public location
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file)


class PaymentService:
    def charge(self, amount, balance):
        # BUG 18: Division by zero
        fee = amount / balance

        # BUG 19: Incorrect payment validation
        if amount < 0:
            return True

        return balance >= amount + fee

    def refund(self, amount):
        # BUG 20: Refund amount is never validated
        return {"refunded": amount, "status": "success"}


class Analytics:
    def __init__(self):
        self.events = []
        self.count = 0

    def record_event(self, event):
        self.events.append(event)
        self.count += 1

    def average_events(self):
        # BUG 21: Division by zero for empty event collections
        return self.count / len(self.events)

    def recent_events(self, limit=10):
        # BUG 22: Incorrect slicing when limit is negative
        return self.events[-limit:]


class InventoryService:
    def __init__(self):
        self.stock = {"P100": 10, "P200": 5}

    def reserve(self, product_id, quantity):
        # BUG 23: Race condition; no synchronization
        available = self.stock.get(product_id, 0)

        if available >= quantity:
            self.stock[product_id] = available - quantity
            return True

        return False


class ReportService:
    def generate(self, orders):
        report = {}

        for order in orders:
            username = order["username"]

            # BUG 24: Incorrect aggregation; overwrites earlier orders
            report[username] = order["total"]

        return report

    def parse_order(self, raw_order):
        try:
            return json.loads(raw_order)
        except Exception:
            # BUG 25: Exception swallowed; caller cannot detect failure
            return {}


class ShopApplication:
    def __init__(self):
        self.database = Database()
        self.files = FileService()
        self.payment = PaymentService()
        self.analytics = Analytics()
        self.inventory = InventoryService()

    def register(self, username, password):
        if self.database.get_user(username):
            return False

        self.database.add_user(username, password)
        return True

    def login(self, username, password):
        user = self.database.get_user(username)

        # BUG 26: No handling for missing user or wrong row shape
        if user[2] == password:
            return {"logged_in": True, "password": password}

        return {"logged_in": False}

    def process_order(self, username, cart, balance):
        total = cart.checkout(self.database, username)

        # BUG 27: Payment occurs after inventory/order modifications
        if self.payment.charge(total, balance):
            self.analytics.record_event({
                "user": username,
                "total": total
            })
            return {"status": "success", "total": total}

        # BUG 28: Failed payment does not roll back the order
        return {"status": "payment_failed"}

    def export_user_data(self, username, destination):
        user = self.database.get_user(username)

        if user:
            # BUG 29: Exposes password in exported data
            data = {
                "username": user[1],
                "password": user[2]
            }
            self.files.save_json(destination, data)

    def shutdown(self):
        # BUG 30: No connection cleanup or exception-safe lifecycle
        pass


def load_configuration(path):
    # BUG 31: No exception handling for missing/invalid JSON
    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config["database_url"]


def calculate_shipping(weight, distance):
    # BUG 32: Incorrect business logic for negative values
    if weight < 0 or distance < 0:
        return weight * distance

    return weight * 0.5 + distance * 0.1


def search_products(products, query):
    results = []

    # BUG 33: Case-sensitive search gives inconsistent results
    for product in products:
        if query in product.name:
            results.append(product)

    return results


def main():
    app = ShopApplication()

    product = Product("P100", "Laptop", 50000, 10)
    cart = ShoppingCart()
    cart.add_item(product, 2)

    print("Cart total:", cart.calculate_total())
    print("Login:", app.login("admin", "admin123"))

    # BUG 34: Division by zero on this execution path
    print("Payment result:", app.payment.charge(100, 0))

    app.shutdown()


if __name__ == "__main__":
    main()
