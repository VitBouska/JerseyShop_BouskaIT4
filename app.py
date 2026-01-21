from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
import os

app = Flask(__name__)

# Doporučení: měj to v env proměnných (na školu může zůstat fallback)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "tajny_klic")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://student11:spsnet@dbs.spskladno.cz:3306/vyuka11"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# MODELY
# -------------------------
class User(db.Model):
    __tablename__ = "users123"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 255 kvůli délce hashů


# -------------------------
# AUTH HELPER
# -------------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Nejprve se přihlas.", "error")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


# -------------------------
# CART HELPERS (session)
# cart = {"items": { "<id>": {"id":..., "name":..., "price":..., "qty":...} } }
# -------------------------
def _get_cart():
    cart = session.get("cart")
    if not cart or "items" not in cart:
        cart = {"items": {}}
        session["cart"] = cart
    return cart


def _cart_count():
    cart = _get_cart()
    return sum(item["qty"] for item in cart["items"].values())


def _cart_total():
    cart = _get_cart()
    return sum(item["price"] * item["qty"] for item in cart["items"].values())


@app.context_processor
def inject_cart():
    # v šablonách můžeš použít {{ cart_count }}
    return {"cart_count": _cart_count()}


# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Přihlášení proběhlo úspěšně.", "success")

            next_url = request.args.get("next")
            return redirect(next_url or url_for("index"))

        error = "Špatné jméno nebo heslo."

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        # Kontroly
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,50}", username):
            error = "Uživatelské jméno musí mít 3–50 znaků a musí obsahovat jen písmena, čísla a . _ -"
        elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            error = "Zadej platný email."
        elif User.query.filter_by(username=username).first():
            error = "Uživatelské jméno je již obsazeno."
        elif User.query.filter_by(email=email).first():
            error = "Email je již použit."
        elif password != password2:
            error = "Hesla se neshodují."
        elif len(password) < 8:
            error = "Heslo musí mít alespoň 8 znaků."
        elif not re.search(r"[A-Z]", password):
            error = "Heslo musí obsahovat alespoň 1 velké písmeno."
        elif not re.search(r"\d", password):
            error = "Heslo musí obsahovat alespoň 1 číslo."

        if error is None:
            try:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()

                session.clear()
                session["user_id"] = new_user.id
                session["username"] = new_user.username
                flash("Účet byl úspěšně vytvořen.", "success")
                return redirect(url_for("index"))

            except Exception:
                db.session.rollback()
                error = "Nastala chyba při vytváření účtu."

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("Byl(a) jste odhlášen(a).", "info")
    return redirect(url_for("index"))

# -------------------------
# PROFIL
# -------------------------

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Nejprve se přihlas.", "error")
        return redirect(url_for("login"))

    # volitelně: můžeš si načíst data z DB (zatím stačí session)
    user = {
        "id": session.get("user_id"),
        "username": session.get("username"),
    }
    return render_template("profile.html", user=user)


# -------------------------
# CART ROUTES
# -------------------------
@app.route("/cart")
def cart():
    cart = _get_cart()
    items = list(cart["items"].values())
    total = _cart_total()
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add", methods=["POST"])
def cart_add():
    pid = request.form.get("product_id", "").strip()
    name = request.form.get("name", "").strip()
    price_raw = request.form.get("price", "").strip()

    if not pid or not name or not price_raw:
        abort(400)

    try:
        price = int(price_raw)
    except ValueError:
        abort(400)

    cart = _get_cart()
    key = str(pid)

    if key in cart["items"]:
        cart["items"][key]["qty"] += 1
    else:
        cart["items"][key] = {"id": key, "name": name, "price": price, "qty": 1}

    session.modified = True
    flash("Přidáno do košíku.", "success")
    return redirect(url_for("cart"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    pid = request.form.get("product_id", "").strip()
    qty_raw = request.form.get("qty", "").strip()

    cart = _get_cart()
    if pid not in cart["items"]:
        return redirect(url_for("cart"))

    try:
        qty = int(qty_raw)
    except ValueError:
        qty = cart["items"][pid]["qty"]

    if qty <= 0:
        cart["items"].pop(pid, None)
    else:
        cart["items"][pid]["qty"] = qty

    session.modified = True
    flash("Košík upraven.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    pid = request.form.get("product_id", "").strip()
    cart = _get_cart()
    cart["items"].pop(pid, None)
    session.modified = True
    flash("Položka odebrána.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/clear")
def cart_clear():
    session.pop("cart", None)
    flash("Košík vyprázdněn.", "info")
    return redirect(url_for("cart"))


# -------------------------
# CHECKOUT
# -------------------------

import uuid
from datetime import datetime

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = _get_cart()
    items = list(cart["items"].values())
    total = _cart_total()

    if not items:
        flash("Košík je prázdný.", "error")
        return redirect(url_for("cart"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        street = request.form.get("street", "").strip()
        city = request.form.get("city", "").strip()
        zip_code = request.form.get("zip_code", "").strip()
        shipping = request.form.get("shipping", "").strip()
        payment = request.form.get("payment", "").strip()
        note = request.form.get("note", "").strip()

        error = None
        if len(full_name) < 3:
            error = "Zadej jméno a příjmení."
        elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            error = "Zadej platný email."
        elif len(street) < 3 or len(city) < 2 or len(zip_code) < 4:
            error = "Zadej kompletní adresu (ulice, město, PSČ)."
        elif shipping not in ("pickup", "courier"):
            error = "Vyber dopravu."
        elif payment not in ("card", "cod", "bank"):
            error = "Vyber platbu."

        if error:
            flash(error, "error")
            return render_template("checkout.html", items=items, total=total)

        # Vytvoříme "čekající objednávku" do session
        order_id = "ORD-" + uuid.uuid4().hex[:8].upper()
        session["pending_order"] = {
            "order_id": order_id,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": f"{street}, {zip_code} {city}",
            "shipping": shipping,
            "payment": payment,
            "note": note,
            "items": items,
            "total": total
        }
        session.modified = True

        # Přesměrování na fake bránu
        return redirect(url_for("payment_gateway"))

    return render_template("checkout.html", items=items, total=total)


# -------------------------
# FAKE PLATEBNI BRANA
# -------------------------


@app.route("/payment", methods=["GET"])
def payment_gateway():
    order = session.get("pending_order")
    if not order:
        flash("Nemáš žádnou rozpracovanou objednávku.", "info")
        return redirect(url_for("cart"))
    return render_template("payment.html", order=order)


@app.route("/payment/confirm", methods=["POST"])
def payment_confirm():
    order = session.get("pending_order")
    if not order:
        flash("Objednávka už není k dispozici.", "error")
        return redirect(url_for("index"))

    action = request.form.get("action")

    if action == "pay":
        # ✅ uložit do historie objednávek (v session)
        orders = session.get("orders", [])
        confirmed = dict(order)  # kopie, ať se to nerozbije po popu pending_order
        confirmed["status"] = "paid"
        orders.insert(0, confirmed)  # nejnovější nahoře
        session["orders"] = orders

        # ✅ potvrzení nákupu
        session.pop("cart", None)
        session.pop("pending_order", None)
        session.modified = True

        flash(f"Platba proběhla úspěšně. Váš nákup je potvrzen (#{order['order_id']}).", "success")
        return redirect(url_for("orders"))

    # ❌ "Platba zrušena"
    flash("Platba byla zrušena. Objednávka nebyla dokončena.", "error")
    return redirect(url_for("checkout"))

@app.route("/orders")
@login_required
def orders():
    orders_list = session.get("orders", [])
    return render_template("orders.html", orders=orders_list)


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)