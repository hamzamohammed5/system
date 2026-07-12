"""
ui/tabs/orders/_customer_form.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton,
    QTextEdit, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from services.orders.customer_service import CustomerService
from ui.widgets.tables.tables import (
    make_compact_table, make_item, insert_row, ROW_HEIGHT_COMPACT,
)
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE, FS_SM, fs
from ui.constants import (
    CUSTOMER_FORM_MIN_W, CUSTOMER_FORM_MIN_H,
    CUSTOMER_FORM_ROOT_MARGIN, CUSTOMER_FORM_ROOT_SPACING,
    CUSTOMER_FORM_FORM_SPACING, CUSTOMER_FORM_GRP_RADIUS,
    CUSTOMER_FORM_GRP_MARGIN_T, CUSTOMER_FORM_GRP_PAD_TOP,
    CUSTOMER_FORM_GRP_TITLE_PAD, CUSTOMER_FORM_GRP_TITLE_R,
    CUSTOMER_FORM_NOTES_MAX_H, CUSTOMER_FORM_CONTACTS_MAX_H,
    CUSTOMER_FORM_CONTACTS_SPACING, CUSTOMER_FORM_SAVE_BTN_MIN_H,
    CUSTOMER_FORM_HDR_RADIUS, CUSTOMER_FORM_HDR_PAD,
    CONTACT_DLG_MIN_W, CONTACT_DLG_ROOT_MARGIN,
    CONTACT_DLG_ROOT_SPACING, CONTACT_DLG_FORM_SPACING,
    CUSTOMER_FORM_CONTACTS_COL1_W, CUSTOMER_FORM_CONTACTS_COL2_W,
    CUSTOMER_FORM_CONTACTS_COL3_W, CUSTOMER_FORM_CONTACTS_COL4_W,
)


def _group_ss() -> str:
    return f"""
        QGroupBox {{
            font-weight: bold;
            color: {_C['text_sec']};
            border: 1px solid {_C['border']};
            border-radius: {CUSTOMER_FORM_GRP_RADIUS}px;
            margin-top: {CUSTOMER_FORM_GRP_MARGIN_T}px;
            padding-top: {CUSTOMER_FORM_GRP_PAD_TOP}px;
            background: {_C['bg_surface']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            right: {CUSTOMER_FORM_GRP_TITLE_R}px; padding: 0 {CUSTOMER_FORM_GRP_TITLE_PAD}px;
            font-size: {FS_SM}px;
            color: {_C['accent']};
        }}
    """


class _CustomerForm(QDialog, WidgetMixin):
    saved = pyqtSignal(int)

    def __init__(self, conn, customer_id: int = None, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.customer_id = customer_id
        self._contacts   = []
        self._deleted_contact_ids = []
        self._svc        = CustomerService(conn)

        self.setWindowTitle(tr("customer_edit_title") if customer_id else tr("customer_new_title"))
        self.setMinimumWidth(CUSTOMER_FORM_MIN_W)
        self.setMinimumHeight(CUSTOMER_FORM_MIN_H)
        self.setModal(True)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._build()
        self._refresh_style()
        if customer_id:
            self._load()

    def _refresh_style(self, *_):
        from ui.theme import _C as C
        from ui.font import FS_BASE as BASE, FS_SM as SM
        self._grp_ss_cache = f"""
            QGroupBox {{
                font-weight: bold;
                color: {C['text_sec']};
                border: 1px solid {C['border']};
                border-radius: {CUSTOMER_FORM_GRP_RADIUS}px;
                margin-top: {CUSTOMER_FORM_GRP_MARGIN_T}px;
                padding-top: {CUSTOMER_FORM_GRP_PAD_TOP}px;
                background: {C['bg_surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                right: {CUSTOMER_FORM_GRP_TITLE_R}px; padding: 0 {CUSTOMER_FORM_GRP_TITLE_PAD}px;
                font-size: {SM}px;
                color: {C['accent']};
            }}
        """
        if hasattr(self, '_basic_grp'):
            self._basic_grp.setStyleSheet(self._grp_ss_cache)
        if hasattr(self, '_contacts_grp'):
            self._contacts_grp.setStyleSheet(self._grp_ss_cache)
        if hasattr(self, '_hdr_lbl'):
            self._hdr_lbl.setStyleSheet(f"""
                font-size: {fs(BASE, +2)}px; font-weight: bold; color: {C['accent_text']};
                background: {C['accent_light']};
                border-radius: {CUSTOMER_FORM_HDR_RADIUS}px; padding: {CUSTOMER_FORM_HDR_PAD}px;
            """)
        self.setStyleSheet(input_style())

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*CUSTOMER_FORM_ROOT_MARGIN)
        root.setSpacing(CUSTOMER_FORM_ROOT_SPACING)

        self._hdr_lbl = QLabel(tr("customer_edit_title") if self.customer_id else tr("customer_new_title"))
        root.addWidget(self._hdr_lbl)

        self._basic_grp = QGroupBox(tr("customer_basic_section"))
        form = QFormLayout(self._basic_grp)
        form.setSpacing(CUSTOMER_FORM_FORM_SPACING)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = ThemedLineEdit()
        self.inp_name.setPlaceholderText(tr("customer_name_lbl"))
        form.addRow(tr("customer_name_lbl"), self.inp_name)

        self.cmb_type = ThemedComboBox()
        self.cmb_type.addItem(tr("customer_type_individual"), "individual")
        self.cmb_type.addItem(tr("customer_type_company"),    "company")
        form.addRow(tr("customer_type_lbl"), self.cmb_type)

        self.inp_phone = ThemedLineEdit()
        form.addRow(tr("customer_phone_lbl"), self.inp_phone)

        self.inp_phone2 = ThemedLineEdit()
        form.addRow(tr("customer_phone2_lbl"), self.inp_phone2)

        self.inp_email = ThemedLineEdit()
        form.addRow(tr("customer_email_lbl"), self.inp_email)

        self.inp_city = ThemedLineEdit()
        form.addRow(tr("customer_city_lbl"), self.inp_city)

        self.inp_address = ThemedLineEdit()
        form.addRow(tr("customer_address_lbl"), self.inp_address)

        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(CUSTOMER_FORM_NOTES_MAX_H)
        form.addRow(tr("customer_notes_lbl"), self.inp_notes)

        root.addWidget(self._basic_grp)

        self._contacts_grp = QGroupBox(tr("customer_contacts_section"))
        c_lay = QVBoxLayout(self._contacts_grp)
        c_lay.setSpacing(CUSTOMER_FORM_CONTACTS_SPACING)

        self.contacts_table = make_compact_table(
            columns=[
                tr("contact_name_lbl"), tr("contact_role_lbl"),
                tr("contact_phone_lbl"), tr("contact_email_lbl"), tr("contact_notes_lbl"),
            ],
            stretch_col=0,
            col_widths={
                1: CUSTOMER_FORM_CONTACTS_COL1_W,
                2: CUSTOMER_FORM_CONTACTS_COL2_W,
                3: CUSTOMER_FORM_CONTACTS_COL3_W,
                4: CUSTOMER_FORM_CONTACTS_COL4_W,
            },
            max_height=CUSTOMER_FORM_CONTACTS_MAX_H,
        )
        c_lay.addWidget(self.contacts_table)

        c_btn_row = QHBoxLayout()
        btn_add_c = make_btn(tr("contact_add_btn"), "success")
        btn_add_c.clicked.connect(self._add_contact_dialog)
        btn_del_c = make_btn(tr("contact_del_btn"), "danger")
        btn_del_c.clicked.connect(self._del_contact)
        c_btn_row.addWidget(btn_add_c)
        c_btn_row.addWidget(btn_del_c)
        c_btn_row.addStretch()
        c_lay.addLayout(c_btn_row)
        root.addWidget(self._contacts_grp)

        btn_row = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn(tr("customer_save_btn"), "primary")
        btn_save.setMinimumHeight(CUSTOMER_FORM_SAVE_BTN_MIN_H)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save, stretch=1)
        root.addLayout(btn_row)

    def _load(self):
        c = self._svc.get_customer(self.customer_id)
        if not c:
            return
        self.inp_name.setText(c["name"])
        self.inp_phone.setText(c["phone"] or "")
        self.inp_phone2.setText(c["phone2"] or "")
        self.inp_email.setText(c["email"] or "")
        self.inp_city.setText(c["city"] or "")
        self.inp_address.setText(c["address"] or "")
        self.inp_notes.setPlainText(c["notes"] or "")
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == c["customer_type"]:
                self.cmb_type.setCurrentIndex(i)
                break
        self._contacts = list(self._svc.list_contacts(self.customer_id))
        self._refresh_contacts_table()

    def _refresh_contacts_table(self):
        self.contacts_table.setRowCount(0)
        for ct in self._contacts:
            r = insert_row(self.contacts_table, ROW_HEIGHT_COMPACT)
            cid   = ct.get("id")   if isinstance(ct, dict) else ct["id"]
            name  = ct.get("name", "")  if isinstance(ct, dict) else ct["name"]
            role  = ct.get("role",  "") or ""
            phone = ct.get("phone", "") or ""
            email = ct.get("email", "") or ""
            notes = ct.get("notes", "") or ""
            self.contacts_table.setItem(r, 0, make_item(name, user_data=cid))
            self.contacts_table.setItem(r, 1, make_item(role))
            self.contacts_table.setItem(r, 2, make_item(phone))
            self.contacts_table.setItem(r, 3, make_item(email))
            self.contacts_table.setItem(r, 4, make_item(notes))

    def _add_contact_dialog(self):
        dlg = _ContactDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._contacts.append(dlg.get_data())
            self._refresh_contacts_table()

    def _del_contact(self):
        row = self.contacts_table.currentRow()
        if row < 0:
            return
        removed = self._contacts.pop(row)
        cid = removed.get("id") if isinstance(removed, dict) else removed["id"]
        if cid:
            self._deleted_contact_ids.append(cid)
        self._refresh_contacts_table()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("customer_name_warn"))
            self.inp_name.setFocus()
            return

        ctype   = self.cmb_type.currentData()
        phone   = self.inp_phone.text().strip()
        phone2  = self.inp_phone2.text().strip()
        email   = self.inp_email.text().strip()
        city    = self.inp_city.text().strip()
        address = self.inp_address.text().strip()
        notes   = self.inp_notes.toPlainText().strip()

        if self.customer_id:
            self._svc.update(self.customer_id, name=name, customer_type=ctype,
                            phone=phone, phone2=phone2, email=email,
                            address=address, city=city, notes=notes)
            cid = self.customer_id
        else:
            cid = self._svc.add(name=name, customer_type=ctype,
                                  phone=phone, phone2=phone2, email=email,
                                  address=address, city=city, notes=notes)

        # [مفعّل] CustomerService أصبح يوفر الآن
        # add_contact/update_contact/delete_contact — لذا لم يعد هناك
        # حاجة لاستدعاء db.orders.customers_repo مباشرة من الـ UI؛
        # الحفظ يمر بالكامل عبر طبقة الـ service.
        for cid_to_del in self._deleted_contact_ids:
            self._svc.delete_contact(cid_to_del)

        for ct in self._contacts:
            if ct.get("id"):
                self._svc.update_contact(
                    ct["id"], name=ct.get("name", ""),
                    role=ct.get("role", ""), phone=ct.get("phone", ""),
                    email=ct.get("email", ""), notes=ct.get("notes", ""),
                )
            else:
                self._svc.add_contact(
                    cid, name=ct.get("name", ""),
                    role=ct.get("role", ""), phone=ct.get("phone", ""),
                    email=ct.get("email", ""), notes=ct.get("notes", ""),
                )

        self.saved.emit(cid)
        self.accept()


class _ContactDialog(QDialog, WidgetMixin):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("contact_title"))
        self.setMinimumWidth(CONTACT_DLG_MIN_W)
        self.setModal(True)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._build()
        self._refresh_style()
        if data:
            self._load(data)

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style())

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*CONTACT_DLG_ROOT_MARGIN)
        root.setSpacing(CONTACT_DLG_ROOT_SPACING)

        form = QFormLayout()
        form.setSpacing(CONTACT_DLG_FORM_SPACING)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name  = ThemedLineEdit(); form.addRow(tr("contact_name_lbl"),  self.inp_name)
        self.inp_role  = ThemedLineEdit(); form.addRow(tr("contact_role_lbl"),  self.inp_role)
        self.inp_phone = ThemedLineEdit(); form.addRow(tr("contact_phone_lbl"), self.inp_phone)
        self.inp_email = ThemedLineEdit(); form.addRow(tr("contact_email_lbl"), self.inp_email)
        self.inp_notes = ThemedLineEdit(); form.addRow(tr("contact_notes_lbl"), self.inp_notes)
        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = make_btn(tr("contact_ok_btn"), "primary")
        btn_ok.clicked.connect(self._ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok, stretch=1)
        root.addLayout(btn_row)

    def _load(self, data: dict):
        self.inp_name.setText(data.get("name", ""))
        self.inp_role.setText(data.get("role", ""))
        self.inp_phone.setText(data.get("phone", ""))
        self.inp_email.setText(data.get("email", ""))
        self.inp_notes.setText(data.get("notes", ""))

    def _ok(self):
        if not self.inp_name.text().strip():
            QMessageBox.warning(self, tr("warning"), tr("contact_name_warn"))
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "id":    None,
            "name":  self.inp_name.text().strip(),
            "role":  self.inp_role.text().strip(),
            "phone": self.inp_phone.text().strip(),
            "email": self.inp_email.text().strip(),
            "notes": self.inp_notes.text().strip(),
        }
