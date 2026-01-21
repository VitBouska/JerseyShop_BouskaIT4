from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import re
import os
import uuid
import random

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


class Order(db.Model):
    __tablename__ = "orders123"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users123.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("orders", lazy=True))

    order_code = db.Column(db.String(32), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255), nullable=False)

    shipping = db.Column(db.String(20), nullable=False)  # pickup/courier
    payment = db.Column(db.String(20), nullable=False)   # card/bank/cod
    note = db.Column(db.String(255))

    total = db.Column(db.Integer, nullable=False)  # už po slevě (pokud byla)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending/paid/canceled


class OrderItem(db.Model):
    __tablename__ = "order_items123"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders123.id"), nullable=False)
    order = db.relationship(
        "Order",
        backref=db.backref("items", lazy=True, cascade="all, delete-orphan")
    )

    product_id = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False)


# Kolo štěstí: uložené slevy
class WheelReward(db.Model):
    __tablename__ = "wheel_rewards123"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users123.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("wheel_rewards", lazy=True))

    percent = db.Column(db.Integer, nullable=False)  # 0–20
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)  # použito při úspěšné platbě


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
    return {"cart_count": _cart_count()}


# -------------------------
# WHEEL HELPERS
# -------------------------
def get_active_reward(user_id: int):
    return (WheelReward.query
            .filter_by(user_id=user_id, used_at=None)
            .order_by(WheelReward.issued_at.desc())
            .first())


def last_spin_time(user_id: int):
    last = (WheelReward.query
            .filter_by(user_id=user_id)
            .order_by(WheelReward.issued_at.desc())
            .first())
    return last.issued_at if last else None


def can_spin(user_id: int):
    last = last_spin_time(user_id)
    if not last:
        return True, None
    next_time = last + timedelta(hours=24)
    return datetime.utcnow() >= next_time, next_time


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

        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,50}", username):
            error = "Uživatelské jméno musí mít 3–50 znaků a může obsahovat jen písmena, čísla a . _ -"
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
# PROFIL + KOLO ŠTĚSTÍ
# -------------------------
@app.route("/profile")
@login_required
def profile():
    uid = session["user_id"]
    active = get_active_reward(uid)

    ok, next_time = can_spin(uid)
    # pokud má aktivní slevu, nedovolíme další točení (aby neměl 10 aktivních slev)
    can_spin_now = ok and (active is None)

    user = {"id": uid, "username": session.get("username")}
    return render_template(
        "profile.html",
        user=user,
        active_discount=(active.percent if active else None),
        can_spin=can_spin_now,
        next_spin_time=(next_time.isoformat() if next_time else None)
    )


@app.route("/wheel/spin", methods=["POST"])
@login_required
def wheel_spin():
    uid = session["user_id"]

    ok, next_time = can_spin(uid)
    if not ok:
        remaining = int((next_time - datetime.utcnow()).total_seconds())
        return jsonify({"ok": False, "error": "wait", "remaining": max(0, remaining)}), 429

    active = get_active_reward(uid)
    if active:
        return jsonify({"ok": False, "error": "active_discount", "percent": active.percent}), 400

    percent = random.randint(0, 20)

    r = WheelReward(user_id=uid, percent=percent)
    db.session.add(r)
    db.session.commit()

    return jsonify({"ok": True, "percent": percent})


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
# CHECKOUT (DB objednávka + automatická sleva)
# -------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = _get_cart()
    items = list(cart["items"].values())
    base_total = _cart_total()

    if not items:
        flash("Košík je prázdný.", "error")
        return redirect(url_for("cart"))

    if request.method == "GET":
        # tady můžeš případně do šablony poslat info o aktivní slevě
        active = get_active_reward(session["user_id"])
        return render_template("checkout.html", items=items, total=base_total, active_discount=(active.percent if active else None))

    # POST – načteme data z formuláře
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    street = request.form.get("street", "").strip()
    city = request.form.get("city", "").strip()
    zip_code = request.form.get("zip_code", "").strip()

    shipping = request.form.get("shipping", "").strip()
    payment = request.form.get("payment", "").strip()
    note = request.form.get("note", "").strip()

    if not full_name or not email or not street or not city or not zip_code or not shipping or not payment:
        flash("Vyplň prosím všechny povinné údaje.", "error")
        return render_template("checkout.html", items=items, total=base_total)

    # --- Sleva z kola (pokud existuje) ---
    active = get_active_reward(session["user_id"])
    discount_percent = active.percent if active else 0
    discount_amount = int(round(base_total * (discount_percent / 100)))
    final_total = max(0, base_total - discount_amount)

    if discount_percent > 0:
        flash(f"Používá se sleva z kola: {discount_percent}% (-{discount_amount} Kč)", "success")

    # vytvoření objednávky v DB (pending)
    order_code = "ORD-" + uuid.uuid4().hex[:8].upper()

    o = Order(
        user_id=session["user_id"],
        order_code=order_code,
        full_name=full_name,
        email=email,
        phone=phone or None,
        address=f"{street}, {zip_code} {city}",
        shipping=shipping,
        payment=payment,
        note=note or None,
        total=final_total,
        status="pending",
    )
    db.session.add(o)
    db.session.flush()  # získáme o.id

    for it in items:
        db.session.add(OrderItem(
            order_id=o.id,
            product_id=str(it["id"]),
            name=it["name"],
            price=int(it["price"]),
            qty=int(it["qty"]),
        ))

    db.session.commit()

    session["pending_order_id"] = o.id
    session.modified = True

    return redirect(url_for("payment_gateway"))


# -------------------------
# FAKE PLATEBNÍ BRÁNA
# -------------------------
@app.route("/payment", methods=["GET"])
@login_required
def payment_gateway():
    order_id = session.get("pending_order_id")
    if not order_id:
        flash("Nemáš žádnou rozpracovanou objednávku.", "info")
        return redirect(url_for("cart"))

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()
    if not order:
        flash("Objednávka nebyla nalezena.", "error")
        session.pop("pending_order_id", None)
        return redirect(url_for("cart"))

    return render_template("payment.html", order=order)


@app.route("/payment/confirm", methods=["POST"])
@login_required
def payment_confirm():
    order_id = session.get("pending_order_id")
    if not order_id:
        flash("Objednávka už není k dispozici.", "error")
        return redirect(url_for("index"))

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()
    if not order:
        flash("Objednávka nebyla nalezena.", "error")
        session.pop("pending_order_id", None)
        return redirect(url_for("index"))

    action = request.form.get("action")

    if action == "pay":
        order.status = "paid"
        db.session.commit()

        # „spálit“ aktivní slevu z kola (označit used_at)
        active = get_active_reward(session["user_id"])
        if active:
            active.used_at = datetime.utcnow()
            db.session.commit()

        session.pop("cart", None)
        session.pop("pending_order_id", None)
        session.modified = True

        flash(f"Platba proběhla úspěšně. Váš nákup je potvrzen (#{order.order_code}).", "success")
        return redirect(url_for("orders"))

    flash("Platba byla zrušena. Objednávka nebyla dokončena.", "error")
    return redirect(url_for("checkout"))


# -------------------------
# PŘEHLED OBJEDNÁVEK (DB)
# -------------------------
@app.route("/orders")
@login_required
def orders():
    orders_list = (
        Order.query
        .filter_by(user_id=session["user_id"])
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders.html", orders=orders_list)


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)