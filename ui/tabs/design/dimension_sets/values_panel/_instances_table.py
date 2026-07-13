"""
ui/tabs/design/dimension_sets/values_panel/_instances_table.py
=====================================
مع دعم تغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,
    QMessageBox,
    QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from ui.widgets.panels.themed_inputs import ThemedFrame

from services.design import get_dimension_set_service
from ._instance_popup import _InstancePopup
from ui.font import get_font_size, fs, FS_XL
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.constants import (
    DIM_INST_TBL_BTN_BORDER_W, DIM_INST_TBL_BTN_RADIUS, DIM_INST_TBL_BTN_PAD_V,
    DIM_INST_TBL_BTN_PAD_H, DIM_INST_TBL_PRIMARY_PAD_V, DIM_INST_TBL_PRIMARY_PAD_H,
    DIM_INST_TBL_TOOLBAR_MARGIN_H, DIM_INST_TBL_TOOLBAR_MARGIN_V, DIM_INST_TBL_TOOLBAR_SPACING,
    DIM_INST_TBL_BTN_H, DIM_INST_TBL_CELL_PAD, DIM_INST_TBL_CELL_PAD_H, DIM_INST_TBL_HDR_BORDER_W,
    DIM_INST_TBL_STATUS_PAD, DIM_INST_TBL_NAME_COL_W, DIM_INST_TBL_VALUE_COL_W,
    DIM_INST_TBL_MIN_SECTION_W, DIM_INST_TBL_ROW_H_PAD, DIM_INST_TBL_EMPTY_SPACING,
    DIM_INST_TBL_HAIRLINE_W,
)

# [إصلاح dark-theme] المتغيرات دي كانت بتتحسب مرة واحدة وقت الـ import
# (وقت ما بايثون يحمّل الموديول لأول مرة) وبتحفظ القيمة الـ hex الثابتة
# بتاعة الثيم الحالي وقتها فقط — غالبًا Light (الثيم الافتراضي في
# _init_default_theme). أي تغيير لاحق للثيم عبر theme_manager.set_theme()
# مبيأثرش على المتغيرات دي خالص لأنها مش بتتقرأ من _C تاني، فكانت
# تفضل بلون الثيم الأول (فاتح) للأبد. الحل: قراءة _C[...] مباشرة وقت
# الاستخدام (جوه الدوال) بدل تجميد القيمة كمتغير module-level.


def _btn_danger_ss(base: int) -> str:
    return (
        f"QPushButton {{"
        f"  background: {_C['danger_bg']}; color: {_C['danger']};"
        f"  border: {DIM_INST_TBL_BTN_BORDER_W}px solid {_C['danger_border']}; border-radius: {DIM_INST_TBL_BTN_RADIUS}px;"
        f"  padding: {DIM_INST_TBL_BTN_PAD_V}px {DIM_INST_TBL_BTN_PAD_H}px; font-size: {fs(base,0)}pt;"
        f"}}"
        f"QPushButton:hover {{ background: {_C['danger_bg']}; border-color: {_C['danger']}; }}"
    )


def _btn_ghost_ss(base: int) -> str:
    return (
        f"QPushButton {{"
        f"  background: {_C['bg_input']}; color: {_C['accent']};"
        f"  border: {DIM_INST_TBL_BTN_BORDER_W}px solid {_C['accent_light']}; border-radius: {DIM_INST_TBL_BTN_RADIUS}px;"
        f"  padding: {DIM_INST_TBL_BTN_PAD_V}px {DIM_INST_TBL_BTN_PAD_H}px; font-size: {fs(base,0)}pt;"
        f"}}"
        f"QPushButton:hover {{ background: {_C['accent_light']}; }}"
    )


def _btn_primary_ss(base: int) -> str:
    return (
        f"QPushButton {{"
        f"  background: {_C['accent']}; color: {_C['accent_text']};"
        f"  border: none; border-radius: {DIM_INST_TBL_BTN_RADIUS}px;"
        f"  padding: {DIM_INST_TBL_PRIMARY_PAD_V}px {DIM_INST_TBL_PRIMARY_PAD_H}px; font-weight: bold; font-size: {fs(base,0)}pt;"
        f"}}"
        f"QPushButton:hover  {{ background: {_C['accent_hover']}; }}"
        f"QPushButton:disabled {{ background: {_C['border_med']}; }}"
    )


class _InstancesTable(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._svc    = get_dimension_set_service(conn)
        self._set_id = None
        self._fields = []
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def showEvent(self, event):
        """
        [إصلاح dark-theme] Qt بيخزّن أي تغيير stylesheet وقت ما الـ widget
        مخفية (isVisible == False)، لكن مبيعيدش رسمها فعليًا إلا لما تظهر
        تاني على الشاشة — وأحيانًا بيرسمها بحالة قديمة (cached) بدل الستايل
        الجديد المخزّن. لو الثيم اتغيّر وإحنا في تاب تاني (يعني الودجت دي
        كانت مخفية وقتها)، الألوان بتتحدث في الذاكرة صح لكن الرسم الفعلي
        بيفضل قديم لحد أول مرة تظهر فيها الودجت. الحل: نجبر إعادة تطبيق
        الستايل بالكامل في اللحظة اللي الودجت بتظهر فيها فعليًا.
        """
        super().showEvent(event)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()

        # [إصلاح dark-theme الجذري] self (_InstancesTable) نفسها — راجع
        # التعليق في _build لتفاصيل السبب.
        self.setStyleSheet(f"background: {_C['bg_input']};")

        # تحديث الـ toolbar label
        self._lbl_set_name.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_C['text_primary']};
            background: transparent;
        """)

        # تحديث الأزرار
        self.btn_add.setStyleSheet(_btn_primary_ss(base))
        self.btn_edit.setStyleSheet(_btn_ghost_ss(base))
        self.btn_copy.setStyleSheet(_btn_ghost_ss(base))
        self.btn_del.setStyleSheet(_btn_danger_ss(base))

        # تحديث الجدول
        self.table.setStyleSheet(self._table_ss())

        # تحديث الـ status bar
        self._status_bar.setStyleSheet(f"""
            background: {_C['bg_surface']};
            color: {_C['text_muted']};
            font-size: {fs(base,-1)}pt;
            padding: {DIM_INST_TBL_STATUS_PAD}px;
            border-top: {DIM_INST_TBL_HAIRLINE_W}px solid {_C['border']};
        """)

        # [إصلاح dark-theme] _empty_state كانت بتاخد خلفيتها وقت البناء
        # بس (_build) ومفيهاش تحديث هنا، فكانت تفضل بلون الثيم القديم
        # بعد التحويل لـ dark. هذا بالظبط سبب المنطقة البيضاء الكبيرة
        # اللي فيها أزرار إضافة/تعديل/نسخ/حذف فوقها.
        if hasattr(self, '_empty_state'):
            self._empty_state.setStyleSheet(f"background: {_C['bg_input']}; border: none;")
            # [إصلاح repaint] القيمة بتتغير فعليًا (تأكدنا بالـ debug) لكن
            # Qt أحيانًا مش بيعيد رسم الـ widget تلقائيًا لو الـ stylesheet
            # اتغير وهو already visible على الشاشة، خصوصًا لو الأب (QSplitter)
            # مش بيبعت resize event. unpolish/polish بيجبر Qt يعيد تقييم
            # الـ stylesheet بالكامل، و update() بيجبر إعادة الرسم الفعلي.
            self._empty_state.style().unpolish(self._empty_state)
            self._empty_state.style().polish(self._empty_state)
            self._empty_state.update()

        # [إصلاح repaint شامل] إجبار إعادة رسم الـ widget بالكامل كحماية
        # إضافية — يغطي أي child تاني ممكن يكون واقع في نفس مشكلة الـ
        # stale repaint رغم إن الـ stylesheet اتحدث فعليًا في الذاكرة.
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        if hasattr(self, '_empty_state'):
            es = self._empty_state


    def _on_font_changed(self, size: int = None):
        """يُبقيها متوافقة مع أي نداء خارجي قديم من _ValuesPanel."""
        self._refresh_style()

    def _table_ss(self) -> str:
        base = get_font_size()
        return f"""
            QTableWidget {{
                border: none;
                background: {_C['bg_input']};
                alternate-background-color: {_C['bg_surface']};
                gridline-color: {_C['border']};
                font-size: {fs(base,0)}pt;
                color: {_C['text_primary']};
                outline: none;
            }}
            QTableWidget::item {{
                padding: {DIM_INST_TBL_CELL_PAD}px {DIM_INST_TBL_CELL_PAD_H}px;
            }}
            QTableWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent']};
            }}
            QHeaderView::section {{
                background: {_C['bg_surface']};
                color: {_C['text_muted']};
                font-weight: bold;
                font-size: {fs(base,-1)}pt;
                padding: {DIM_INST_TBL_CELL_PAD}px {DIM_INST_TBL_CELL_PAD_H}px;
                border: none;
                border-bottom: {DIM_INST_TBL_HDR_BORDER_W}px solid {_C['border']};
                border-right: {DIM_INST_TBL_HAIRLINE_W}px solid {_C['border']};
            }}
        """

    def _build(self):
        base = get_font_size()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # [إصلاح dark-theme الجذري] _InstancesTable (self) نفسها — الـ
        # QWidget الأب اللي فيه root layout — ماكانش عندها setStyleSheet
        # خالص، لا هنا ولا في _refresh_style. أي QWidget بدون stylesheet
        # خاص بياخد الخلفية الافتراضية من نظام التشغيل (رمادي فاتح/أبيض
        # على Windows)، مش من _C. وبما إن _empty_state (QFrame داخلي)
        # بياخد بس حجم محتواه (AlignCenter، مش بيتمدد)، فالمساحة الفاضية
        # حواليه كانت بتفضل بلون الخلفية الافتراضي الأبيض ده — مش لون
        # الثيم. هذا هو السبب الحقيقي للمربع الأبيض في كل الصور.
        self.setStyleSheet(f"background: {_C['bg_input']};")

        # ── Toolbar ──
        toolbar = ThemedFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border-bottom: {DIM_INST_TBL_HAIRLINE_W}px solid {_C['border']};
            }}
        """)
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(DIM_INST_TBL_TOOLBAR_MARGIN_H, DIM_INST_TBL_TOOLBAR_MARGIN_V,
                                  DIM_INST_TBL_TOOLBAR_MARGIN_H, DIM_INST_TBL_TOOLBAR_MARGIN_V)
        t_lay.setSpacing(DIM_INST_TBL_TOOLBAR_SPACING)

        self._lbl_set_name = QLabel(tr("dim_inst_table_placeholder"))
        self._lbl_set_name.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_C['text_primary']};
            background: transparent;
        """)
        t_lay.addWidget(self._lbl_set_name, stretch=1)

        self.btn_add = QPushButton(tr("dim_inst_add_btn"))
        self.btn_add.setStyleSheet(_btn_primary_ss(base))
        self.btn_add.setMinimumHeight(DIM_INST_TBL_BTN_H)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self._add_instance)

        self.btn_edit = QPushButton(tr("dim_inst_edit_btn"))
        self.btn_edit.setStyleSheet(_btn_ghost_ss(base))
        self.btn_edit.setMinimumHeight(DIM_INST_TBL_BTN_H)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._edit_instance)

        self.btn_copy = QPushButton(tr("dim_inst_copy_btn"))
        self.btn_copy.setStyleSheet(_btn_ghost_ss(base))
        self.btn_copy.setMinimumHeight(DIM_INST_TBL_BTN_H)
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._copy_instance)

        self.btn_del = QPushButton(tr("btn_delete"))
        self.btn_del.setStyleSheet(_btn_danger_ss(base))
        self.btn_del.setMinimumHeight(DIM_INST_TBL_BTN_H)
        self.btn_del.setEnabled(False)
        self.btn_del.clicked.connect(self._delete_instance)

        t_lay.addWidget(self.btn_add)
        t_lay.addWidget(self.btn_edit)
        t_lay.addWidget(self.btn_copy)
        t_lay.addWidget(self.btn_del)

        root.addWidget(toolbar)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setStyleSheet(self._table_ss())
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.horizontalHeader().setMinimumSectionSize(DIM_INST_TBL_MIN_SECTION_W)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(lambda: self._edit_instance())
        root.addWidget(self.table, stretch=1)

        # ── Status Bar ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_C['bg_surface']};
            color: {_C['text_muted']};
            font-size: {fs(base,-1)}pt;
            padding: {DIM_INST_TBL_STATUS_PAD}px;
            border-top: {DIM_INST_TBL_HAIRLINE_W}px solid {_C['border']};
        """)
        root.addWidget(self._status_bar)

        # ── Empty State ──
        self._empty_state = ThemedFrame()
        self._empty_state.setStyleSheet(f"background: {_C['bg_input']}; border: none;")
        e_lay = QVBoxLayout(self._empty_state)
        e_lay.setAlignment(Qt.AlignCenter)
        e_lbl = QLabel(tr("dim_inst_empty_icon"))
        e_lbl.setAlignment(Qt.AlignCenter)
        e_lbl.setStyleSheet(f"font-size: {fs(FS_XL, +24)}pt; background: transparent;")
        e_msg = QLabel(tr("dim_inst_table_placeholder"))
        e_msg.setAlignment(Qt.AlignCenter)
        e_msg.setStyleSheet(f"color: {_C['text_muted']}; font-size: {fs(base,+1)}pt; background: transparent;")
        e_hint = QLabel(tr("dim_sets_empty_select_hint"))
        e_hint.setAlignment(Qt.AlignCenter)
        e_hint.setStyleSheet(f"color: {_C['border_med']}; font-size: {fs(base,-1)}pt; background: transparent;")
        e_lay.addWidget(e_lbl)
        e_lay.addSpacing(DIM_INST_TBL_EMPTY_SPACING)
        e_lay.addWidget(e_msg)
        e_lay.addWidget(e_hint)

        root.addWidget(self._empty_state)
        self.table.setVisible(False)
        self._status_bar.setVisible(False)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self.btn_add.setEnabled(True)

        try:
            set_name = self._svc.get_set_name(set_id)
        except Exception:
            set_name = tr("dim_unnamed_set_fallback").format(id=set_id)
        self._lbl_set_name.setText(f"{tr('dim_sets_set_icon')}  {set_name}")

        self._fields = [
            f for f in self._svc.list_fields(set_id)
            if f["field_type"] == "number"
        ]
        self._empty_state.setVisible(False)
        self.table.setVisible(True)
        self._status_bar.setVisible(True)
        self._refresh_table()

    def _refresh_table(self):
        if not self._set_id:
            return

        prev_row = self.table.currentRow()
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setRowCount(0)

        col_labels = [tr("dim_inst_col_name")] + [f["label"] for f in self._fields]
        self.table.setColumnCount(len(col_labels))
        self.table.setHorizontalHeaderLabels(col_labels)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.setColumnWidth(0, DIM_INST_TBL_NAME_COL_W)
        for i in range(1, len(col_labels)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            self.table.setColumnWidth(i, DIM_INST_TBL_VALUE_COL_W)
        if len(col_labels) > 1:
            hh.setSectionResizeMode(len(col_labels) - 1, QHeaderView.Stretch)

        instances = self._svc.list_instances(self._set_id)
        base = get_font_size()
        for inst in instances:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, fs(base, 0) * 3 + DIM_INST_TBL_ROW_H_PAD)

            name = inst["name"].strip() if inst["name"].strip() else tr("dim_unnamed_set_fallback").format(id=inst['id'])
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, inst["id"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            name_item.setForeground(QColor(_C['acc_type_asset']))
            self.table.setItem(r, 0, name_item)

            values = self._svc.get_instance_values(inst["id"])
            for ci, f in enumerate(self._fields, start=1):
                val_info = values.get(f["id"], {})
                val = val_info.get("value_num")
                unit = f["unit"] or ""
                txt  = f"{val:g}  {unit}".strip() if val is not None else tr("dim_value_empty")
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if val is None:
                    item.setForeground(QColor(_C['text_muted']))
                self.table.setItem(r, ci, item)

        self.table.blockSignals(False)

        cnt = self.table.rowCount()
        self._status_bar.setText(tr("dim_inst_table_status").format(count=cnt))

        if prev_row >= 0 and prev_row < cnt:
            self.table.selectRow(prev_row)

        self._update_action_btns()

    def _selected_instance_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        self._update_action_btns()

    def _update_action_btns(self):
        has_sel = self._selected_instance_id() is not None
        self.btn_edit.setEnabled(has_sel)
        self.btn_copy.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)

    def _add_instance(self):
        if not self._set_id:
            return
        popup = _InstancePopup(self.conn, self._set_id, parent=self)
        popup.saved.connect(self._on_saved)
        popup.exec_()

    def _edit_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        popup = _InstancePopup(self.conn, self._set_id,
                               instance_id=iid, parent=self)
        popup.saved.connect(self._on_saved)
        popup.exec_()

    def _copy_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = self._svc.get_instance(iid)
        src_name = inst["name"] if inst else ""
        name, ok = QInputDialog.getText(
            self, tr("dim_inst_copy_title"),
            tr("dim_inst_copy_label"),
            text=tr("dim_inst_copy_default").format(name=src_name) if src_name else ""
        )
        if ok:
            self._svc.duplicate_instance(iid, name.strip())
            self._refresh_table()

    def _delete_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = self._svc.get_instance(iid)
        name = inst["name"] if inst and inst["name"] else f"#{iid}"
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("dim_inst_delete_confirm").format(name=name),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self._svc.delete_instance(iid)
            self._refresh_table()

    def _on_saved(self, instance_id: int):
        self._refresh_table()
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == instance_id:
                self.table.selectRow(r)
                break

    def clear(self):
        self._set_id = None
        self._fields = []
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setVisible(False)
        self._status_bar.setVisible(False)
        self._empty_state.setVisible(True)
        self._lbl_set_name.setText(tr("dim_inst_table_placeholder"))
        self.btn_add.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.btn_del.setEnabled(False)