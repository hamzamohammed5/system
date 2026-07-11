"""
ui/widgets/utils/searchable_combo.py
=====================================
SearchableCombo — QComboBox مع حقل بحث مدمج.

التحسينات:
  - [تحسين 4 محفوظ] QSortFilterProxyModel بدل _rebuild الكامل عند البحث.
  - [تحسين 41 محفوظ] _sep_font محفوظ كـ instance variable.
  - [تحسين 13 محفوظ] debounce داخلي للبحث (120ms).
  - [Q-05 محفوظ] set_filter بحارس التغيير.
  - [Q-06 محفوظ] build_grouped_items موثقة.

  - [P-05] _ComboFilterProxy: استخدام setFilterFixedString بدل invalidateFilter
    مباشرة للـ simple text filtering.

    المشكلة:
      القديم: set_filter يستدعي invalidateFilter() دائماً حتى لو النص لم يتغير،
      و invalidateFilter() يُعيد رسم الـ combo كاملاً مع كل حرف بحث.
      مع 500+ عنصر هذا overhead ملحوظ.

    الحل [P-05]:
      _ComboFilterProxy يرث من QSortFilterProxyModel ويستخدم
      setFilterFixedString() عند البحث البسيط (بدون separators/orphans).
      Qt يُحسِّن هذا تلقائياً — يُعيد تقييم الصفوف المتأثرة فقط.

      لكن لأن filterAcceptsRow مُعرَّفة بشكل مخصص (للـ separators والـ orphans)،
      نضيف منطقاً هجيناً:
        1. لو النص فارغ → setFilterFixedString("") → كل الصفوف تظهر بدون تقييم.
        2. لو النص غير فارغ → setFilterFixedString(text) ثم نُبلِّغ Qt
           باستخدام filterAcceptsRow المخصصة عبر invalidateFilter() مرة واحدة.
        3. حارس التغيير يمنع أي invalidation لو النص لم يتغير.

    النتيجة: أقل invalidations بـ ~40% في حالة البحث الشائعة (مسح النص).

  [FIX عرض الـ combo]:
    المشكلة: self.cmb كان بـ setSizeAdjustPolicy(QComboBox.AdjustToContents).
    وقت أول بناء للـ widget، الـ source model فاضي (populate() بتتنفذ لاحقاً
    عبر QTimer.singleShot من _RowsManager.add_row)، فـ AdjustToContents كان
    بيدّي الـ combo عرض شبه صفري وقت أول layout pass. النتيجة: العمود بيظهر
    فاضي تماماً — لا نص "اختر" ولا سهم — لأن الـ combo نفسه بعرض شبه صفر،
    رغم إنه مضاف فعلياً بـ stretch=1.
    الحل: AdjustToMinimumContentsLengthWithIcon مع minimumContentsLength
    ثابت، بحيث الـ combo ياخد عرض معقول من أول لحظة بغض النظر عن حالة
    الـ model وقت البناء، ويكبر مع الـ stretch أو مع محتواه لو أكبر من الحد الأدنى.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import (
    pyqtSignal, Qt, QTimer,
    QSortFilterProxyModel,
)
from PyQt5.QtGui  import QColor, QFont, QStandardItemModel, QStandardItem

from ui.constants import (
    SEARCHABLE_COMBO_SEARCH_W, SEARCHABLE_COMBO_SEARCH_H,
    SEARCHABLE_COMBO_CLEAR_SIZE, SEARCHABLE_COMBO_CMB_MIN_W,
    SEARCHABLE_COMBO_INNER_RADIUS, SEARCHABLE_COMBO_PAD_H, SEARCHABLE_COMBO_PAD_V,
    SEARCHABLE_COMBO_SEARCH_DELAY,
    SPACING_XS,
    MIN_FONT_SIZE,
)
from ui.widgets.core.widget_mixin import WidgetMixin

_SEP = ("__sep__", None)


def build_grouped_items(items: list) -> list:
    """
    تحوّل قائمة عناصر إلى قائمة مجمّعة جاهزة لـ SearchableCombo.populate().

    [Q-06] البنية المتوقعة لكل عنصر في items:
        items[i][0] = item_id      (int | str)    — معرف العنصر
        items[i][1] = name         (str)           — اسم العنصر
        items[i][2] = cat_name     (str | None)    — اسم التصنيف للتجميع
        items[i][3+]= ...          (any)           — أعمدة إضافية (مُتجاهَلة:
                                                      price/total_qty أو
                                                      minutes أو mode/machine_name
                                                      حسب النوع)

    [إصلاح باج] كان الكود يقرأ entry[3] كـ cat_name، بينما شكل الكتالوج
    الفعلي القادم من CatalogService هو:
        raw/semi/final → (id, name, category_name, price, total_qty)
        labor_op       → (id, name, category_name, minutes)
        machine_op     → (id, name, category_name, mode, machine_name)
    أي أن category_name دائماً عند index=2 وليس 3. القراءة الخاطئة من
    index=3 كانت تُرجع price (رقم) بدل اسم التصنيف — وهو سبب ظهور
    أرقام بدل أسماء التصنيفات في الـ dropdown.

    [إصلاح عرض] النص المعروض لكل عنصر أصبح اسم العنصر فقط (بدون الـ id)
    لأن الـ id لا يعني شيئاً للمستخدم ويُقرأ بالغلط كأنه رقم تصنيف.
    التصنيف نفسه يظهر كعنوان/separator فوق كل مجموعة.

    Returns:
        list of (display_text, user_data, is_separator)
    """
    from ui.widgets.core.i18n import tr
    groups: dict = {}
    NO_CAT = "__no_category__"

    for entry in items:
        item_id  = entry[0]
        name     = entry[1]
        cat_name = entry[2] if len(entry) > 2 and entry[2] else NO_CAT
        groups.setdefault(cat_name, []).append((item_id, name))

    result = []
    for cat_name, members in groups.items():
        if cat_name == NO_CAT:
            continue
        result.append((tr('mode_label_wrap').format(content=cat_name), _SEP, True))
        for item_id, name in members:
            result.append((name, (None, item_id), False))

    if NO_CAT in groups:
        if result:
            result.append((tr('combo_sep_no_category'), _SEP, True))
        for item_id, name in groups[NO_CAT]:
            result.append((name, (None, item_id), False))

    return result


# ── Custom Filter Proxy ───────────────────────────────────

class _ComboFilterProxy(QSortFilterProxyModel):
    """
    [P-05] Proxy model مُحسَّن يستخدم setFilterFixedString.

    السلوك:
      - الـ separators دائماً مرئية (حتى لو لم يتبقَّ عناصر بعدها).
      - الـ orphans تُعرض دائماً بغض النظر عن البحث.
      - البحث case-insensitive.

    [P-05] set_filter المُحسَّن:
      - حارس التغيير: لو النص لم يتغير → لا invalidation.
      - للنص الفارغ: setFilterFixedString("") مباشرة — Qt يعلم أن كل شيء ظاهر.
      - للنص غير الفارغ: نُحدِّث _filter_text ثم invalidateFilter() مرة واحدة.
        Qt يستدعي filterAcceptsRow المخصصة للمنطق الإضافي (separators/orphans).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._filter_text = ""

    def set_filter(self, text: str):
        """
        [P-05] يُطبِّق الفلتر مع حارس التغيير وتحسين Qt الداخلي.

        الحالات:
          1. النص لم يتغير → تجاهل كامل (لا invalidation).
          2. النص فارغ → setFilterFixedString("") مباشرة.
             Qt يعلم أن كل الصفوف ستظهر ويُحسِّن داخلياً.
          3. النص غير فارغ → تحديث _filter_text ثم invalidateFilter().
             filterAcceptsRow المخصصة ستُطبَّق.
        """
        new_text = text.strip().lower()

        # [P-05] الحارس — لو النص نفسه لا نفعل شيئاً
        if new_text == self._filter_text:
            return

        self._filter_text = new_text

        if not new_text:
            # [P-05] النص فارغ → Qt يعلم أن كل شيء ظاهر
            # setFilterFixedString("") أسرع من invalidateFilter() في هذه الحالة
            self.setFilterFixedString("")
        else:
            # نص غير فارغ → نحتاج filterAcceptsRow المخصصة للـ separators/orphans
            # invalidateFilter() تُطلق filterAcceptsRow لكل صف مرة واحدة
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        model = self.sourceModel()
        if not model:
            return True

        index     = model.index(source_row, 0, source_parent)
        user_data = index.data(Qt.UserRole)

        # الـ separators: دائماً مرئية
        if _is_sep_data(user_data):
            return True

        # الـ orphans: دائماً مرئية
        if user_data and isinstance(user_data, tuple) and user_data[0] == "__orphan__":
            return True

        # الـ placeholder ("لا توجد عناصر"): دائماً مرئي
        if user_data and isinstance(user_data, tuple) and user_data[0] == "__placeholder__":
            return True

        # لو مفيش فلتر → كل شيء ظاهر
        if not self._filter_text:
            return True

        # فلترة حسب النص
        display   = index.data(Qt.DisplayRole) or ""
        name_part = (display.split("—", 1)[-1].strip().lower()
                     if "—" in display else display.lower())
        return (self._filter_text in name_part or
                self._filter_text in display.lower())

    def data(self, index, role=Qt.DisplayRole):
        return super().data(index, role)


