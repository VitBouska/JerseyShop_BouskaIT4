"""
JerseyShop – PyQt5 Admin Aplikace
Připoj se na stejnou MySQL databázi jako Flask app.
Spuštění:  python admin_pyqt.py
Závislosti: pip install PyQt5 pymysql
"""

import sys
from datetime import datetime

try:
    import pymysql
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QTabWidget,
        QVBoxLayout, QHBoxLayout, QGridLayout,
        QTableWidget, QTableWidgetItem, QHeaderView,
        QPushButton, QLabel, QLineEdit, QComboBox,
        QMessageBox, QDialog, QFormLayout, QSpinBox,
        QGroupBox, QSplitter, QFrame, QTextEdit,
        QStatusBar
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QPalette
except ImportError as e:
    print(f"Chybí balíček: {e}")
    print("Spusť: pip install PyQt5 pymysql")
    sys.exit(1)


# ─────────────────────────────────────────
#  KONFIGURACE DATABÁZE  ← uprav dle potřeby
# ─────────────────────────────────────────
DB_CONFIG = {
    "host":   "dbs.spskladno.cz",
    "port":   3306,
    "user":   "student11",
    "password": "spsnet",
    "database": "vyuka11",
    "charset": "utf8mb4",
}

# Názvy tabulek (musí odpovídat app.py)
T_PRODUCTS = "products123"
T_USERS    = "users123"
T_ORDERS   = "orders123"
T_ITEMS    = "order_items123"


# ─────────────────────────────────────────
#  DB HELPER
# ─────────────────────────────────────────
def get_conn():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)


def query(sql, params=None, fetch=True):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


# ─────────────────────────────────────────
#  STYL
# ─────────────────────────────────────────
STYLE = """
QMainWindow, QDialog {
    background: #1e1e2e;
}
QWidget {
    background: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
}
QTabBar::tab {
    background: #313244;
    color: #cdd6f4;
    padding: 8px 20px;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
}
QTabBar::tab:selected {
    background: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}
QTableWidget {
    background: #181825;
    alternate-background-color: #1e1e2e;
    gridline-color: #313244;
    border: 1px solid #313244;
    border-radius: 6px;
}
QTableWidget::item:selected {
    background: #89b4fa;
    color: #1e1e2e;
}
QHeaderView::section {
    background: #313244;
    color: #89b4fa;
    padding: 6px;
    border: none;
    font-weight: bold;
}
QPushButton {
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background: #b4befe;
}
QPushButton:pressed {
    background: #7287fd;
}
QPushButton.danger {
    background: #f38ba8;
}
QPushButton.danger:hover {
    background: #eba0ac;
}
QPushButton.warning {
    background: #fab387;
}
QPushButton.success {
    background: #a6e3a1;
}
QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 6px 10px;
    color: #cdd6f4;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #89b4fa;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
}
QLabel {
    color: #cdd6f4;
}
QStatusBar {
    background: #181825;
    color: #6c7086;
    font-size: 11px;
}
QScrollBar:vertical {
    background: #181825;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
}
"""


