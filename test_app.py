"""
Testy pro JerseyShop – školní projekt
Spuštění: pytest test_app.py -v
"""

import pytest
import sys
import os

# Přidej cestu k projektu
sys.path.insert(0, os.path.dirname(__file__))

from app import app as flask_app, PRODUCTS


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def app():
    """Vytvoří testovací instanci aplikace s in-memory SQLite databází."""
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["SECRET_KEY"] = "test_klic"
    flask_app.config["WTF_CSRF_ENABLED"] = False

    from app import db, _seed_products_if_empty
    with flask_app.app_context():
        db.create_all()
        _seed_products_if_empty()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    """HTTP testovací klient."""
    return app.test_client()


# -------------------------
# 1. Testy dat produktů (PRODUCTS slovník)
# -------------------------

class TestProductData:
    """Ověřuje správnost dat produktů."""

    def test_products_not_empty(self):
        """Produkty nejsou prázdné."""
        assert len(PRODUCTS) > 0

    def test_all_products_have_required_fields(self):
        """Každý produkt má povinné klíče."""
        required = {"id", "name", "team_key", "type_key", "price", "image_file", "stock_sizes"}
        for pid, product in PRODUCTS.items():
            missing = required - set(product.keys())
            assert not missing, f"Produkt {pid} nemá pole: {missing}"

    def test_all_prices_are_positive(self):
        """Všechny ceny jsou kladná celá čísla."""
        for pid, product in PRODUCTS.items():
            assert isinstance(product["price"], int), f"Cena produktu {pid} není int"
            assert product["price"] > 0, f"Cena produktu {pid} musí být kladná"

    def test_old_price_is_higher_than_price(self):
        """Pokud existuje stará cena, musí být vyšší než aktuální."""
        for pid, product in PRODUCTS.items():
            if product.get("old_price"):
                assert product["old_price"] > product["price"], (
                    f"Produkt {pid}: old_price ({product['old_price']}) "
                    f"musí být > price ({product['price']})"
                )

    def test_type_key_is_valid(self):
        """type_key musí být 'home' nebo 'away'."""
        for pid, product in PRODUCTS.items():
            assert product["type_key"] in ("home", "away"), (
                f"Produkt {pid} má neplatný type_key: {product['type_key']}"
            )

    def test_stock_sizes_not_empty(self):
        """Každý produkt má alespoň jednu velikost."""
        for pid, product in PRODUCTS.items():
            assert len(product["stock_sizes"]) > 0, (
                f"Produkt {pid} nemá žádné velikosti"
            )

    def test_each_team_has_home_and_away(self):
        """Každý klub má domácí i venkovní dres."""
        teams = {}
        for product in PRODUCTS.values():
            team = product["team_key"]
            type_ = product["type_key"]
            teams.setdefault(team, set()).add(type_)

        for team, types in teams.items():
            assert "home" in types, f"{team} nemá domácí dres"
            assert "away" in types, f"{team} nemá venkovní dres"

    def test_image_file_has_extension(self):
        """image_file má příponu .png nebo .jpg."""
        for pid, product in PRODUCTS.items():
            img = product.get("image_file", "")
            assert img.endswith((".png", ".jpg", ".jpeg")), (
                f"Produkt {pid} má neplatný soubor obrázku: {img}"
            )


# -------------------------
# 2. Testy logiky filtrování
# -------------------------

class TestFilterLogic:
    """Testuje filtrování produktů – stejnou logiku jako JS v index.html."""

    def _filter(self, products, team=None, type_=None, min_price=None, max_price=None, text=None):
        """Python ekvivalent JS filter funkce."""
        result = []
        for p in products.values():
            if team and p["team_key"] != team:
                continue
            if type_ and p["type_key"] != type_:
                continue
            if min_price is not None and p["price"] < min_price:
                continue
            if max_price is not None and p["price"] > max_price:
                continue
            if text and text.lower() not in p["name"].lower():
                continue
            result.append(p)
        return result

    def test_filter_by_team(self):
        """Filtr podle klubu vrátí jen produkty daného klubu."""
        results = self._filter(PRODUCTS, team="arsenal")
        assert len(results) > 0
        for p in results:
            assert p["team_key"] == "arsenal"

    def test_filter_by_type_home(self):
        """Filtr 'home' vrátí jen domácí dresy."""
        results = self._filter(PRODUCTS, type_="home")
        for p in results:
            assert p["type_key"] == "home"

    def test_filter_by_type_away(self):
        """Filtr 'away' vrátí jen venkovní dresy."""
        results = self._filter(PRODUCTS, type_="away")
        for p in results:
            assert p["type_key"] == "away"

    def test_filter_by_min_price(self):
        """Min cena funguje správně."""
        min_p = 1800
        results = self._filter(PRODUCTS, min_price=min_p)
        for p in results:
            assert p["price"] >= min_p

    def test_filter_by_max_price(self):
        """Max cena funguje správně."""
        max_p = 1700
        results = self._filter(PRODUCTS, max_price=max_p)
        for p in results:
            assert p["price"] <= max_p

    def test_filter_price_range(self):
        """Filtr rozsahu cen vrátí jen produkty v rozsahu."""
        results = self._filter(PRODUCTS, min_price=1600, max_price=1800)
        for p in results:
            assert 1600 <= p["price"] <= 1800

    def test_filter_impossible_range_returns_empty(self):
        """Nesmyslný rozsah cen vrátí prázdný seznam."""
        results = self._filter(PRODUCTS, min_price=9999, max_price=10000)
        assert results == []

    def test_filter_by_text(self):
        """Textové vyhledávání funguje case-insensitive."""
        results = self._filter(PRODUCTS, text="real madrid")
        assert len(results) > 0
        for p in results:
            assert "real madrid" in p["name"].lower()

    def test_filter_combined_team_and_type(self):
        """Kombinovaný filtr klub + typ."""
        results = self._filter(PRODUCTS, team="barcelona", type_="home")
        assert len(results) == 1
        assert results[0]["team_key"] == "barcelona"
        assert results[0]["type_key"] == "home"

    def test_no_filter_returns_all(self):
        """Bez filtru vrátí všechny produkty."""
        results = self._filter(PRODUCTS)
        assert len(results) == len(PRODUCTS)

    def test_filter_nonexistent_team_returns_empty(self):
        """Filtr neexistujícího klubu vrátí prázdný seznam."""
        results = self._filter(PRODUCTS, team="chelsea")
        assert results == []