"""
ui/tabs/orders/_order_form.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QDateEdit,
    QMessageBox, QGroupBox,
    QDoubleSpinBox, QScrollArea, QWidget, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate

from db.orders.customers_repo import fetch_all_customers, search_customers
from db.orders.orders_repo import (
    fetch_order, insert_order, update_order,
    fetch_order_items, insert_order_item,
    update_order_item, delete_order_item,
)
from db.shared.connection import get_connection
from .order_form._item_row_widget  import _ItemRowWidget
from .order_form._products_fetcher import fetch_offers, fetch_offer_lines

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE, FS_SM
from ui.constants import (
    ORDER_FORM_MIN_W, ORDER_FORM_MIN_H,
    ORDER_FORM_ROOT_MARGIN, ORDER_FORM_ROOT_SPACING,
    ORDER_FORM_GRP_SPACING, ORDER_FORM_GRP_MARGIN_TOP, ORDER_FORM_GRP_PAD_TOP,
    ORDER_FORM_GRP_TITLE_PAD_H, ORDER_FORM_DETAILS_SPACING,
    ORDER_FORM_TOOLBAR_SPACING, ORDER_FORM_OFFERS_MIN_H, ORDER_FORM_OFFERS_MIN_W,
    ORDER_FORM_ROWS_SPACING, ORDER_FORM_ROWS_MARGIN,
    ORDER_FORM_TOTAL_BAR_RADIUS, ORDER_FORM_TOTAL_BAR_MARGIN,
    ORDER_FORM_NOTES_MAX_H, ORDER_FORM_NOTES_SPACING,
    ORDER_FORM_SAVE_BTN_MIN_H, ORDER_FORM_CUST_INFO_RADIUS, ORDER_FORM_CUST_INFO_PAD,
    ORDER_FORM_DUE_DATE_DEFAULT, ORDER_FORM_DISCOUNT_MAX, ORDER_FORM_PAID_MAX,
    ORDER_FORM_HDR_RADIUS, ORDER_FORM_HDR_PAD,
)


def _group_ss(accent=None) -> str:
    c = accent or _C['accent']
    return f"""
        QGroupBox {{
            font-weight: bold;
            color: {_C['text_sec']};
            border: 1px solid {_C['border']};
            border-radius: 8px;
            margin-top: {ORDER_FORM_GRP_MARGIN_TOP}px;
            padding-top: {ORDER_FORM_GRP_PAD_TOP}px;
            background: {_C['bg_surface']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            right: 12px;
            padding: 0 {ORDER_FORM_GRP_TITLE_PAD_H}px;
            font-size: {FS_SM}px;
            color: {c};
        }}
    """


def _get_status_options() -> list:
    from .order_detail._status_config import get_status_labels
    labels = get_status_labels()
    return [
        ("pending",     labels["pending"][0]),
        ("confirmed",   labels["confirmed"][0]),
        ("in_progress", labels["in_progress"][0]),
        ("ready",       labels["ready"][0]),
    ]


def _get_priority_options() -> list:
    from .order_detail._status_config import get_priority_labels
    labels = get_priority_labels()
    return [(k, v[0]) for k, v in labels.items()]


def _get_type_options() -> list:
    from .order_detail._status_config import get_type_labels
    labels = get_type_labels()
    return list(labels.items())


class _OrderForm(QDialog):
    saved = pyqtSignal(int)

    def __init__(self, conn, order_id: int = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.order_id   = order_id
        self._customer_id = None
        self._item_rows: list[_ItemRowWidget] = []

        _ItemRowWidget.invalidate_cache()

        self.setWindowTitle(tr("order_edit_title") if order_id else tr("order_new_title"))
        self.setMinimumWidth(ORDER_FORM_MIN_W)
        self.setMinimumHeight(ORDER_FORM_MIN_H)
        self.setModal(True)
        self._build()
        if order_id:
            self._load()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(*ORDER_FORM_ROOT_MARGIN)
        root.setSpacing(ORDER_FORM_ROOT_SPACING)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.setStyleSheet(input_style())

        hdr = QLabel(tr("order_edit_title") if self.order_id else tr("order_new_title"))
        hdr.setStyleSheet(f"""
            font-size: {FS_BASE + 3}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: {ORDER_FORM_HDR_RADIUS}px; padding: {ORDER_FORM_HDR_PAD};
        """)
        root.addWidget(hdr)

        self._build_customer_section(root)
        self._build_order_details(root)
        self._build_items_section(root)
        self._build_notes_section(root)
        self._build_save_buttons(root)

        self._add_item_row()

    def _build_customer_section(self, root):
        cust_grp = QGroupBox(tr("order_customer_section"))
        cust_grp.setStyleSheet(_group_ss(_C['accent']))
        c_lay = QVBoxLayout(cust_grp)
        c_lay.setSpacing(ORDER_FORM_GRP_SPACING)

        search_row = QHBoxLayout()
        self.inp_cust_search = QLineEdit()
        self.inp_cust_search.setPlaceholderText(tr("order_customer_search"))
        self.inp_cust_search.textChanged.connect(self._search_customers)

        btn_new_cust = make_btn(tr("customer_new_btn"), "success")
        btn_new_cust.clicked.connect(self._new_customer)

        search_row.addWidget(self.inp_cust_search, stretch=1)
        search_row.addWidget(btn_new_cust)
        c_lay.addLayout(search_row)

        self.cmb_customer = QComboBox()
        self.cmb_customer.setPlaceholderText(tr("select_field").format(label=tr("customer_name")))
        self._all_customers = fetch_all_customers(self.conn, active_only=True)
        for c in self._all_customers:
            label = f"{c['code']}  {c['name']}  ({c['phone'] or tr('no_data')})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.currentIndexChanged.connect(self._on_customer_changed)
        c_lay.addWidget(self.cmb_customer)

        self._lbl_cust_info = QLabel("")
        self._lbl_cust_info.setStyleSheet(
            f"font-size:{FS_SM}px; color:{_C['text_muted']};"
            f"background:{_C['bg_surface_2']};"
            f"border:1px solid {_C['border']}; border-radius:{ORDER_FORM_CUST_INFO_RADIUS}px;"
            f"padding:{ORDER_FORM_CUST_INFO_PAD[0]}px {ORDER_FORM_CUST_INFO_PAD[1]}px;"
        )
        self._lbl_cust_info.setVisible(False)
        c_lay.addWidget(self._lbl_cust_info)
        root.addWidget(cust_grp)

    def _build_order_details(self, root):
        order_grp = QGroupBox(tr("order_details_section"))
        order_grp.setStyleSheet(_group_ss(_C['accent']))
        form = QFormLayout(order_grp)
        form.setSpacing(ORDER_FORM_DETAILS_SPACING)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_type = QComboBox()
        for k, v in _get_type_options():
            self.cmb_type.addItem(v, k)
        form.addRow(tr("order_type_label"), self.cmb_type)

        self.cmb_status = QComboBox()
        for k, v in _get_status_options():
            self.cmb_status.addItem(v, k)
        if not self.order_id:
            self.cmb_status.setVisible(False)
        form.addRow(tr("order_status_label"), self.cmb_status)

        self.cmb_priority = QComboBox()
        for k, v in _get_priority_options():
            self.cmb_priority.addItem(v, k)
        self.cmb_priority.setCurrentIndex(1)
        form.addRow(tr("order_priority_label"), self.cmb_priority)

        self.inp_due_date = QDateEdit()
        self.inp_due_date.setCalendarPopup(True)
        self.inp_due_date.setDate(QDate.currentDate().addDays(ORDER_FORM_DUE_DATE_DEFAULT))
        self.inp_due_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow(tr("order_due_date_label"), self.inp_due_date)

        self.sp_discount = QDoubleSpinBox()
        self.sp_discount.setRange(0, ORDER_FORM_DISCOUNT_MAX)
        self.sp_discount.setDecimals(2)
        self.sp_discount.setSuffix(f" {tr('currency_sym')}")
        form.addRow(tr("order_discount_total"), self.sp_discount)

        self.sp_paid = QDoubleSpinBox()
        self.sp_paid.setRange(0, ORDER_FORM_PAID_MAX)
        self.sp_paid.setDecimals(2)
        self.sp_paid.setSuffix(f" {tr('currency_sym')}")
        form.addRow(tr("order_paid_amount"), self.sp_paid)
        root.addWidget(order_grp)

    def _build_items_section(self, root):
        items_grp = QGroupBox(tr("order_items_section"))
        items_grp.setStyleSheet(_group_ss(_C['warning']))
        items_lay = QVBoxLayout(items_grp)
        items_lay.setSpacing(ORDER_FORM_GRP_SPACING)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(ORDER_FORM_TOOLBAR_SPACING)

        btn_add_item = make_btn(tr("order_add_item_btn"), "success")
        btn_add_item.clicked.connect(self._add_item_row)

        lbl_offer = QLabel(tr("order_select_offer_lbl"))
        lbl_offer.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")

        self.cmb_offers = QComboBox()
        self.cmb_offers.setMinimumHeight(ORDER_FORM_OFFERS_MIN_H)
        self.cmb_offers.setMinimumWidth(ORDER_FORM_OFFERS_MIN_W)
        self._load_offers_combo()

        btn_import_offer = make_btn(tr("order_import_offer_btn"), "ghost")
        btn_import_offer.clicked.connect(self._import_offer)

        toolbar.addWidget(btn_add_item)
        toolbar.addStretch()
        toolbar.addWidget(lbl_offer)
        toolbar.addWidget(self.cmb_offers, stretch=1)
        toolbar.addWidget(btn_import_offer)
        items_lay.addLayout(toolbar)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(ORDER_FORM_ROWS_SPACING)
        self._rows_layout.setContentsMargins(*ORDER_FORM_ROWS_MARGIN)
        items_lay.addWidget(self._rows_container)

        total_bar = QFrame()
        total_bar.setStyleSheet(f"""
            QFrame {{
                background: {_C['accent_light']};
                border: 1px solid {_C['accent_mid']};
                border-radius: {ORDER_FORM_TOTAL_BAR_RADIUS}px;
            }}
        """)
        total_row = QHBoxLayout(total_bar)
        total_row.setContentsMargins(*ORDER_FORM_TOTAL_BAR_MARGIN)

        lbl_items_count = QLabel(tr("order_items_count_lbl"))
        lbl_items_count.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{FS_SM}px; background:transparent;"
        )
        self.lbl_items_count = QLabel("0")
        self.lbl_items_count.setStyleSheet(
            f"font-weight:bold; color:{_C['accent_text']}; background:transparent;"
        )
        lbl_subtotal_txt = QLabel(tr("order_subtotal_lbl"))
        lbl_subtotal_txt.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{FS_SM}px; background:transparent;"
        )
        self.lbl_subtotal = QLabel(f"0.00 {tr('currency_sym')}")
        self.lbl_subtotal.setStyleSheet(
            f"font-weight:bold; color:{_C['accent_text']}; font-size:{FS_BASE + 1}px; background:transparent;"
        )

        total_row.addWidget(lbl_items_count)
        total_row.addWidget(self.lbl_items_count)
        total_row.addStretch()
        total_row.addWidget(lbl_subtotal_txt)
        total_row.addWidget(self.lbl_subtotal)
        items_lay.addWidget(total_bar)
        root.addWidget(items_grp)

    def _build_notes_section(self, root):
        notes_grp = QGroupBox(tr("order_notes_section"))
        notes_grp.setStyleSheet(_group_ss(_C['text_muted']))
        n_lay = QVBoxLayout(notes_grp)
        n_lay.setSpacing(ORDER_FORM_NOTES_SPACING)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText(tr("order_customer_notes"))
        self.inp_notes.setMaximumHeight(ORDER_FORM_NOTES_MAX_H)
        n_lay.addWidget(QLabel(tr("order_customer_notes")))
        n_lay.addWidget(self.inp_notes)

        self.inp_internal = QTextEdit()
        self.inp_internal.setPlaceholderText(tr("order_internal_notes"))
        self.inp_internal.setMaximumHeight(ORDER_FORM_NOTES_MAX_H)
        n_lay.addWidget(QLabel(tr("order_internal_notes_lbl")))
        n_lay.addWidget(self.inp_internal)
        root.addWidget(notes_grp)

    def _build_save_buttons(self, root):
        btns = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn(tr("order_save_btn"), "primary")
        btn_save.setMinimumHeight(ORDER_FORM_SAVE_BTN_MIN_H)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save, stretch=1)
        root.addLayout(btns)

    def _add_item_row(self, prefill: dict = None) -> _ItemRowWidget:
        row = _ItemRowWidget()
        row.changed.connect(self._update_totals)
        row.removed.connect(self._remove_item_row)
        self._item_rows.append(row)
        self._rows_layout.addWidget(row)
        if prefill:
            row.load_from_order_item(prefill)
        self._update_totals()
        return row

    def _remove_item_row(self, row_widget: _ItemRowWidget):
        if row_widget in self._item_rows:
            self._item_rows.remove(row_widget)
        self._rows_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self._update_totals()

    def _update_totals(self):
        total = sum(r.get_total() for r in self._item_rows)
        valid = sum(1 for r in self._item_rows if r.get_product_name())
        self.lbl_items_count.setText(str(valid))
        self.lbl_subtotal.setText(f"{total:,.2f} {tr('currency_sym')}")

    def _load_offers_combo(self):
        self.cmb_offers.clear()
        self.cmb_offers.addItem(tr("offer_select_label"), None)
        for o in fetch_offers():
            cat = f" [{o['category_name']}]" if o.get("category_name") else ""
            label = f"{tr('order_offer_icon')} {o['name']}  {tr('discount')} {o['discount']:.0f}%{cat}"
            self.cmb_offers.addItem(label, o["id"])

    def _import_offer(self):
        oid = self.cmb_offers.currentData()
        if not oid:
            return
        offer_discount = 0.0
        try:
            conn_erp = get_connection("erp")
            o = conn_erp.execute("SELECT discount FROM offers WHERE id=?", (oid,)).fetchone()
            if o:
                offer_discount = float(o["discount"])
        except Exception:
            pass

        lines = fetch_offer_lines(oid)
        if not lines:
            QMessageBox.information(self, tr("info"), tr("no_data"))
            return

        for r in list(self._item_rows):
            if not r.get_product_name():
                self._remove_item_row(r)

        for line in lines:
            row = self._add_item_row()
            pid = line.get("item_id")
            if pid:
                cmb = row.cmb_product
                for i in range(cmb.count()):
                    if cmb.itemData(i) == pid:
                        cmb.blockSignals(True)
                        cmb.setCurrentIndex(i)
                        cmb.blockSignals(False)
                        for p in _ItemRowWidget._get_products():
                            if p["id"] == pid:
                                row._unit_price = p.get("price") or 0.0
                                row.lbl_price.setText(f"{row._unit_price:.2f} {tr('currency_sym')}")
                                break
                        break
            row.sp_qty.setValue(line["qty"])
            row.set_offer_discount(offer_discount)

        self.cmb_offers.setCurrentIndex(0)

    def _search_customers(self, text: str):
        if len(text) < 2:
            return
        results = search_customers(self.conn, text)
        self.cmb_customer.blockSignals(True)
        self.cmb_customer.clear()
        for c in results:
            label = f"{c['code']}  {c['name']}  ({c['phone'] or tr('no_data')})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.blockSignals(False)
        if results:
            self.cmb_customer.setCurrentIndex(0)
            self._on_customer_changed(0)

    def _on_customer_changed(self, idx: int):
        cid = self.cmb_customer.currentData()
        self._customer_id = cid
        if cid:
            from db.orders.customers_repo import fetch_customer
            c = fetch_customer(self.conn, cid)
            if c:
                parts = []
                if c["phone"]:  parts.append(f"{tr('order_phone_icon')} {c['phone']}")
                if c["city"]:   parts.append(f"{tr('order_city_icon')} {c['city']}")
                if c["email"]:  parts.append(f"{tr('order_email_icon')} {c['email']}")
                self._lbl_cust_info.setText("  |  ".join(parts) if parts else "")
                self._lbl_cust_info.setVisible(bool(parts))
        else:
            self._lbl_cust_info.setVisible(False)

    def _new_customer(self):
        from ui.tabs.orders._customer_form import _CustomerForm
        dlg = _CustomerForm(self.conn, parent=self)
        dlg.saved.connect(self._on_customer_created)
        dlg.exec_()

    def _on_customer_created(self, customer_id: int):
        from db.orders.customers_repo import fetch_customer
        c = fetch_customer(self.conn, customer_id)
        if c:
            label = f"{c['code']}  {c['name']}  ({c['phone'] or tr('no_data')})"
            self.cmb_customer.insertItem(0, label, customer_id)
            self.cmb_customer.setCurrentIndex(0)
            self._customer_id = customer_id

    def _load(self):
        d = fetch_order(self.conn, self.order_id)
        if not d:
            return

        for i in range(self.cmb_customer.count()):
            if self.cmb_customer.itemData(i) == d["customer_id"]:
                self.cmb_customer.setCurrentIndex(i)
                break

        for cmb, key in [(self.cmb_type, "order_type"),
                         (self.cmb_priority, "priority"),
                         (self.cmb_status, "status")]:
            for i in range(cmb.count()):
                if cmb.itemData(i) == d[key]:
                    cmb.setCurrentIndex(i)
                    break

        if d["due_date"]:
            self.inp_due_date.setDate(QDate.fromString(d["due_date"], "yyyy-MM-dd"))
        self.sp_discount.setValue(d["discount"] or 0)
        self.sp_paid.setValue(d["paid_amount"] or 0)
        self.inp_notes.setPlainText(d["notes"] or "")
        self.inp_internal.setPlainText(d["internal_notes"] or "")

        for r in list(self._item_rows):
            self._remove_item_row(r)

        items = fetch_order_items(self.conn, self.order_id)
        for item in items:
            self._add_item_row(prefill=dict(item))

    def _save(self):
        if not self._customer_id:
            QMessageBox.warning(self, tr("warning"), tr("order_no_customer_warn"))
            return

        valid_rows = [r for r in self._item_rows if r.get_product_name()]
        if not valid_rows:
            QMessageBox.warning(self, tr("warning"), tr("order_no_items_warn"))
            return

        priority   = self.cmb_priority.currentData()
        order_type = self.cmb_type.currentData()
        due_date   = self.inp_due_date.date().toString("yyyy-MM-dd")
        discount   = self.sp_discount.value()
        paid       = self.sp_paid.value()
        notes      = self.inp_notes.toPlainText().strip()
        internal   = self.inp_internal.toPlainText().strip()

        if self.order_id:
            update_order(self.conn, self.order_id, priority=priority,
                         due_date=due_date, discount=discount,
                         paid_amount=paid, notes=notes, internal_notes=internal)
            existing = fetch_order_items(self.conn, self.order_id)
            for eid in {i["id"] for i in existing}:
                delete_order_item(self.conn, eid)
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(self.conn, self.order_id,
                                  item_name=d["item_name"], description=d["description"],
                                  quantity=d["quantity"], unit=d["unit"],
                                  unit_price=d["unit_price"], discount_pct=d["discount_pct"],
                                  design_ref=d["design_ref"], notes=d["notes"], sort_order=idx)
            self.saved.emit(self.order_id)
        else:
            oid = insert_order(self.conn, customer_id=self._customer_id,
                               order_type=order_type, priority=priority,
                               due_date=due_date, discount=discount,
                               paid_amount=paid, notes=notes, internal_notes=internal)
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(self.conn, oid,
                                  item_name=d["item_name"], description=d["description"],
                                  quantity=d["quantity"], unit=d["unit"],
                                  unit_price=d["unit_price"], discount_pct=d["discount_pct"],
                                  design_ref=d["design_ref"], notes=d["notes"], sort_order=idx)
            self.saved.emit(oid)

        self.accept()
