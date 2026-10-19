import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, admin_required, bs

# Configure application
app:application

# Custom filter
app.jinja_env.filters["Bs."] = bs

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pos.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Principal screen"""
    return render_template("pos.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("Debe ingresar un nombre de usuario", 403)
        elif not password:
            return apology("Debe ingresar su contraseña", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Nombre de usuario y/o contraseña invalido", 403)
        pass
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user_role"] = rows[0].get("role", "seller")
        session["username"] = rows[0]["username"]

        # Consultar si es la primera configuración (0 usuarios en la BD)
        user_count = db.execute("SELECT COUNT(*) AS count FROM users")[0]["count"]
        if user_count == 0:
            return render_template("login.html", show_register=(user_count == 0))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Permite el registro únicamente si NO existen usuarios en la base de datos (Primer inicio)"""
    # 1. Verificar si ya existen usuarios registrados
    user_count = db.execute("SELECT COUNT(*) AS count FROM users")[0]["count"]

    if user_count > 0:
        flash("El registro público está deshabilitado. Solicita una cuenta al administrador.", "warning")
        return redirect("/login")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password:
            flash("Debes ingresar un usuario y una contraseña.", "danger")
            return render_template("register.html")

        if password != confirmation:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("register.html")

        # Verificar disponibilidad del nombre de usuario
        existing = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing:
            flash("El usuario ya existe.", "danger")
            return render_template("register.html")

        # Como es el primer usuario, se le asigna el rol 'admin'
        hash_pw = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash, role) VALUES (?, ?, 'admin')", username, hash_pw)

        flash("¡Cuenta de Administrador creada exitosamente! Ahora puedes iniciar sesión.", "success")
        return redirect("/login")

    return render_template("register.html")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Show history of transactions"""

    if request.method == "POST":
        current = request.form.get("current")
        new = request.form.get("new")
        confirm = request.form.get("confirm")

        if not current:
            return apology("Debes introducir tu contraseña actual", 400)
        elif not new:
            return apology("Debes introducir una nueva contraseña", 400)
        elif not confirm:
            return apology("Debes introducir la confirmación de tu nueva contraseña", 400)

        user_id = session["user_id"]
        user_hash = db.execute("SELECT hash FROM users WHERE id = ?", user_id)

        if not check_password_hash(user_hash[0]["hash"], current):
            return apology("Tu contraseña actual es incorrecta", 400)

        if new != confirm:
            return apology("La nueva contraseña y su confirmación no coinciden", 400)

        if current == new:
            return apology("La nueva contraseña debe ser diferente a la actual", 400)

        new_hash = generate_password_hash(new)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, user_id)

        return redirect("/")

    else:
        return render_template("change.html")


@app.route("/api/product/<barcode>")
@login_required
def get_product(barcode):
    """Endpoint API para la caja POS"""
    product = db.execute("SELECT * FROM products WHERE barcode = ?", barcode)
    if not product:
        return jsonify({"success": False, "message": "Producto no encontrado"}), 404

    return jsonify({
        "success": True,
        "product": {
            "id": product[0]["id"],
            "barcode": product[0]["barcode"],
            "name": product[0]["name"],
            "price": float(product[0]["price"]),
            "stock": product[0]["stock"]
        }
    })


@app.route("/inventory", methods=["GET", "POST"])
@login_required
@admin_required  # Restringe acceso a la lista de productos e inventario
def inventory():

    if request.method == "POST":
        barcode = request.form.get("barcode")
        name = request.form.get("name")
        price_raw = request.form.get("price")
        cost_raw = request.form.get("cost")
        stock_raw = request.form.get("stock")
        min_stock_raw = request.form.get("min_stock")
        #expiration_date = request.form.get("expiration_Date")

        # enter validation

        if not barcode or not name or not price_raw or not cost_raw or not stock_raw or not min_stock_raw:
            return apology("Todos los campos deben ser llenados", 400)

        try:
            price = float(price_raw)
            cost = float(cost_raw)
            stock = int(stock_raw)
            min_stock = int(min_stock_raw)
            #expiration_date = datetime()
        except ValueError:
            return apology("El precio de venta, costo de adquisición y/o existencias deben ser números", 400)

        try:
            db.execute("INSERT INTO products (barcode, name, price, cost, stock, min_stock) VALUES (?, ?, ?, ?, ?, ?)",
                barcode, name, price, cost, stock, min_stock) #, expiration_date)

            return redirect("/inventory")

        except ValueError:
                    return apology("Este producto ya está registrado.", 400)
    else:
        products = db.execute("SELECT * FROM products ORDER BY name ASC")
        return render_template("inventory.html", products=products)


@app.route("/api/product/<barcode>")
@login_required
def check_product(barcode):
    rows = db.execute("SELECT * FROM products WHERE barcode = ?", barcode)
    if rows:
        return jsonify({"success": True, "product": dict(rows[0])})
    return jsonify({"success": False, "product": None})


@app.route("/inventory/edit/<int:product_id>", methods=["POST"])
@login_required
def edit_product(product_id):
    """Editar un producto existente"""
    barcode = request.form.get("barcode").strip()
    name = request.form.get("name").strip()
    price = request.form.get("price")
    cost = request.form.get("cost")
    stock = request.form.get("stock")
    min_stock = request.form.get("min_stock") or 5

    if not barcode or not name or not price or not cost or not stock:
        return apology("Todos los campos obligatorios deben ser llenados", 400)

    try:
        db.execute(
            """UPDATE products
               SET barcode = ?, name = ?, price = ?, cost = ?, stock = ?, min_stock = ?
               WHERE id = ?""",
            barcode, name, float(price), float(cost), int(stock), int(min_stock), product_id
        )
        flash("Producto actualizado correctamente", "success")
        return redirect("/inventory")
    except ValueError:
        return apology("Error al actualizar. Verifique que el código de barras no esté duplicado.", 400)


@app.route("/inventory/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    """Eliminar un producto del inventario"""
    db.execute("DELETE FROM products WHERE id = ?", product_id)
    flash("Producto eliminado del inventario", "info")
    return redirect("/inventory")



@app.route("/api/product/search")
@login_required
def search_product():
    """
    Busca productos por código de barras exacto o coincidencia de nombre.
    Soporta búsqueda directa por cámara o teclado.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    # 1. Intentar búsqueda por código de barras exacto
    rows = db.execute("SELECT id, barcode, name, price, stock FROM products WHERE barcode = ?", query)

    # 2. Si no hay coincidencia por barcode, buscar por nombre
    if not rows:
        rows = db.execute(
            "SELECT id, barcode, name, price, stock FROM products WHERE name LIKE ? LIMIT 10",
            f"%{query}%"
        )

    return jsonify(rows)