# ─────────────────────────────────────────
#  DIALOGY
# ─────────────────────────────────────────
class ProductDialog(QDialog):
    """Přidat / upravit produkt."""

    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Upravit produkt" if product else "Nový produkt")
        self.setMinimumWidth(420)
        self.setStyleSheet(STYLE)
        self._build()
        if product:
            self._fill(product)

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.f_name = QLineEdit()
        self.f_team = QLineEdit()
        self.f_type = QComboBox()
        self.f_type.addItems(["home", "away"])
        self.f_season = QLineEdit("25/26")
        self.f_price = QSpinBox(); self.f_price.setRange(0, 99999); self.f_price.setSuffix(" Kč")
        self.f_old_price = QSpinBox(); self.f_old_price.setRange(0, 99999); self.f_old_price.setSuffix(" Kč")
        self.f_badge = QLineEdit()
        self.f_image = QLineEdit()
        self.f_sizes = QLineEdit()
        self.f_numbers = QLineEdit()

        form.addRow("Název:", self.f_name)
        form.addRow("Tým (key):", self.f_team)
        form.addRow("Typ:", self.f_type)
        form.addRow("Sezóna:", self.f_season)
        form.addRow("Cena:", self.f_price)
        form.addRow("Původní cena:", self.f_old_price)
        form.addRow("Badge:", self.f_badge)
        form.addRow("Obrázek:", self.f_image)
        form.addRow("Velikosti (CSV):", self.f_sizes)
        form.addRow("Čísla (CSV):", self.f_numbers)
        layout.addLayout(form)

        btns = QHBoxLayout()
        save = QPushButton("💾 Uložit")
        save.clicked.connect(self.accept)
        cancel = QPushButton("Zrušit")
        cancel.setStyleSheet("background:#45475a;")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _fill(self, p):
        self.f_name.setText(p.get("name", ""))
        self.f_team.setText(p.get("team_key", ""))
        idx = self.f_type.findText(p.get("type_key", "home"))
        self.f_type.setCurrentIndex(max(0, idx))
        self.f_season.setText(p.get("season", "25/26"))
        self.f_price.setValue(int(p.get("price", 0)))
        self.f_old_price.setValue(int(p.get("old_price") or 0))
        self.f_badge.setText(p.get("badge") or "")
        self.f_image.setText(p.get("image_file") or "")
        self.f_sizes.setText(p.get("stock_sizes") or "")
        self.f_numbers.setText(p.get("stock_numbers") or "")

    def get_data(self):
        return {
            "name":         self.f_name.text().strip(),
            "team_key":     self.f_team.text().strip().lower(),
            "type_key":     self.f_type.currentText(),
            "season":       self.f_season.text().strip(),
            "price":        self.f_price.value(),
            "old_price":    self.f_old_price.value() or None,
            "badge":        self.f_badge.text().strip() or None,
            "image_file":   self.f_image.text().strip() or None,
            "stock_sizes":  self.f_sizes.text().strip(),
            "stock_numbers":self.f_numbers.text().strip(),
        }


