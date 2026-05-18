"""
ui/tabs/orders/_customer_form.py
=================================
Dialog لإنشاء عميل جديد أو تعديل عميل موجود.

✅ يستخدم make_compact_table من table_utils
✅ الجداول Fixed — لا تتمدد
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QGroupBox,
    QMessageBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.customers_repo import (
    fetch_customer, insert_customer, update_customer,
    fetch_contacts, insert_contact, update_contact, delete_contact,
)
from ui.widgets.shared.table_utils import (
    make_compact_table, make_table_item, insert_row, ROW_HEIGHT_COMPACT,
)


def _input_ss():
    return """
        QLineEdit, QTextEdit, QComboBox {
            background: #f8f9fb;
            border: 1px solid #cdd3e0;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            color: #1a2035;
            min-height: 34px;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #1565c0;
            background: white;
        }
        QComboBox::drop-down { border: none; width: 20px; }
    """


def _group_ss():
    return """
        QGroupBox {
            font-weight: bold;
            color: #374151;
            border: 1px solid #e5e9f0;
            border-radius: 8px;
            margin-top: 8px;
            padding-top: 8px;
            background: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            right: 12px; padding: 0 4px;
            font-size: 11px;
        }
    """


class _CustomerForm(QDialog):
    saved = pyqtSignal(int)   # customer_id

    def __init__(self, conn, customer_id: int = None, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.customer_id = customer_id
        self._contacts   = []

        title = "تعديل بيانات العميل" if customer_id else "عميل جديد"
        self.setWindowTitle(title)
        self.setMinimumWidth(580)
        self.setMinimumHeight(620)
        self.setModal(True)
        self.setStyleSheet("QDialog { background: #f8f9fb; }")

        self._build()
        if customer_id:
            self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        hdr = QLabel(
            "✏️  تعديل بيانات العميل" if self.customer_id else "👤  عميل جديد"
        )
        hdr.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #1565c0;
            background: #e8f0fe; border-radius: 8px; padding: 8px 14px;
        """)
        root.addWidget(hdr)

        self.setStyleSheet(self.styleSheet() + _input_ss())

        # ══ بيانات العميل الأساسية ══
        basic_grp = QGroupBox("البيانات الأساسية")
        basic_grp.setStyleSheet(_group_ss())
        form = QFormLayout(basic_grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم العميل أو الشركة...")
        form.addRow("الاسم * :", self.inp_name)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("فرد", "individual")
        self.cmb_type.addItem("شركة", "company")
        form.addRow("النوع :", self.cmb_type)

        self.inp_phone = QLineEdit()
        self.inp_phone.setPlaceholderText("رقم الهاتف الأساسي...")
        form.addRow("الهاتف :", self.inp_phone)

        self.inp_phone2 = QLineEdit()
        self.inp_phone2.setPlaceholderText("رقم هاتف بديل (اختياري)...")
        form.addRow("هاتف 2 :", self.inp_phone2)

        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("البريد الإلكتروني...")
        form.addRow("الإيميل :", self.inp_email)

        self.inp_city = QLineEdit()
        self.inp_city.setPlaceholderText("المدينة...")
        form.addRow("المدينة :", self.inp_city)

        self.inp_address = QLineEdit()
        self.inp_address.setPlaceholderText("العنوان التفصيلي...")
        form.addRow("العنوان :", self.inp_address)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText("ملاحظات عن العميل...")
        self.inp_notes.setMaximumHeight(70)
        form.addRow("ملاحظات :", self.inp_notes)

        root.addWidget(basic_grp)

        # ══ جهات الاتصال الإضافية ══
        contacts_grp = QGroupBox("جهات الاتصال الإضافية")
        contacts_grp.setStyleSheet(_group_ss())
        c_lay = QVBoxLayout(contacts_grp)
        c_lay.setSpacing(8)

        # ✅ استخدام make_compact_table من shared
        self.contacts_table = make_compact_table(
            columns=["الاسم", "الصفة", "الهاتف", "الإيميل", "ملاحظات"],
            stretch_col=0,
            col_widths={1: 80, 2: 100, 3: 120, 4: 120},
            max_height=150,
        )
        c_lay.addWidget(self.contacts_table)

        c_btn_row = QHBoxLayout()
        btn_add_c = QPushButton("➕  إضافة جهة اتصال")
        btn_add_c.setMinimumHeight(28)
        btn_add_c.setStyleSheet("""
            QPushButton {
                background: #ecfdf5; color: #065f46;
                border: 1px solid #a7f3d0; border-radius: 5px;
                padding: 0 10px; font-size: 11px;
            }
            QPushButton:hover { background: #d1fae5; }
        """)
        btn_add_c.clicked.connect(self._add_contact_dialog)

        btn_del_c = QPushButton("🗑️  حذف")
        btn_del_c.setMinimumHeight(28)
        btn_del_c.setStyleSheet("""
            QPushButton {
                background: #fef2f2; color: #dc2626;
                border: 1px solid #fecaca; border-radius: 5px;
                padding: 0 10px; font-size: 11px;
            }
            QPushButton:hover { background: #fee2e2; }
        """)
        btn_del_c.clicked.connect(self._del_contact)

        c_btn_row.addWidget(btn_add_c)
        c_btn_row.addWidget(btn_del_c)
        c_btn_row.addStretch()
        c_lay.addLayout(c_btn_row)

        root.addWidget(contacts_grp)

        # ══ أزرار ══
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: white; color: #374151;
                border: 1px solid #cdd3e0; border-radius: 7px;
                padding: 0 16px; font-size: 12px;
            }
            QPushButton:hover { background: #f8f9fb; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾  حفظ")
        btn_save.setMinimumHeight(38)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 7px;
                padding: 0 22px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_save.clicked.connect(self._save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save, stretch=1)
        root.addLayout(btn_row)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        c = fetch_customer(self.conn, self.customer_id)
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

        self._contacts = list(fetch_contacts(self.conn, self.customer_id))
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

            from ui.widgets.shared.table_utils import make_table_item
            item0 = make_table_item(name, user_data=cid)
            self.contacts_table.setItem(r, 0, item0)
            self.contacts_table.setItem(r, 1, make_table_item(role))
            self.contacts_table.setItem(r, 2, make_table_item(phone))
            self.contacts_table.setItem(r, 3, make_table_item(email))
            self.contacts_table.setItem(r, 4, make_table_item(notes))

    # ══════════════════════════════════════════════════════
    # جهات الاتصال
    # ══════════════════════════════════════════════════════

    def _add_contact_dialog(self):
        dlg = _ContactDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            self._contacts.append(data)
            self._refresh_contacts_table()

    def _del_contact(self):
        row = self.contacts_table.currentRow()
        if row < 0:
            return
        self._contacts.pop(row)
        self._refresh_contacts_table()

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العميل")
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
            update_customer(
                self.conn, self.customer_id,
                name=name, customer_type=ctype,
                phone=phone, phone2=phone2,
                email=email, address=address,
                city=city, notes=notes,
            )
            cid = self.customer_id
        else:
            cid = insert_customer(
                self.conn,
                name=name, customer_type=ctype,
                phone=phone, phone2=phone2,
                email=email, address=address,
                city=city, notes=notes,
            )

        for ct in self._contacts:
            if not ct.get("id"):
                insert_contact(
                    self.conn, cid,
                    name=ct.get("name", ""),
                    role=ct.get("role", ""),
                    phone=ct.get("phone", ""),
                    email=ct.get("email", ""),
                    notes=ct.get("notes", ""),
                )

        self.saved.emit(cid)
        self.accept()


# ══════════════════════════════════════════════════════════
# Dialog إضافة جهة اتصال
# ══════════════════════════════════════════════════════════

class _ContactDialog(QDialog):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("جهة اتصال")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build()
        if data:
            self._load(data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم جهة الاتصال...")
        self.inp_name.setMinimumHeight(32)
        form.addRow("الاسم * :", self.inp_name)

        self.inp_role = QLineEdit()
        self.inp_role.setPlaceholderText("مثال: مدير، محاسب، مندوب...")
        self.inp_role.setMinimumHeight(32)
        form.addRow("الصفة :", self.inp_role)

        self.inp_phone = QLineEdit()
        self.inp_phone.setMinimumHeight(32)
        form.addRow("الهاتف :", self.inp_phone)

        self.inp_email = QLineEdit()
        self.inp_email.setMinimumHeight(32)
        form.addRow("الإيميل :", self.inp_email)

        self.inp_notes = QLineEdit()
        self.inp_notes.setMinimumHeight(32)
        form.addRow("ملاحظات :", self.inp_notes)

        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅  إضافة")
        btn_ok.setMinimumHeight(34)
        btn_ok.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 6px;
                padding: 0 16px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_ok.clicked.connect(self._ok)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(34)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: white; color: #374151;
                border: 1px solid #cdd3e0; border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #f8f9fb; }
        """)
        btn_cancel.clicked.connect(self.reject)

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
            QMessageBox.warning(self, "تنبيه", "أدخل اسم جهة الاتصال")
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