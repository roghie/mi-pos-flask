# CASHLY - POS & INVENTORY MANAGEMENT SYSTEM
#### Video Demo:  https://youtu.be/sFLE0KC9PDk
#### Description:

A full-stack Web-based Point of Sale (POS) and Inventory Management System built with **Python (Flask)**, **SQLite**, and **Bootstrap 5**. Designed specifically for local retail stores and neighborhood shops to streamline daily checkout operations, track product inventory, manage customer lines of credit (debt tracking), and generate comprehensive financial reports.

---

## Key Features

### 1. User Role Management & Security
- **Administrator Role:** Full access to product management (CRUD operations), user account administration, customer debt registry, and store-wide financial reports.
- **Seller / Cashier Role:** Tailored interface restricted strictly to executing sales, looking up customers, registering debt partial payments, and reviewing personal daily transactions.
- **Protected First-Time Setup:** Public registration is automatically locked once the primary Administrator account is registered. Subsequent users can only be created internally through the Admin dashboard.

### 2. Inventory & Product Management (Admin Only)
- **Product Catalog Operations (CRUD):** Full management capabilities allowing Administrators to create, edit, update prices/stock levels, and delete products.
- **Real-Time Stock Tracking:** Automatic stock deduction upon sale completion, preventing sales of out-of-stock items.
- **Barcode & SKU Assignment:** Support for assigning unique numeric barcodes (EAN-13, UPC-A) or custom internal product codes for fast lookup during checkout.
- **Active / Discontinued Status:** Ability to archive or disable products without corrupting past sales records and transaction history.
- **Relational Integrity for Inventory:** Products are linked to historical sale entries (`sale_items`) using strict foreign key relationships. Deleting or modifying a product's price in the inventory table will never alter historical financial records or previous receipt totals

### 3. Point of Sale (POS) & Camera Barcode Scanning
- Real-time product search by name or numeric barcode.
- Camera-based scanning integration using the `Html5Qrcode` JavaScript library.
- **Mobile Camera Optimization:** Custom Full HD camera constraint resolution (`1920x1080`), restricted EAN/UPC barcode decoding formats, and a 2-frame consecutive reading confirmation algorithm to eliminate false readings on mobile devices (e.g., Samsung, Iphone).
- Multi-payment support: **Cash**, **QR Mobile Payment**, and **Credit / Store Debt**.

### 4. Customer Account Statements & Credit Management
- Comprehensive customer database tracking active account balances (`balance`).
- Individual **Account Statement ("Estado de Cuenta")** view showing a detailed audit trail of all credit purchases and financial receipts.
- Partial and total debt repayment modal with automatic balance recalculation.

### 5. Financial Analytics & Sales Reports
- Dynamic filtering by customizable date ranges (**Today**, **This Week**, **This Month**, **This Year**, or **Custom Dates**).
- Revenue breakdown segmented by payment method (**Cash**, **QR**, and **Credit**).
- Top 5 best-selling products chart/list.
- Admin filter to analyze performance per cashier/seller.

---

## System Architecture & File Structure

/
├── app.py                     # Primary Flask application containing all backend routes, session handlers, and access decorators (@login_required, @admin_required).
├── helpers.py                 # Utility helper functions, access control decorators (@login_required, @admin_required), and custom error handlers.
├── pos.db                     # Relational SQLite database schema storing users, products, sales, sale_items, customers, and customer_payments.
├── requirements.txt           # Python dependencies (Flask, Werkzeug, etc.).
├── static/
│   ├── styles.css             # Custom CSS styling overrides, card layouts, and responsive design rules.
│   └── favicon.ico            # Application browser tab favicon.
└── templates/
    ├── layout.html            # Main base Jinja2 template featuring role-based dynamic navigation links.
    ├── apology.html           # Error handling view displaying user-friendly error messages and status codes.
    ├── login.html             # Secure login screen with conditional initial setup warning.
    ├── register.html          # Locked registration page for initial admin account setup.
    ├── pos.html               # Interactive POS interface with cart builder and camera reader.
    ├── inventory.html         # Inventory management console (Admin only).
    ├── users.html             # User account creation and role modification panel (Admin only).
    ├── customers.html         # General customer credit overview and balances.
    ├── customer_history.html  # Detailed account statement showing sales history and payment logs for a given customer.
    └── reports.html           # Financial dashboard and sales filter analytics.