class OrderDetailDialog(QDialog):
    """Detail objednávky s položkami."""

    def __init__(self, parent, order_id):
        super().__init__(parent)
        self.setWindowTitle(f"Detail objednávky #{order_id}")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(STYLE)
        self._build(order_id)

    def _build(self, order_id):
        layout = QVBoxLayout(self)

        try:
            orders = query(f"SELECT * FROM {T_ORDERS} WHERE id=%s", (order_id,))
            items  = query(f"SELECT * FROM {T_ITEMS}  WHERE order_id=%s", (order_id,))
        except Exception as e:
            QLabel(f"Chyba: {e}", self)
            return

        if not orders:
            QLabel("Objednávka nenalezena.", self)
            return

        o = orders[0]

        info = QGroupBox("Informace o objednávce")
        grid = QGridLayout(info)
        fields = [
            ("Kód:", o.get("order_code", "")),
            ("Zákazník:", o.get("full_name", "")),
            ("Email:", o.get("email", "")),
            ("Telefon:", o.get("phone") or "—"),
            ("Adresa:", o.get("address", "")),
            ("Platba:", o.get("payment", "")),
            ("Doprava:", o.get("shipping", "")),
            ("Status:", o.get("status", "")),
            ("Celkem:", f"{o.get('total', 0)} Kč"),
            ("Vytvořeno:", str(o.get("created_at", ""))),
            ("Poznámka:", o.get("note") or "—"),
        ]
        for i, (lbl, val) in enumerate(fields):
            grid.addWidget(QLabel(f"<b>{lbl}</b>"), i, 0)
            grid.addWidget(QLabel(str(val)), i, 1)
        layout.addWidget(info)

        items_grp = QGroupBox("Položky")
        vbox = QVBoxLayout(items_grp)
        tbl = QTableWidget(len(items), 4)
        tbl.setHorizontalHeaderLabels(["Název", "Cena", "Qty", "Mezisoučet"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for r, it in enumerate(items):
            tbl.setItem(r, 0, QTableWidgetItem(it.get("name", "")))
            tbl.setItem(r, 1, QTableWidgetItem(f"{it.get('price',0)} Kč"))
            tbl.setItem(r, 2, QTableWidgetItem(str(it.get("qty", 1))))
            tbl.setItem(r, 3, QTableWidgetItem(f"{it.get('price',0)*it.get('qty',1)} Kč"))
        vbox.addWidget(tbl)
        layout.addWidget(items_grp)

        close_btn = QPushButton("Zavřít")
        close_btn.setStyleSheet("background:#45475a;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)


# ─────────────────────────────────────────
#  ZÁLOŽKY
# ─────────────────────────────────────────
class ProductsTab(QWidget):
    status_msg = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Hledat produkt...")
        self.search_box.textChanged.connect(self._filter)
        btn_add = QPushButton("➕ Přidat produkt")
        btn_add.clicked.connect(self._add)
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        btn_refresh.setToolTip("Obnovit")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        # Tabulka
        cols = ["ID", "Název", "Tým", "Typ", "Sezóna", "Cena", "Sleva", "Badge", "Akce"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            self.products = query(f"SELECT * FROM {T_PRODUCTS} ORDER BY id")
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))
            self.products = []
        self._render(self.products)
        self.status_msg.emit(f"Produkty: načteno {len(self.products)} záznamů")

    def _filter(self, text):
        text = text.lower()
        filtered = [p for p in self.products
                    if text in (p.get("name") or "").lower()
                    or text in (p.get("team_key") or "").lower()]
        self._render(filtered)

    def _render(self, data):
        self.table.setRowCount(0)
        for p in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            old = p.get("old_price")
            cells = [
                str(p.get("id", "")),
                p.get("name", ""),
                p.get("team_key", ""),
                p.get("type_key", ""),
                p.get("season", ""),
                f"{p.get('price', 0)} Kč",
                f"{old} Kč" if old else "—",
                p.get("badge") or "—",
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)

            # Akce buňka
            cell = QWidget()
            hbox = QHBoxLayout(cell)
            hbox.setContentsMargins(4, 2, 4, 2)
            hbox.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 28)
            btn_edit.setToolTip("Upravit")
            btn_edit.clicked.connect(lambda _, pid=p["id"]: self._edit(pid))

            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(32, 28)
            btn_del.setToolTip("Smazat")
            btn_del.setStyleSheet("background:#f38ba8; color:#1e1e2e;")
            btn_del.clicked.connect(lambda _, pid=p["id"], nm=p["name"]: self._delete(pid, nm))

            hbox.addWidget(btn_edit)
            hbox.addWidget(btn_del)
            self.table.setCellWidget(r, 8, cell)

        self.table.resizeRowsToContents()

    def _add(self):
        dlg = ProductDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "Chyba", "Název nesmí být prázdný.")
            return
        try:
            query(
                f"""INSERT INTO {T_PRODUCTS}
                    (name,team_key,type_key,season,price,old_price,badge,image_file,stock_sizes,stock_numbers)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (data["name"], data["team_key"], data["type_key"], data["season"],
                 data["price"], data["old_price"], data["badge"], data["image_file"],
                 data["stock_sizes"], data["stock_numbers"]),
                fetch=False
            )
            self.status_msg.emit(f"Produkt '{data['name']}' přidán.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))

    def _edit(self, pid):
        row = next((p for p in self.products if p["id"] == pid), None)
        if not row:
            return
        dlg = ProductDialog(self, row)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        try:
            query(
                f"""UPDATE {T_PRODUCTS}
                    SET name=%s, team_key=%s, type_key=%s, season=%s,
                        price=%s, old_price=%s, badge=%s, image_file=%s,
                        stock_sizes=%s, stock_numbers=%s
                    WHERE id=%s""",
                (data["name"], data["team_key"], data["type_key"], data["season"],
                 data["price"], data["old_price"], data["badge"], data["image_file"],
                 data["stock_sizes"], data["stock_numbers"], pid),
                fetch=False
            )
            self.status_msg.emit(f"Produkt #{pid} upraven.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))

    def _delete(self, pid, name):
        reply = QMessageBox.question(
            self, "Smazat produkt",
            f"Opravdu smazat produkt '{name}' (#{pid})?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            query(f"DELETE FROM {T_PRODUCTS} WHERE id=%s", (pid,), fetch=False)
            self.status_msg.emit(f"Produkt #{pid} '{name}' smazán.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))


class OrdersTab(QWidget):
    status_msg = pyqtSignal(str)

    STATUS_COLORS = {
        "pending":   "#fab387",
        "paid":      "#a6e3a1",
        "shipped":   "#89b4fa",
        "cancelled": "#f38ba8",
    }

    def __init__(self):
        super().__init__()
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Hledat zákazníka / kód...")
        self.search_box.textChanged.connect(self._filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Vše", "pending", "paid", "shipped", "cancelled"])
        self.status_filter.currentTextChanged.connect(self._filter)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(QLabel("Status:"))
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        # Stats řádek
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color:#6c7086; font-size:12px;")
        layout.addWidget(self.stats_label)

        cols = ["ID", "Kód", "Zákazník", "Email", "Celkem", "Platba", "Doprava", "Status", "Vytvořeno", "Akce"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._open_detail)
        layout.addWidget(self.table)

        layout.addWidget(QLabel("💡 Dvojklikem otevřeš detail objednávky", alignment=Qt.AlignRight))

    def refresh(self):
        try:
            self.orders = query(
                f"SELECT * FROM {T_ORDERS} ORDER BY created_at DESC"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))
            self.orders = []
        self._update_stats()
        self._render(self.orders)
        self.status_msg.emit(f"Objednávky: načteno {len(self.orders)} záznamů")

    def _update_stats(self):
        total = sum(o.get("total", 0) for o in self.orders)
        paid  = sum(1 for o in self.orders if o.get("status") == "paid")
        pend  = sum(1 for o in self.orders if o.get("status") == "pending")
        self.stats_label.setText(
            f"Celkový obrat: {total:,} Kč  |  Zaplaceno: {paid}  |  Čekající: {pend}"
        )

    def _filter(self):
        text = self.search_box.text().lower()
        sf   = self.status_filter.currentText()
        filtered = [
            o for o in self.orders
            if (text in (o.get("full_name") or "").lower()
                or text in (o.get("order_code") or "").lower()
                or text in (o.get("email") or "").lower())
            and (sf == "Vše" or o.get("status") == sf)
        ]
        self._render(filtered)

    def _render(self, data):
        self.table.setRowCount(0)
        for o in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            created = o.get("created_at")
            created_str = created.strftime("%d.%m.%Y %H:%M") if hasattr(created, "strftime") else str(created)

            cells = [
                str(o.get("id", "")),
                o.get("order_code", ""),
                o.get("full_name", ""),
                o.get("email", ""),
                f"{o.get('total', 0)} Kč",
                o.get("payment", ""),
                o.get("shipping", ""),
                o.get("status", ""),
                created_str,
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, o.get("id"))
                # Barva statusu
                if c == 7:
                    color = self.STATUS_COLORS.get(val, "#cdd6f4")
                    item.setForeground(QColor(color))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(r, c, item)

            # Akce
            cell = QWidget()
            hbox = QHBoxLayout(cell)
            hbox.setContentsMargins(4, 2, 4, 2)
            hbox.setSpacing(3)

            status_combo = QComboBox()
            status_combo.addItems(["pending", "paid", "shipped", "cancelled"])
            status_combo.setCurrentText(o.get("status", "pending"))
            status_combo.setFixedWidth(100)

            btn_save = QPushButton("💾")
            btn_save.setFixedSize(32, 28)
            btn_save.setToolTip("Uložit status")
            oid = o["id"]
            btn_save.clicked.connect(
                lambda _, oid=oid, cb=status_combo: self._update_status(oid, cb.currentText())
            )

            btn_detail = QPushButton("📋")
            btn_detail.setFixedSize(32, 28)
            btn_detail.setToolTip("Detail")
            btn_detail.setStyleSheet("background:#89dceb; color:#1e1e2e;")
            btn_detail.clicked.connect(lambda _, oid=oid: self._show_detail(oid))

            hbox.addWidget(status_combo)
            hbox.addWidget(btn_save)
            hbox.addWidget(btn_detail)
            self.table.setCellWidget(r, 9, cell)

        self.table.resizeRowsToContents()

    def _update_status(self, order_id, new_status):
        try:
            query(
                f"UPDATE {T_ORDERS} SET status=%s WHERE id=%s",
                (new_status, order_id), fetch=False
            )
            self.status_msg.emit(f"Objednávka #{order_id} → {new_status}")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))

    def _open_detail(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            self._show_detail(int(item.text()))

    def _show_detail(self, order_id):
        dlg = OrderDetailDialog(self, order_id)
        dlg.exec_()


class UsersTab(QWidget):
    status_msg = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Hledat uživatele...")
        self.search_box.textChanged.connect(self._filter)
        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        cols = ["ID", "Uživatelské jméno", "Email", "Počet objednávek", "Akce"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            self.users = query(
                f"""SELECT u.id, u.username, u.email,
                           COUNT(o.id) AS order_count
                    FROM {T_USERS} u
                    LEFT JOIN {T_ORDERS} o ON o.user_id = u.id
                    GROUP BY u.id
                    ORDER BY u.id"""
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))
            self.users = []
        self._render(self.users)
        self.status_msg.emit(f"Uživatelé: načteno {len(self.users)} záznamů")

    def _filter(self, text):
        text = text.lower()
        filtered = [u for u in self.users
                    if text in (u.get("username") or "").lower()
                    or text in (u.get("email") or "").lower()]
        self._render(filtered)

    def _render(self, data):
        self.table.setRowCount(0)
        for u in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            cells = [
                str(u.get("id", "")),
                u.get("username", ""),
                u.get("email", ""),
                str(u.get("order_count", 0)),
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)

            cell = QWidget()
            hbox = QHBoxLayout(cell)
            hbox.setContentsMargins(4, 2, 4, 2)

            btn_del = QPushButton("🗑️ Smazat")
            btn_del.setStyleSheet("background:#f38ba8; color:#1e1e2e;")
            uid = u["id"]
            uname = u.get("username", "")
            btn_del.clicked.connect(lambda _, uid=uid, uname=uname: self._delete(uid, uname))
            hbox.addWidget(btn_del)
            self.table.setCellWidget(r, 4, cell)

        self.table.resizeRowsToContents()

    def _delete(self, uid, uname):
        reply = QMessageBox.question(
            self, "Smazat uživatele",
            f"Opravdu smazat uživatele '{uname}' (#{uid})?\n\nToto smaže i jeho objednávky!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            # Smazat order items → orders → user
            order_ids = query(f"SELECT id FROM {T_ORDERS} WHERE user_id=%s", (uid,))
            for oid in order_ids:
                query(f"DELETE FROM {T_ITEMS} WHERE order_id=%s", (oid["id"],), fetch=False)
            query(f"DELETE FROM {T_ORDERS} WHERE user_id=%s", (uid,), fetch=False)
            query(f"DELETE FROM {T_USERS} WHERE id=%s", (uid,), fetch=False)
            self.status_msg.emit(f"Uživatel '{uname}' smazán.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba DB", str(e))


class StatsTab(QWidget):
    """Přehled statistik."""

    def __init__(self):
        super().__init__()
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)

        btn_refresh = QPushButton("🔄 Obnovit statistiky")
        btn_refresh.setFixedWidth(200)
        btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(btn_refresh, alignment=Qt.AlignLeft)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-family: monospace; font-size: 13px;")
        layout.addWidget(self.text)

    def refresh(self):
        try:
            orders    = query(f"SELECT status, total FROM {T_ORDERS}")
            users     = query(f"SELECT COUNT(*) as cnt FROM {T_USERS}")
            products  = query(f"SELECT COUNT(*) as cnt FROM {T_PRODUCTS}")
            top_items = query(
                f"""SELECT name, SUM(qty) as total_qty, SUM(price*qty) as revenue
                    FROM {T_ITEMS}
                    GROUP BY name
                    ORDER BY total_qty DESC
                    LIMIT 10"""
            )
        except Exception as e:
            self.text.setPlainText(f"Chyba: {e}")
            return

        total_revenue = sum(o["total"] for o in orders)
        paid_revenue  = sum(o["total"] for o in orders if o["status"] == "paid")
        by_status     = {}
        for o in orders:
            by_status[o["status"]] = by_status.get(o["status"], 0) + 1

        lines = [
            "═" * 50,
            "  📊  PŘEHLED OBCHODU",
            "═" * 50,
            "",
            f"  👤 Uživatelů:      {users[0]['cnt']}",
            f"  📦 Produktů:       {products[0]['cnt']}",
            f"  🛒 Objednávek:     {len(orders)}",
            "",
            "  Objednávky podle statusu:",
        ]
        for status, count in sorted(by_status.items()):
            lines.append(f"    • {status:<12} {count}")

        lines += [
            "",
            f"  💰 Celkový obrat:  {total_revenue:,} Kč",
            f"  ✅ Zaplaceno:      {paid_revenue:,} Kč",
            "",
            "─" * 50,
            "  🏆 TOP 10 nejprodávanějších položek:",
            "─" * 50,
        ]
        for i, it in enumerate(top_items, 1):
            lines.append(f"  {i:2}. {it['name'][:35]:<35}  {it['total_qty']} ks  |  {it['revenue']:,} Kč")

        lines += ["", "═" * 50,
                  f"  Aktualizováno: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                  "═" * 50]
        self.text.setPlainText("\n".join(lines))


# ─────────────────────────────────────────
#  HLAVNÍ OKNO
# ─────────────────────────────────────────
class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JerseyShop – Admin Panel")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(STYLE)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Připojeno k databázi.")

        # Centrální widget + tabs
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        self.tab_products = ProductsTab()
        self.tab_orders   = OrdersTab()
        self.tab_users    = UsersTab()
        self.tab_stats    = StatsTab()

        tabs.addTab(self.tab_products, "📦 Produkty")
        tabs.addTab(self.tab_orders,   "🛒 Objednávky")
        tabs.addTab(self.tab_users,    "👤 Uživatelé")
        tabs.addTab(self.tab_stats,    "📊 Statistiky")

        # Propoj status signály
        for tab in (self.tab_products, self.tab_orders, self.tab_users):
            tab.status_msg.connect(self.status_bar.showMessage)

        tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tabs)
        self.tabs = tabs

    def _on_tab_changed(self, idx):
        if idx == 3:  # Statistiky
            self.tab_stats.refresh()


# ─────────────────────────────────────────
#  SPUŠTĚNÍ
# ─────────────────────────────────────────
def main():
    # Test připojení
    try:
        get_conn().close()
    except Exception as e:
        app = QApplication(sys.argv)
        app.setStyleSheet(STYLE)
        msg = QMessageBox()
        msg.setWindowTitle("Chyba připojení")
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"Nelze se připojit k databázi:\n\n{e}\n\nUprav DB_CONFIG v souboru admin_pyqt.py")
        msg.exec_()
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("JerseyShop Admin")
    window = AdminWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
