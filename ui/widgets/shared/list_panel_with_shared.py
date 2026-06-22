"""
ui/widgets/shared/list_panel_with_shared.py
============================================
SharedItemsListPanel — قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة.

يرث من BaseListPanel + SharedOpsMixin + LiveConnMixin ويضيف:
  - legend العناصر المشتركة/المنشورة
  - دمج الصفوف المحلية مع المشتركة
  - أزرار: تعديل / حذف / استبدال شامل / تعديل مشترك / نشر كمشترك
  - منطق التلوين للصفوف المشتركة/المنشورة
  - _live_conn() عبر LiveConnMixin (لا override — يستخدم الـ mixin مباشرة)
  - _selected_row_data() للحصول على بيانات الصف المختار

إعدادات الـ subclass:
  SHARED_TYPE      : str  — نوع العنصر المشترك ("raw"|"machine"|"labor_op"|"machine_op")
  TABLE_COLS       : list — أسماء الأعمدة
  FILTER_SCOPE     : str  — نطاق الفلتر (افتراضياً يستخدم SHARED_TYPE)
  TABLE_TITLE      : str  — عنوان الجدول
  HAS_BULK_REPLACE : bool — هل يدعم الاستبدال الشامل

Hooks المطلوبة في الـ subclass:
  _fetch_local_rows() → list[dict]
  _get_shared_rows(local_rows) → list[dict]
  _fill_table_row(r, item)
  _edit_item(item_id)
  _delete_item(item_id, item_name)
  _get_item_data_for_publish(row) → dict

Hooks الاختيارية:
  _bulk_replace_item(item_id, item_name)
  _setup_column_widths(table)
  _on_edit_shared()   — override لتخصيص سلوك تعديل المشترك

[إصلاح] حذف _live_conn override الخاطئ الذي كان يتجاهل LiveConnMixin.
  القديم: كان يستدعي get_connection() مباشرة، متجاهلاً company_state.
  الجديد: يعتمد على LiveConnMixin._live_conn() الموروثة التي تستخدم
          self.conn أولاً ثم company_state كـ fallback.

[إصلاح FILTER_SCOPE] القديم: FILTER_SCOPE = "all" ثابت، يُظهر كل التصنيفات بغض النظر عن SHARED_TYPE.
  الجديد: _build_filter() يستخدم SHARED_TYPE كـ scope للفلتر لو لم يُحدَّد FILTER_SCOPE صراحةً.
  هذا يضمن أن قائمة التصنيفات تتطابق مع نوع العنصر المعروض.
"""

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5.QtGui     import QColor

from ui.widgets.base.list_panel       import BaseListPanel
from ui.widgets.mixins.shared_ops     import SharedOpsMixin
from ui.widgets.core.conn             import LiveConnMixin
from ui.widgets.dialogs.confirm       import confirm_delete
from ui.tabs.costing.shared._utils    import (
    SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG,
)
from ui.tabs.companies.shared_items_mixin import get_published_local_names
from ui.widgets.core.i18n             import tr