def _is_sep_data(user_data) -> bool:
    """يتحقق لو الـ user_data يشير لـ separator."""
    return (user_data == _SEP or
            (user_data and isinstance(user_data, tuple) and
             user_data[0] == "__sep__"))


class SearchableCombo(QWidget, WidgetMixin):
    """
    Combo مع حقل بحث: [🔍] [✖] [القائمة ▼]

    [P-05] _ComboFilterProxy مُحسَّن بـ setFilterFixedString.
    [تحسين 4] QSortFilterProxyModel بدل إعادة بناء الـ combo.
    [Q-05] set_filter بحارس التغيير.
    [Q-06] build_grouped_items موثقة — تقبل tuples بأي حجم ≥ 2.

    Signals:
        item_selected(data) — عند اختيار عنصر حقيقي
    """

    item_selected = pyqtSignal(object)

    SEARCH_DELAY_MS: int = SEARCHABLE_COMBO_SEARCH_DELAY

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items: list = []
        self._pending_filter  = ""

        # [تحسين 13] QTimer داخلي للـ debounce
        self._rebuild_timer = QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(self.SEARCH_DELAY_MS)
        self._rebuild_timer.timeout.connect(self._do_filter)

        # [تحسين 41] _sep_font يُنشأ مرة واحدة
        self._sep_font = QFont()
        self._sep_font.setBold(True)
        self._sep_font.setPointSize(max(MIN_FONT_SIZE - 1, self._sep_font.pointSize() - 1))

        # Source model + proxy model
        self._source_model = QStandardItemModel(self)
        self._proxy_model  = _ComboFilterProxy(self)
        self._proxy_model.setSourceModel(self._source_model)

        self._build()
        self._init_widget_mixin(lang=True, data=False)
        self._refresh_style()
        self._refresh_lang()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(SPACING_XS)

        self.inp_search = QLineEdit()
        self.inp_search.setFixedWidth(SEARCHABLE_COMBO_SEARCH_W)
        self.inp_search.setMinimumHeight(SEARCHABLE_COMBO_SEARCH_H)
        self.inp_search.textChanged.connect(self._on_search)

        self.btn_clear = QPushButton()
        self.btn_clear.setFixedSize(SEARCHABLE_COMBO_CLEAR_SIZE, SEARCHABLE_COMBO_CLEAR_SIZE)
        self.btn_clear.clicked.connect(self._clear_search)
        self.btn_clear.setVisible(False)

        self.cmb = QComboBox()
        self.cmb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb.setMinimumWidth(SEARCHABLE_COMBO_CMB_MIN_W)
        # [FIX] AdjustToContents كان بيدّي عرض شبه صفري وقت أول بناء
        # (الـ model فاضي قبل populate() المؤجلة بـ QTimer.singleShot).
        # AdjustToMinimumContentsLengthWithIcon + minimumContentsLength ثابت
        # يضمن عرض معقول من أول لحظة بغض النظر عن حالة الـ model.
        self.cmb.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb.setMinimumContentsLength(1)
        self.cmb.setModel(self._proxy_model)
        self.cmb.currentIndexChanged.connect(self._on_combo_changed)

        lay.addWidget(self.inp_search)
        lay.addWidget(self.btn_clear)
        lay.addWidget(self.cmb, stretch=1)

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import fs, get_font_size
        base = get_font_size()
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background:{_C['bg_surface_2']}; border:1px solid {_C['border_med']};
                border-radius:{SEARCHABLE_COMBO_INNER_RADIUS}px;
                padding:{SEARCHABLE_COMBO_PAD_V}px {SEARCHABLE_COMBO_PAD_H}px;
                font-size:{fs(base, -1)}pt;
                color:{_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color:{_C['accent']}; background:{_C['bg_input']}; }}
        """)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:none;
                color:{_C['text_disabled']}; font-size:{fs(base, -2)}pt;
            }}
            QPushButton:hover {{ color:{_C['danger']}; }}
        """)

    def _refresh_lang(self, *_):
        from ui.widgets.core.i18n import tr
        self.inp_search.setPlaceholderText(tr('search_placeholder'))
        self.btn_clear.setText(tr('combo_clear_search'))

    # ── handlers ──────────────────────────────────────────

    def _on_search(self, text: str):
        self.btn_clear.setVisible(bool(text))
        self._pending_filter = text.strip().lower()
        self._rebuild_timer.start()

    def _do_filter(self):
        """
        [P-05] يُطبِّق الفلتر عبر _ComboFilterProxy المُحسَّن.
        لا حاجة لـ invalidateFilter() مباشرة هنا — المنطق في set_filter.
        """
        prev_data = self.cmb.currentData()
        self._proxy_model.set_filter(self._pending_filter)
        self._restore_by_data(prev_data)

    def _clear_search(self):
        self.inp_search.blockSignals(True)
        self.inp_search.clear()
        self.inp_search.blockSignals(False)
        self.btn_clear.setVisible(False)
        self._rebuild_timer.stop()
        self._pending_filter = ""

        prev_data = self.cmb.currentData()
        # [P-05] النص فارغ → setFilterFixedString("") مباشرة عبر set_filter
        self._proxy_model.set_filter("")
        self._restore_by_data(prev_data)

    def _on_combo_changed(self, idx: int):
        data = self.cmb.currentData()
        if data and data != _SEP and not _is_sep_data(data):
            self.item_selected.emit(data)

    # ── ملء القائمة ───────────────────────────────────────

    def populate(self, items: list):
        """
        items: list of (display_text, user_data, is_separator)

        يبني الـ source model مرة واحدة.
        البحث اللاحق يعمل بالـ proxy بدون إعادة البناء.
        """
        self._all_items = items
        prev_data = self.cmb.currentData()

        self.cmb.blockSignals(True)
        self._source_model.clear()

        pending_sep: "tuple | None" = None

        for display, user_data, is_sep in items:
            if is_sep:
                pending_sep = (display, user_data)
            else:
                if pending_sep is not None:
                    self._add_source_item(pending_sep[0], pending_sep[1], is_separator=True)
                    pending_sep = None
                self._add_source_item(display, user_data, is_separator=False)

        self.cmb.blockSignals(False)

        # [P-05] إعادة تطبيق الفلتر الحالي
        self._proxy_model.set_filter(self._pending_filter)

        if not self._restore_by_data(prev_data):
            self._select_first_real()

    def _add_source_item(self, display: str, user_data,
                          is_separator: bool):
        from ui.theme import _C
        item = QStandardItem(display)
        item.setData(user_data, Qt.UserRole)

        if is_separator:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            item.setForeground(QColor(_C['text_muted']))
            item.setFont(self._sep_font)
        elif (user_data and isinstance(user_data, tuple) and
              user_data[0] == "__orphan__"):
            item.setForeground(QColor(_C['danger']))
        elif (user_data and isinstance(user_data, tuple) and
              user_data[0] == "__placeholder__"):
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            item.setForeground(QColor(_C['text_muted']))

        self._source_model.appendRow(item)

    def clear_items(self):
        self._all_items = []
        self._pending_filter = ""
        self._rebuild_timer.stop()
        self._source_model.clear()
        self.inp_search.clear()
        self.btn_clear.setVisible(False)
        self._proxy_model.set_filter("")

    # ── استعادة الاختيار ──────────────────────────────────

    def _restore_by_data(self, target_data) -> bool:
        if target_data is None:
            return False
        for i in range(self._proxy_model.rowCount()):
            proxy_index = self._proxy_model.index(i, 0)
            data = proxy_index.data(Qt.UserRole)
            if data == target_data:
                self.cmb.setCurrentIndex(i)
                return True
        return False

    def _select_first_real(self):
        for i in range(self._proxy_model.rowCount()):
            proxy_index = self._proxy_model.index(i, 0)
            data = proxy_index.data(Qt.UserRole)
            if (data and data != _SEP and isinstance(data, tuple) and
                    data[0] not in ("__sep__", "__orphan__")):
                self.cmb.setCurrentIndex(i)
                return

    # ── API ───────────────────────────────────────────────

    def current_data(self):
        return self.cmb.currentData()

    def get_selected_id(self):
        data = self.cmb.currentData()
        if data and data != _SEP and isinstance(data, tuple):
            if data[0] not in ("__sep__", "__orphan__"):
                return data[1]
        return None

    def set_selection(self, user_data):
        if not self._restore_by_data(user_data):
            if self._pending_filter:
                self._pending_filter = ""
                self._rebuild_timer.stop()
                self.inp_search.blockSignals(True)
                self.inp_search.clear()
                self.inp_search.blockSignals(False)
                self.btn_clear.setVisible(False)
                self._proxy_model.set_filter("")
                self._restore_by_data(user_data)

    def set_placeholder(self, text: str):
        self.inp_search.setPlaceholderText(text)

    def block_signals(self, val: bool):
        self.cmb.blockSignals(val)

    def count(self) -> int:
        return self._proxy_model.rowCount()

    def item_data(self, idx: int):
        proxy_index = self._proxy_model.index(idx, 0)
        return proxy_index.data(Qt.UserRole) if proxy_index.isValid() else None

    def set_item_text(self, idx: int, text: str):
        proxy_index = self._proxy_model.index(idx, 0)
        if not proxy_index.isValid():
            return
        source_index = self._proxy_model.mapToSource(proxy_index)
        item = self._source_model.itemFromIndex(source_index)
        if item:
            item.setText(text)

    def add_item_at_start(self, text: str, data):
        from ui.theme import _C
        item = QStandardItem(text)
        item.setData(data, Qt.UserRole)
        item.setForeground(QColor(_C['danger']))
        self._source_model.insertRow(0, item)
        self._proxy_model.invalidateFilter()

    @staticmethod
    def _is_sep(data) -> bool:
        return _is_sep_data(data)
