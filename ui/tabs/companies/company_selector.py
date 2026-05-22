"""
ui/widgets/shared/company_selector.py
=======================================
Dropdown اختيار الشركة النشطة — يظهر في header النافذة الرئيسية.

يُطلق signal company_changed(company_id, name, color)
عند تغيير الشركة المختارة.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor

from db.companies.companies_schema import get_central_connection, create_central_tables
from db.companies.companies_repo   import fetch_all_companies
from db.companies.company_state    import company_state
from ui.app_settings               import _C


class CompanySelector(QWidget):
    """
    شريط اختيار الشركة النشطة.
    signal: company_changed(company_id: int)
    """
    company_changed = pyqtSignal(int)   # يُطلق عند تغيير الشركة

    def __init__(self, parent=None):
        super().__init__(parent)
        self._central_conn = None
        self._companies    = []
        self._build()
        self._load()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)

        # أيقونة
        ico = QLabel("🏢")
        ico.setStyleSheet("font-size: 13pt; background: transparent; border: none;")
        ico.setFixedWidth(22)
        lay.addWidget(ico)

        # الـ combo
        self._combo = QComboBox()
        self._combo.setMinimumWidth(180)
        self._combo.setFixedHeight(30)
        self._combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 11pt;
                font-weight: 600;
                color: {_C['sidebar_text']};
                background: {_C['sidebar_hover']};
                border: 1px solid {_C['sidebar_border']};
                border-radius: 5px;
                padding: 2px 8px;
            }}
            QComboBox:hover {{
                background: {_C['sidebar_active']};
                border-color: {_C['accent_mid']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {_C['sidebar_bg']};
                color: {_C['sidebar_text']};
                border: 1px solid {_C['sidebar_border']};
                selection-background-color: {_C['sidebar_active']};
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                min-height: 28px;
            }}
        """)
        self._combo.currentIndexChanged.connect(self._on_changed)
        lay.addWidget(self._combo)

        # زر الإدارة
        self._manage_btn = QPushButton("⚙")
        self._manage_btn.setFixedSize(30, 30)
        self._manage_btn.setToolTip("إدارة الشركات")
        self._manage_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {_C['sidebar_border']};
                border-radius: 5px;
                color: {_C['sidebar_muted']};
                font-size: 12pt;
            }}
            QPushButton:hover {{
                background: {_C['sidebar_hover']};
                color: {_C['sidebar_text']};
            }}
        """)
        self._manage_btn.clicked.connect(self._open_manager)
        lay.addWidget(self._manage_btn)

    # ── تحميل الشركات ─────────────────────────────────────

    def _get_central(self):
        if not self._central_conn:
            self._central_conn = get_central_connection()
            create_central_tables(self._central_conn)
        return self._central_conn

    def _load(self):
        """تحميل الشركات في الـ combo."""
        self._combo.blockSignals(True)
        self._combo.clear()

        try:
            conn = self._get_central()
            self._companies = list(fetch_all_companies(conn, active_only=True))
        except Exception as e:
            print(f"[CompanySelector] load error: {e}")
            self._companies = []

        if not self._companies:
            self._combo.addItem("— لا توجد شركات —")
            self._combo.setEnabled(False)
        else:
            self._combo.setEnabled(True)
            for c in self._companies:
                self._combo.addItem(f"  {c['name']}", userData=c["id"])

            # استعادة الشركة النشطة لو موجودة
            if company_state.is_ready:
                for i, c in enumerate(self._companies):
                    if c["id"] == company_state.company_id:
                        self._combo.setCurrentIndex(i)
                        break
            else:
                # اختر الأولى تلقائياً
                self._combo.setCurrentIndex(0)

        self._combo.blockSignals(False)

        # فعّل الشركة الحالية
        if self._companies:
            idx = self._combo.currentIndex()
            if 0 <= idx < len(self._companies):
                self._activate(idx)

    def _on_changed(self, idx: int):
        if 0 <= idx < len(self._companies):
            self._activate(idx)

    def _activate(self, idx: int):
        company = self._companies[idx]
        cid     = company["id"]
        name    = company["name"]
        color   = company["color"] or "#1565c0"

        company_state.set_active(cid, name, color)
        self.company_changed.emit(cid)

    # ── فتح نافذة إدارة الشركات ───────────────────────────

    def _open_manager(self):
        from ui.tabs.companies.companies_dialog import CompaniesDialog
        dlg = CompaniesDialog(self._get_central(), parent=self)
        dlg.exec_()
        # إعادة تحميل بعد أي تغيير
        current_id = company_state.company_id
        self._load()
        # استعد الشركة القديمة لو ما زالت موجودة
        if current_id:
            for i, c in enumerate(self._companies):
                if c["id"] == current_id:
                    self._combo.setCurrentIndex(i)
                    break

    def refresh(self):
        """إعادة تحميل القائمة من الخارج."""
        self._load()

    def closeEvent(self, event):
        if self._central_conn:
            try:
                self._central_conn.close()
            except Exception:
                pass
        super().closeEvent(event)