class SharedItemsListPanel(BaseListPanel, SharedOpsMixin, LiveConnMixin):
    """
    قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة.
    راجع docstring الملف للتفاصيل الكاملة.

    [إصلاح] لا override لـ _live_conn — LiveConnMixin تتولى الأمر.
    الـ inheritance chain: SharedItemsListPanel → BaseListPanel → BusConnectedMixin
                                                 → LiveConnMixin
    LiveConnMixin._live_conn() يستخدم self.conn ثم company_state كـ fallback.

    [إصلاح FILTER_SCOPE] _build_filter يستخدم SHARED_TYPE كـ scope
    لو لم يُحدَّد FILTER_SCOPE صراحةً في الـ subclass.
    """

    # [إصلاح] يُحدَّد صريحاً لإسكات false-positive warning من LiveConnMixin.
    # السبب: __init_subclass__ بتفحص substring "conn" في أسماء الـ class attrs،
    # و"CONNECT_BUS" تحتوي "conn" (من Connect) بالغلط مع إنها بوليني غير متعلق
    # بـ DB connection خالص. القيمة "conn" هي الصحيحة فعلياً (موروثة من
    # BaseListPanel وتُستخدم في self.conn بكل الكود) — لكن لازم تُذكر هنا
    # صريحةً في cls.__dict__ لإيقاف الفحص قبل ما يصل لـ CONNECT_BUS.
    _conn_attr = "conn"

    # ── إعدادات الـ subclass ──────────────────────────────
    SHARED_TYPE      : str  = "raw"
    TABLE_COLS       : list = []
    TABLE_TITLE      : str  = ""
    HAS_BULK_REPLACE : bool = False

    # ── BaseListPanel settings ────────────────────────────
    SHOW_CATEGORY    : bool = True
    CONNECT_BUS      : bool = True
    ADD_TEXT         : str  = ""

    # FILTER_SCOPE — لو لم يُحدَّد في الـ subclass، يُستخدم SHARED_TYPE تلقائياً
    # انظر _build_filter() أدناه
    FILTER_SCOPE     : str  = ""   # فارغ = استخدم SHARED_TYPE

    def __init__(self, conn=None, parent=None):
        # تحويل TABLE_COLS → COLUMNS المطلوب من BaseListPanel
        self.COLUMNS    = self.TABLE_COLS
        self.LIST_TITLE = self.TABLE_TITLE
        self.STRETCH_COL = 1
        self._published_names: set = set()
        super().__init__(conn, parent)
        # ضبط عرض الأعمدة بعد بناء الجدول
        self._setup_column_widths(self.table)
        self.table.setColumnHidden(0, True)

    # ══════════════════════════════════════════════════════
    # Hooks المطلوبة
    # ══════════════════════════════════════════════════════

    def _fetch_local_rows(self) -> list:
        raise NotImplementedError

    def _get_shared_rows(self, local_rows: list) -> list:
        return []

    def _fill_table_row(self, r: int, item: dict):
        raise NotImplementedError

    def _edit_item(self, item_id: int):
        raise NotImplementedError

    def _delete_item(self, item_id: int, item_name: str):
        raise NotImplementedError

    def _get_item_data_for_publish(self, row: dict) -> dict:
        return {}

    # ══════════════════════════════════════════════════════
    # Hooks الاختيارية
    # ══════════════════════════════════════════════════════

    def _bulk_replace_item(self, item_id: int, item_name: str):
        """Override لإضافة منطق الاستبدال الشامل."""

    def _setup_column_widths(self, table):
        """Override لضبط عرض الأعمدة."""

    # ══════════════════════════════════════════════════════
    # BaseListPanel interface
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        """يدمج الصفوف المحلية مع المشتركة."""
        self._published_names = get_published_local_names(self.SHARED_TYPE)
        local_rows  = self._fetch_local_rows()
        shared_rows = self._get_shared_rows(local_rows)
        return local_rows + shared_rows

    def _fill_row(self, table, r: int, row: dict):
        """يطبق التلوين ثم يستدعي _fill_table_row."""
        self._fill_table_row(r, row)
        self._apply_row_colors(r, row)

    # ══════════════════════════════════════════════════════
    # [إصلاح FILTER_SCOPE] override _build_filter
    # ══════════════════════════════════════════════════════

    def _build_filter(self):
        """
        [إصلاح FILTER_SCOPE] يستخدم SHARED_TYPE كـ scope لو FILTER_SCOPE فارغ.

        القديم: FILTER_SCOPE = "all" ثابت → يُظهر كل التصنيفات دائماً
        الجديد: scope = SHARED_TYPE لو FILTER_SCOPE فارغ → تصنيفات نوع العنصر فقط

        مثال: raw panel يُعرض تصنيفات "raw" فقط بدل كل التصنيفات.
        """
        if not self.SHOW_CATEGORY:
            return None

        scope = self.FILTER_SCOPE if self.FILTER_SCOPE else self.SHARED_TYPE

        from ui.widgets.panels.filter import FilterToolbar
        toolbar = FilterToolbar(
            conn          = self.conn,
            scope         = scope,
            show_category = self.SHOW_CATEGORY,
            show_date     = self.SHOW_DATE,
            placeholder   = self.SEARCH_PLACEHOLDER,
        )
        toolbar.filter_changed.connect(lambda: self._timer.start())
        self.inp_search = toolbar.inp_search
        return toolbar

    # ══════════════════════════════════════════════════════
    # التلوين
    # ══════════════════════════════════════════════════════

    def _apply_row_colors(self, r: int, item: dict):
        """يُطبق ألوان الصف حسب حالته (مشترك/منشور/عادي)."""
        is_shared    = item.get("_is_shared", False)
        is_published = item.get("_is_published", False)

        if not is_shared and not is_published:
            name = str(item.get("name", "")).strip().lower()
            is_published = name in self._published_names

        if is_shared:
            fg, bg = SHARED_COLOR, SHARED_BG
        elif is_published:
            fg, bg = PUBLISHED_COLOR, PUBLISHED_BG
        else:
            return

        for col in range(self.table.columnCount()):
            itm = self.table.item(r, col)
            if itm:
                itm.setForeground(QColor(fg))
                itm.setBackground(QColor(bg))

    # ══════════════════════════════════════════════════════
    # أزرار الهيدر
    # ══════════════════════════════════════════════════════

    def _build_extra_header_actions(self, header):
        if self.HAS_BULK_REPLACE:
            header.add_action(tr("shared_bulk_replace_btn"),  self._on_bulk_replace,  "primary")
        header.add_action(tr("edit_selected_btn"),   self._on_edit_selected)
        header.add_action(tr("delete_selected_btn"), self._on_delete_selected, "danger")
        header.add_action(tr("shared_edit_shared_btn"),  self._on_edit_shared)
        header.add_action(tr("shared_publish_as_shared_btn"), self._on_publish_selected)

    # ══════════════════════════════════════════════════════
    # إجراءات الأزرار
    # ══════════════════════════════════════════════════════

    def _on_edit_selected(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("select_item_first"))
            return
        self._edit_item(item_id)

    def _on_delete_selected(self):
        item_id, item_name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("select_item_first"))
            return
        self._delete_item(item_id, item_name)

    def _on_bulk_replace(self):
        item_id, item_name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("select_item_first"))
            return
        self._bulk_replace_item(item_id, item_name)

    def _on_edit_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("select_item_first"))
            return
        self._edit_shared_item(item_id, self.SHARED_TYPE, self)

    def _on_publish_selected(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("select_item_first"))
            return
        row = self._get_current_row_dict()
        if not row:
            return
        self._publish_item(row, self.SHARED_TYPE,
                           self._get_item_data_for_publish(row), self)

    # ══════════════════════════════════════════════════════
    # BaseListPanel hooks
    # ══════════════════════════════════════════════════════

    def _on_add_clicked(self):
        pass  # الإضافة عبر فورم منفصل

    def _on_edit_item(self, item_id):
        self._edit_item(item_id)

    def _on_delete_item(self, item_id, item_name: str):
        self._delete_item(item_id, item_name)

    def _on_row_double_clicked(self, item_id):
        self._edit_item(item_id)

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _selected_row_data(self) -> "tuple[int|None, str]":
        """يرجع (item_id, item_name) للصف المختار."""
        item_id = self.selected_id()
        if item_id is None:
            return None, ""
        row = self._get_current_row_dict()
        name = row.get("name", f"ID:{item_id}") if row else f"ID:{item_id}"
        return item_id, name

    def _get_current_row_dict(self) -> "dict | None":
        """يرجع dict بيانات الصف المختار من _all_rows."""
        item_id = self.selected_id()
        if item_id is None:
            return None
        for row in self._all_rows:
            if str(row.get("id")) == str(item_id):
                return row
        return None

    # ══════════════════════════════════════════════════════
    # [إصلاح] لا _live_conn override هنا.
    # LiveConnMixin._live_conn() موروثة وتعمل صح:
    #   1. تجرب self.conn أولاً
    #   2. ثم company_state كـ fallback
    #   3. ترمي RuntimeError واضحة لو فشل كل شيء
    # ══════════════════════════════════════════════════════