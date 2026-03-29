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

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "tajny_klic")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://student11:spsnet@dbs.spskladno.cz:3306/vyuka11"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------------------------------------------------
# PRODUKTY (pro školní projekt)
# - team_key: pro filtr (mancity, realmadrid, ...)
# - type_key: home/away
# - old_price + badge: pro slevu
# ------------------------------------------------------------
PRODUCTS = {
    "1": {
        "id": "1",
        "name": "Manchester City - domaci",
        "team_key": "mancity",
        "type_key": "home",
        "season": "25/26",
        "price": 1799,
        "old_price": 1999,
        "badge": "Sleva",
        "image_file": "mancity_home.png",
        "stock_sizes": ["S", "M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "9", "10", "11", "HAALAND 9", "DE BRUYNE 17"],
    },
    "2": {
        "id": "2",
        "name": "Manchester City - venkovni",
        "team_key": "mancity",
        "type_key": "away",
        "season": "25/26",
        "price": 1699,
        "old_price": None,
        "badge": None,
        "image_file": "mancity_away.png",
        "stock_sizes": ["S", "M", "L"],
        "stock_numbers": ["Bez cisla", "9", "10", "FODEN 47"],
    },
    "3": {
        "id": "3",
        "name": "Real Madrid - domaci",
        "team_key": "realmadrid",
        "type_key": "home",
        "season": "25/26",
        "price": 1899,
        "old_price": 2199,
        "badge": "Sleva",
        "image_file": "realmadrid_home.png",
        "stock_sizes": ["M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "5", "7", "10", "BELLINGHAM 5", "VINICIUS 7"],
    },
    "4": {
        "id": "4",
        "name": "Real Madrid - venkovni",
        "team_key": "realmadrid",
        "type_key": "away",
        "season": "25/26",
        "price": 1799,
        "old_price": None,
        "badge": None,
        "image_file": "realmadrid_away.png",
        "stock_sizes": ["S", "M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "5", "7", "10", "VALVERDE 15"],
    },
    "5": {
        "id": "5",
        "name": "Barcelona - domaci",
        "team_key": "barcelona",
        "type_key": "home",
        "season": "25/26",
        "price": 1699,
        "old_price": 1999,
        "badge": "Sleva",
        "image_file": "barcelona_home.png",
        "stock_sizes": ["S", "M", "L"],
        "stock_numbers": ["Bez cisla", "9", "10", "RAPINHA 19", "LEWANDOWSKI 9"],
    },
    "6": {
        "id": "6",
        "name": "Barcelona - venkovni",
        "team_key": "barcelona",
        "type_key": "away",
        "season": "25/26",
        "price": 1599,
        "old_price": None,
        "badge": None,
        "image_file": "barcelona_away.png",
        "stock_sizes": ["M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "10", "11", "BALDE 19"],
    },
    "7": {
        "id": "7",
        "name": "Bayern Mnichov - domaci",
        "team_key": "bayern",
        "type_key": "home",
        "season": "25/26",
        "price": 1899,
        "old_price": 2099,
        "badge": "Sleva",
        "image_file": "bayern_home.png",
        "stock_sizes": ["S", "M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "9", "10", "KIMMICH 6", "KANE 9"],
    },
    "8": {
        "id": "8",
        "name": "Bayern Mnichov - venkovni",
        "team_key": "bayern",
        "type_key": "away",
        "season": "25/26",
        "price": 1799,
        "old_price": None,
        "badge": None,
        "image_file": "bayern_away.png",
        "stock_sizes": ["S", "M", "L"],
        "stock_numbers": ["Bez cisla", "9", "10", "MUSIALA 42"],
    },
    "9": {
        "id": "9",
        "name": "PSG - domaci",
        "team_key": "psg",
        "type_key": "home",
        "season": "25/26",
        "price": 1899,
        "old_price": 2199,
        "badge": "Sleva",
        "image_file": "psg_home.png",
        "stock_sizes": ["M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "7", "10", "MBAPPE 7"],
    },
    "10": {
        "id": "10",
        "name": "PSG - venkovni",
        "team_key": "psg",
        "type_key": "away",
        "season": "25/26",
        "price": 1799,
        "old_price": None,
        "badge": None,
        "image_file": "psg_away.png",
        "stock_sizes": ["S", "M", "L"],
        "stock_numbers": ["Bez cisla", "7", "10", "DEMBELE 10"],
    },
    "11": {
        "id": "11",
        "name": "Arsenal - domaci",
        "team_key": "arsenal",
        "type_key": "home",
        "season": "25/26",
        "price": 1699,
        "old_price": 1899,
        "badge": "Sleva",
        "image_file": "arsenal_home.png",
        "stock_sizes": ["S", "M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "7", "8", "SAKA 7", "ODEGAARD 8"],
    },
    "12": {
        "id": "12",
        "name": "Arsenal - venkovni",
        "team_key": "arsenal",
        "type_key": "away",
        "season": "25/26",
        "price": 1599,
        "old_price": None,
        "badge": None,
        "image_file": "arsenal_away.png",
        "stock_sizes": ["M", "L"],
        "stock_numbers": ["Bez cisla", "7", "9", "JESUS 9"],
    },
    "13": {
        "id": "13",
        "name": "Juventus - domaci",
        "team_key": "juventus",
        "type_key": "home",
        "season": "25/26",
        "price": 1749,
        "old_price": None,
        "badge": None,
        "image_file": "juventus_home.png",
        "stock_sizes": ["S", "M", "L"],
        "stock_numbers": ["Bez cisla", "7", "10", "CHIESA 7"],
    },
    "14": {
        "id": "14",
        "name": "Juventus - venkovni",
        "team_key": "juventus",
        "type_key": "away",
        "season": "25/26",
        "price": 1649,
        "old_price": 1899,
        "badge": "Sleva",
        "image_file": "juventus_away.png",
        "stock_sizes": ["M", "L", "XL"],
        "stock_numbers": ["Bez cisla", "7", "9", "VLAHOVIC 9"],
    },
}


# -------------------------
# MODELY
# -------------------------

class Product(db.Model):
    __tablename__ = "products123"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    team_key = db.Column(db.String(50))
    type_key = db.Column(db.String(10))
    season = db.Column(db.String(20))
    price = db.Column(db.Integer, nullable=False)
    old_price = db.Column(db.Integer, nullable=True)
    badge = db.Column(db.String(50), nullable=True)
    image_file = db.Column(db.String(100), nullable=True)
    stock_sizes = db.Column(db.String(200))
    stock_numbers = db.Column(db.String(500))

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "team_key": self.team_key or "",
            "type_key": self.type_key or "home",
            "season": self.season or "25/26",
            "price": self.price,
            "old_price": self.old_price,
            "badge": self.badge,
            "image_file": self.image_file,
            "stock_sizes": [s.strip() for s in (self.stock_sizes or "").split(",") if s.strip()],
            "stock_numbers": [n.strip() for n in (self.stock_numbers or "").split(",") if n.strip()],
        }


def _seed_products_if_empty():
    if Product.query.count() == 0:
        for p in PRODUCTS.values():
            db.session.add(Product(
                id=int(p["id"]),
                name=p["name"],
                team_key=p.get("team_key"),
                type_key=p.get("type_key"),
                season=p.get("season", "25/26"),
                price=p["price"],
                old_price=p.get("old_price"),
                badge=p.get("badge"),
                image_file=p.get("image_file"),
                stock_sizes=",".join(p.get("stock_sizes", [])),
                stock_numbers=",".join(p.get("stock_numbers", [])),
            ))
        db.session.commit()


class User(db.Model):
    __tablename__ = "users123"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


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

    shipping = db.Column(db.String(20), nullable=False)
    payment = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255))

    total = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)


class OrderItem(db.Model):
    __tablename__ = "order_items123"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders123.id"), nullable=False)
    order = db.relationship(
        "Order",
        backref=db.backref("items", lazy=True, cascade="all, delete-orphan")
    )

    product_id = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False)


class WheelReward(db.Model):
    __tablename__ = "wheel_rewards123"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users123.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("wheel_rewards", lazy=True))

    percent = db.Column(db.Integer, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)


# -------------------------
# AUTH
# -------------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Nejprve se prihlas.", "error")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


# -------------------------
# CART HELPERS
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


def _real_utcnow() -> datetime:
    """Vrací skutečný UTC čas z internetu (NTP). Pokud selže, použije systémový čas."""
    import socket, struct
    try:
        NTP_SERVER = "pool.ntp.org"
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(3)
        data = b'\x1b' + 47 * b'\0'
        client.sendto(data, (NTP_SERVER, 123))
        data, _ = client.recvfrom(1024)
        client.close()
        if data:
            t = struct.unpack('!12I', data)[10]
            t -= 2208988800  # rozdíl epoch NTP vs Unix
            return datetime.utcfromtimestamp(t)
    except Exception:
        pass
    return datetime.utcnow()


def can_spin(user_id: int):
    last = last_spin_time(user_id)
    if not last:
        return True, None
    next_time = last + timedelta(hours=24)
    now = _real_utcnow()
    return now >= next_time, next_time


# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def index():
    db_products = Product.query.order_by(Product.id).all()
    products_sorted = []
    for prod in db_products:
        p = prod.to_dict()
        p["image_url"] = url_for("static", filename=f"img/{p['image_file']}") if p.get("image_file") else None
        products_sorted.append(p)
    return render_template("index.html", products=products_sorted)


@app.route("/product/<product_id>")
def product_detail(product_id):
    prod = Product.query.get(int(product_id)) if product_id.isdigit() else None
    if not prod:
        abort(404)
    p = prod.to_dict()
    p["image_url"] = url_for("static", filename=f"img/{p['image_file']}") if p.get("image_file") else None
    return render_template("product.html", p=p)


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
            flash("Prihlaseni probehlo uspesne.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("index"))

        error = "Spatne jmeno nebo heslo."
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
            error = "Uzivatelske jmeno musi mit 3-50 znaku a muze obsahovat jen pismena, cisla a . _ -"
        elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            error = "Zadej platny email."
        elif User.query.filter_by(username=username).first():
            error = "Uzivatelske jmeno je jiz obsazeno."
        elif User.query.filter_by(email=email).first():
            error = "Email je jiz pouzit."
        elif password != password2:
            error = "Hesla se neshoduji."
        elif len(password) < 8:
            error = "Heslo musi mit alespon 8 znaku."
        elif not re.search(r"[A-Z]", password):
            error = "Heslo musi obsahovat alespon 1 velke pismeno."
        elif not re.search(r"\d", password):
            error = "Heslo musi obsahovat alespon 1 cislo."

        if error is None:
            try:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()

                session.clear()
                session["user_id"] = new_user.id
                session["username"] = new_user.username
                flash("Ucet byl uspesne vytvoren.", "success")
                return redirect(url_for("index"))
            except Exception:
                db.session.rollback()
                error = "Nastala chyba pri vytvareni uctu."

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("Byl(a) jste odhlaseni.", "info")
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    uid = session["user_id"]
    active = get_active_reward(uid)
    ok, next_time = can_spin(uid)
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
        remaining = int((next_time - _real_utcnow()).total_seconds())
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

    size = request.form.get("size", "").strip()
    number = request.form.get("number", "").strip()

    if not pid or not name or not price_raw:
        abort(400)

    try:
        price = int(price_raw)
    except ValueError:
        abort(400)

    variant_key = f"{pid}|{size}|{number}" if (size or number) else str(pid)

    cart = _get_cart()
    if variant_key in cart["items"]:
        cart["items"][variant_key]["qty"] += 1
    else:
        cart["items"][variant_key] = {
            "id": variant_key,
            "product_id": str(pid),
            "name": name,
            "price": price,
            "qty": 1,
            "size": size,
            "number": number,
        }

    session.modified = True
    flash("Pridano do kosiku.", "success")
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
    flash("Kosik upraven.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    pid = request.form.get("product_id", "").strip()
    cart = _get_cart()
    cart["items"].pop(pid, None)
    session.modified = True
    flash("Polozka odebrana.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/clear")
def cart_clear():
    session.pop("cart", None)
    flash("Kosik vyprazdnen.", "info")
    return redirect(url_for("cart"))


# -------------------------
# CHECKOUT + PAYMENT + ORDERS
# -------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = _get_cart()
    items = list(cart["items"].values())
    base_total = _cart_total()

    if not items:
        flash("Kosik je prazdny.", "error")
        return redirect(url_for("cart"))

    if request.method == "GET":
        active = get_active_reward(session["user_id"])
        return render_template(
            "checkout.html",
            items=items,
            total=base_total,
            active_discount=(active.percent if active else None)
        )

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
        flash("Vypln prosim vsechny povinne udaje.", "error")
        return render_template("checkout.html", items=items, total=base_total)

    active = get_active_reward(session["user_id"])
    discount_percent = active.percent if active else 0
    discount_amount = int(round(base_total * (discount_percent / 100)))
    final_total = max(0, base_total - discount_amount)

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
    db.session.flush()

    for it in items:
        base_pid = it.get("product_id", it.get("id"))
        variant = []
        if it.get("size"):
            variant.append(f"Velikost {it['size']}")
        if it.get("number"):
            variant.append(f"Cislo {it['number']}")
        variant_text = (" - " + " - ".join(variant)) if variant else ""

        db.session.add(OrderItem(
            order_id=o.id,
            product_id=str(base_pid),
            name=f"{it['name']}{variant_text}",
            price=int(it["price"]),
            qty=int(it["qty"]),
        ))

    db.session.commit()

    session["pending_order_id"] = o.id
    session.modified = True
    return redirect(url_for("payment_gateway"))


@app.route("/payment", methods=["GET"])
@login_required
def payment_gateway():
    order_id = session.get("pending_order_id")
    if not order_id:
        flash("Nemas zadnou rozpracovanou objednavku.", "info")
        return redirect(url_for("cart"))

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()
    if not order:
        flash("Objednavka nebyla nalezena.", "error")
        session.pop("pending_order_id", None)
        return redirect(url_for("cart"))

    return render_template("payment.html", order=order)


@app.route("/payment/confirm", methods=["POST"])
@login_required
def payment_confirm():
    order_id = session.get("pending_order_id")
    if not order_id:
        flash("Objednavka uz neni k dispozici.", "error")
        return redirect(url_for("index"))

    card_number = request.form.get("card_number")

    if not card_number or len(card_number.replace(" ", "")) < 16:
        flash("Neplatná karta")
        return redirect(url_for("payment"))

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()
    if not order:
        flash("Objednavka nebyla nalezena.", "error")
        session.pop("pending_order_id", None)
        return redirect(url_for("index"))

    action = request.form.get("action")

    if action == "pay":
        order.status = "paid"
        db.session.commit()

        active = get_active_reward(session["user_id"])
        if active:
            active.used_at = datetime.utcnow()
            db.session.commit()

        session.pop("cart", None)
        session.pop("pending_order_id", None)
        session.modified = True

        flash(f"Platba probehla uspesne. Vas nakup je potvrzen (#{order.order_code}).", "success")
        return redirect(url_for("orders"))

    flash("Platba byla zrusena. Objednavka nebyla dokoncena.", "error")
    return redirect(url_for("checkout"))


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
# ADMIN
# -------------------------
ADMIN_USERNAME = "admin"


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Nejprve se prihlas.", "error")
            return redirect(url_for("login", next=request.path))
        if session.get("username") != ADMIN_USERNAME:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


@app.route("/admin")
@admin_required
def admin_panel():
    products_sorted = [p.to_dict() for p in Product.query.order_by(Product.id).all()]
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin.html", products=products_sorted, orders=all_orders)


@app.route("/admin/product/add", methods=["POST"])
@admin_required
def admin_add_product():
    name = request.form.get("name", "").strip()
    team_key = request.form.get("team_key", "").strip().lower()
    type_key = request.form.get("type_key", "home").strip()
    season = request.form.get("season", "25/26").strip()
    image_file = request.form.get("image_file", "").strip()
    badge = request.form.get("badge", "").strip() or None

    try:
        price = int(request.form.get("price", 0))
    except ValueError:
        flash("Neplatna cena.", "error")
        return redirect(url_for("admin_panel"))

    old_price_raw = request.form.get("old_price", "").strip()
    old_price = int(old_price_raw) if old_price_raw else None

    sizes_raw = request.form.get("sizes", "S, M, L, XL")
    numbers_raw = request.form.get("numbers", "Bez cisla, 9, 10")
    sizes = [s.strip() for s in sizes_raw.split(",") if s.strip()]
    numbers = [n.strip() for n in numbers_raw.split(",") if n.strip()]

    prod = Product(
        name=name, team_key=team_key, type_key=type_key, season=season,
        price=price, old_price=old_price, badge=badge,
        image_file=image_file if image_file else None,
        stock_sizes=",".join(sizes),
        stock_numbers=",".join(numbers),
    )
    db.session.add(prod)
    db.session.commit()

    flash(f"Produkt '{name}' byl pridan (ID {prod.id}).", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/product/edit", methods=["POST"])
@admin_required
def admin_edit_product():
    pid = request.form.get("product_id", "").strip()
    name = request.form.get("name", "").strip()
    badge = request.form.get("badge", "").strip() or None

    try:
        price = int(request.form.get("price", 0))
    except ValueError:
        flash("Neplatna cena.", "error")
        return redirect(url_for("admin_panel"))

    old_price_raw = request.form.get("old_price", "").strip()
    old_price = int(old_price_raw) if old_price_raw else None

    prod = Product.query.get(int(pid))
    if not prod:
        flash("Produkt nenalezen.", "error")
        return redirect(url_for("admin_panel"))
    prod.name = name
    prod.price = price
    prod.old_price = old_price
    prod.badge = badge
    db.session.commit()

    flash(f"Produkt #{pid} '{name}' byl upraven.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/product/delete/<product_id>", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    prod = Product.query.get(int(product_id)) if product_id.isdigit() else None
    if not prod:
        flash("Produkt nenalezen.", "error")
        return redirect(url_for("admin_panel"))
    name = prod.name
    db.session.delete(prod)
    db.session.commit()
    flash(f"Produkt '{name}' byl smazan.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "pending")
    allowed = {"pending", "paid", "shipped", "cancelled"}
    if new_status not in allowed:
        flash("Neplatny status.", "error")
        return redirect(url_for("admin_panel"))
    order.status = new_status
    db.session.commit()
    flash(f"Objednavka #{order.order_code} -> status: {new_status}", "success")
    return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        _seed_products_if_empty()
    app.run(debug=True, use_reloader=False)