@app.route("/api/customers")
@login_required
def get_customers():
    """Devuelve la lista de clientes registrados para ventas a crédito"""
    customers = db.execute("SELECT id, name, phone, balance FROM customers ORDER BY name ASC")
    return jsonify(customers)


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """Procesa la venta enviada desde pos.html"""
    data = request.get_json()

    if not data or "cart" not in data or not data["cart"]:
        return jsonify({"success": False, "message": "El carrito está vacío."}), 400

    cart = data["cart"]
    payment_type = data.get("payment_type", "cash")  # 'cash', 'qr', 'credit'
    customer_id = int(data.get("customer_id", 1))    # 1 = Cliente General

    # Validación de cliente para crédito
    if payment_type == "credit" and customer_id == 1:
        return jsonify({
            "success": False,
            "message": "Debe seleccionar un cliente registrado para ventas a crédito."
        }), 400

    total_sale = 0.0
    items_to_process = []

    # 1. Validar productos y disponibilidad de stock
    for item in cart:
        product_id = item.get("id")
        qty = int(item.get("qty", 0))

        if qty <= 0:
            continue

        rows = db.execute("SELECT * FROM products WHERE id = ?", product_id)
        if not rows:
            return jsonify({"success": False, "message": f"Producto no encontrado (ID: {product_id})."}), 400

        product = rows[0]
        if product["stock"] < qty:
            return jsonify({
                "success": False,
                "message": f"Stock insuficiente para '{product['name']}'. Disponible: {product['stock']}"
            }), 400

        subtotal = product["price"] * qty
        total_sale += subtotal

        items_to_process.append({
            "id": product_id,
            "qty": qty,
            "price": product["price"],
            "subtotal": subtotal,
            "new_stock": product["stock"] - qty
        })

    if not items_to_process:
        return jsonify({"success": False, "message": "No hay ítems válidos en el carrito."}), 400

    # 2. Registrar la venta en la tabla `sales`
    status = "pending" if payment_type == "credit" else "paid"

    sale_id = db.execute(
        """INSERT INTO sales (user_id, customer_id, total, payment_type, status)
           VALUES (?, ?, ?, ?, ?)""",
        session["user_id"], customer_id, total_sale, payment_type, status
    )

    # 3. Insertar detalle de venta y descontar stock
    for item in items_to_process:
        db.execute(
            """INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
               VALUES (?, ?, ?, ?, ?)""",
            sale_id, item["id"], item["qty"], item["price"], item["subtotal"]
        )
        db.execute("UPDATE products SET stock = ? WHERE id = ?", item["new_stock"], item["id"])

    # 4. Si fue venta a crédito, actualizar el saldo deudor del cliente
    if payment_type == "credit":
        db.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", total_sale, customer_id)

    return jsonify({
        "success": True,
        "message": "Venta realizada con éxito",
        "sale_id": sale_id,
        "total": total_sale
    })



@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    """Gestión de clientes y registro de nuevos clientes"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name:
            flash("El nombre del cliente es obligatorio.", "warning")
            return redirect("/customers")

        # Registrar cliente
        db.execute(
            "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
            name, phone, address
        )
        flash(f"Cliente '{name}' registrado con éxito.", "success")
        return redirect("/customers")

    # GET: Obtener lista de clientes ordenados por mayor deuda (excluyendo cliente general)
    customer_list = db.execute(
        "SELECT * FROM customers WHERE id != 1 ORDER BY balance DESC, name ASC"
    )
    return render_template("customers.html", customers=customer_list)


@app.route("/customers/pay", methods=["POST"])
@login_required
def customer_pay():
    """Registrar abono o pago parcial/total de deuda de un cliente"""
    customer_id = request.form.get("customer_id")
    amount_str = request.form.get("amount")
    payment_type = request.form.get("payment_type", "cash")
    notes = request.form.get("notes", "").strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("El monto del abono debe ser mayor a 0.", "danger")
            return redirect("/customers")
    except (ValueError, TypeError):
        flash("Monto inválido.", "danger")
        return redirect("/customers")

    # Consultar cliente
    rows = db.execute("SELECT * FROM customers WHERE id = ?", customer_id)
    if not rows:
        flash("Cliente no encontrado.", "danger")
        return redirect("/customers")

    customer = rows[0]

    if amount > customer["balance"]:
        flash(f"El monto (Bs. {amount:.2f}) excede la deuda actual (Bs. {customer['balance']:.2f}).", "warning")
        return redirect("/customers")

    # 1. Registrar la transacción de cobro/abono
    db.execute(
        """INSERT INTO customer_payments (customer_id, user_id, amount, payment_type, notes)
           VALUES (?, ?, ?, ?, ?)""",
        customer_id, session["user_id"], amount, payment_type, notes
    )

    # 2. Descontar el saldo adeudado
    db.execute(
        "UPDATE customers SET balance = balance - ? WHERE id = ?",
        amount, customer_id
    )

    flash(f"Abono de Bs. {amount:.2f} registrado para '{customer['name']}'.", "success")
    return redirect("/customers")


@app.route("/customers/edit", methods=["POST"])
@login_required
def customer_edit():
    """Actualiza la información de un cliente existente"""
    customer_id = request.form.get("customer_id")
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    if not customer_id or not name:
        flash("El nombre del cliente es obligatorio.", "warning")
        return redirect("/customers")

    db.execute(
        "UPDATE customers SET name = ?, phone = ?, address = ? WHERE id = ?",
        name, phone, address, customer_id
    )
    flash("Datos del cliente actualizados correctamente.", "success")
    return redirect("/customers")


@app.route("/customers/delete", methods=["POST"])
@login_required
def customer_delete():
    """Elimina un cliente si no tiene deudas pendientes ni ventas asociadas"""
    customer_id = request.form.get("customer_id")

    if not customer_id or customer_id == "1":
        flash("Operación no permitida.", "danger")
        return redirect("/customers")

    # 1. Verificar si tiene deuda pendiente
    rows = db.execute("SELECT balance, name FROM customers WHERE id = ?", customer_id)
    if not rows:
        flash("Cliente no encontrado.", "danger")
        return redirect("/customers")

    customer = rows[0]
    if customer["balance"] > 0:
        flash(f"No se puede eliminar a '{customer['name']}' porque tiene una deuda pendiente de Bs. {customer['balance']:.2f}.", "warning")
        return redirect("/customers")

    # 2. Verificar si tiene ventas registradas a su nombre
    sales_count = db.execute("SELECT COUNT(*) AS count FROM sales WHERE customer_id = ?", customer_id)[0]["count"]
    if sales_count > 0:
        flash(f"No se puede eliminar a '{customer['name']}' porque tiene historial de ventas asociadas. Puedes dejar sus datos o renombrarlo.", "warning")
        return redirect("/customers")

    # 3. Eliminar cliente
    db.execute("DELETE FROM customers WHERE id = ?", customer_id)
    flash(f"Cliente '{customer['name']}' eliminado con éxito.", "info")
    return redirect("/customers")



@app.route("/reports")
@login_required
def reports():
    """Vista de reportes de ventas con control por rol"""
    period = request.args.get("period", "today")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    selected_seller = request.args.get("seller_id", "")

    # 1. Definición del filtro por fecha
    if period == "today":
        date_clause = "DATE(created_at, 'localtime') = DATE('now', 'localtime')"
    elif period == "week":
        date_clause = "DATE(created_at, 'localtime') >= DATE('now', 'localtime', 'weekday 0', '-6 days')"
    elif period == "month":
        date_clause = "DATE(created_at, 'localtime') >= DATE('now', 'localtime', 'start of month')"
    elif period == "year":
        date_clause = "DATE(created_at, 'localtime') >= DATE('now', 'localtime', 'start of year')"
    elif period == "custom" and start_date and end_date:
        date_clause = f"DATE(created_at, 'localtime') BETWEEN '{start_date}' AND '{end_date}'"
    else:
        period = "today"
        date_clause = "DATE(created_at, 'localtime') = DATE('now', 'localtime')"

    # 2. Definición del filtro por vendedor según el Rol
    user_role = session.get("user_role")
    current_user_id = session.get("user_id")

    if user_role == "admin":
        if selected_seller:
            seller_clause = f"AND user_id = {selected_seller}"
        else:
            seller_clause = ""
        sellers_list = db.execute("SELECT id, username FROM users ORDER BY username")
    else:
        # Vendedores solo ven sus propias ventas
        seller_clause = f"AND user_id = {current_user_id}"
        sellers_list = []

    where_clause = f"{date_clause} {seller_clause}"

    # 3. Consultas SQL
    summary = db.execute(
        f"""SELECT
            COALESCE(SUM(total), 0) AS grand_total,
            COALESCE(SUM(CASE WHEN payment_type = 'cash' THEN total ELSE 0 END), 0) AS total_cash,
            COALESCE(SUM(CASE WHEN payment_type = 'qr' THEN total ELSE 0 END), 0) AS total_qr,
            COALESCE(SUM(CASE WHEN payment_type = 'credit' THEN total ELSE 0 END), 0) AS total_credit,
            COUNT(id) AS sales_count
           FROM sales
           WHERE {where_clause}"""
    )[0]

    payments_total = db.execute(
        f"""SELECT COALESCE(SUM(amount), 0) AS total
           FROM customer_payments
           WHERE {where_clause}"""
    )[0]["total"]

    top_products = db.execute(
        f"""SELECT p.name, SUM(si.quantity) AS total_qty, SUM(si.subtotal) AS total_amount
           FROM sale_items si
           JOIN sales s ON si.sale_id = s.id
           JOIN products p ON si.product_id = p.id
           WHERE {where_clause.replace('created_at', 's.created_at')}
           GROUP BY p.id
           ORDER BY total_qty DESC
           LIMIT 5"""
    )

    sales_list = db.execute(
        f"""SELECT s.id, s.created_at AS timestamp, s.total, s.payment_type, c.name AS customer_name, u.username AS seller_name
           FROM sales s
           JOIN customers c ON s.customer_id = c.id
           JOIN users u ON s.user_id = u.id
           WHERE {where_clause.replace('created_at', 's.created_at')}
           ORDER BY s.created_at DESC"""
    )

    return render_template(
        "reports.html",
        summary=summary,
        payments_total=payments_total,
        top_products=top_products,
        sales_list=sales_list,
        period=period,
        start_date=start_date,
        end_date=end_date,
        sellers=sellers_list,
        selected_seller=selected_seller
    )



from functools import wraps

def admin_required(f):
    """Decorador para restringir rutas solo a administradores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_role") != "admin":
            flash("Acceso denegado: Se requieren permisos de Administrador.", "danger")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function



from werkzeug.security import generate_password_hash

@app.route("/users", methods=["GET", "POST"])
@login_required
@admin_required
def users():
    """Gestión de Vendedores / Usuarios"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        role = request.form.get("role", "seller")

        if not username or not password:
            flash("El usuario y la contraseña son obligatorios.", "warning")
            return redirect("/users")

        existing = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing:
            flash("El nombre de usuario ya está registrado.", "warning")
            return redirect("/users")

        hash_pw = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash, role) VALUES (?, ?, ?)", username, hash_pw, role)
        flash(f"Usuario '{username}' registrado exitosamente.", "success")
        return redirect("/users")

    users_list = db.execute("SELECT id, username, role FROM users ORDER BY username")
    return render_template("users.html", users=users_list)



@app.route("/users/edit", methods=["POST"])
@login_required
@admin_required
def user_edit():
    """Editar rol o contraseña de un usuario"""
    user_id = request.form.get("user_id")
    role = request.form.get("role")
    new_password = request.form.get("password")

    if not user_id:
        flash("Usuario no válido.", "danger")
        return redirect("/users")

    if new_password:
        hash_pw = generate_password_hash(new_password)
        db.execute("UPDATE users SET role = ?, hash = ? WHERE id = ?", role, hash_pw, user_id)
    else:
        db.execute("UPDATE users SET role = ? WHERE id = ?", role, user_id)

    flash("Datos del usuario actualizados.", "success")
    return redirect("/users")


@app.route("/users/delete", methods=["POST"])
@login_required
@admin_required
def user_delete():
    """Eliminar un usuario"""
    user_id = request.form.get("user_id")

    if user_id == str(session.get("user_id")):
        flash("No puedes eliminar tu propia cuenta mientras estás logueado.", "danger")
        return redirect("/users")

    db.execute("DELETE FROM users WHERE id = ?", user_id)
    flash("Usuario eliminado correctamente.", "info")
    return redirect("/users")



@app.route("/customers/history/<int:customer_id>")
@login_required
def customer_history(customer_id):
    """Muestra el historial detallado de compras fiadas y abonos de un cliente"""
    # 1. Obtener datos del cliente
    customer = db.execute("SELECT * FROM customers WHERE id = ?", customer_id)
    if not customer:
        flash("Cliente no encontrado.", "danger")
        return redirect("/customers")

    customer_info = customer[0]

    # 2. Obtener compras realizadas a crédito por este cliente
    sales = db.execute(
        """SELECT s.id, s.created_at AS timestamp, s.total, u.username AS seller_name
           FROM sales s
           LEFT JOIN users u ON s.user_id = u.id
           WHERE s.customer_id = ? AND s.payment_type = 'credit'
           ORDER BY s.created_at DESC""",
        customer_id
    )

    # 3. Obtener abonos/pagos realizados por este cliente
    payments = db.execute(
        """SELECT p.id, p.created_at AS timestamp, p.amount, p.payment_type, p.notes, u.username AS seller_name
           FROM customer_payments p
           LEFT JOIN users u ON p.user_id = u.id
           WHERE p.customer_id = ?
           ORDER BY p.created_at DESC""",
        customer_id
    )

    return render_template(
        "customer_history.html",
        customer=customer_info,
        sales=sales,
        payments=payments
    )
