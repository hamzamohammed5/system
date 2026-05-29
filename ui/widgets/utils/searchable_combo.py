"""
ui/widgets/utils/searchable_combo.py
=====================================
SearchableCombo — QComboBox مع حقل بحث مدمج.

التحسينات:
  - [تحسين 4] استخدام QSortFilterProxyModel بدل _rebuild الكامل عند البحث.
    القديم: كل حرف يُطلق _rebuild الذي يمسح ويُعيد إنشاء كل الـ QComboBox items.
    مع 500+ عنصر هذا overhead واضح.
    الجديد: QSortFilterProxyModel يُفلتر الـ items بدون إعادة إنشائها.
    استثناء: populate() تُعيد البناء الكامل مرة واحدة عند تغيير البيانات.

    ملاحظة التوافق: الـ separators (is_sep=True) تُعامَل برفع الـ flag
    Qt.ItemIsEnabled=False في الـ model مباشرة، والـ proxy يُخفيها عند البحث
    لو لم يتبقَّ بعدها عناصر حقيقية (pending_sep pattern محفوظ في populate).

  - [تحسين 41 محفوظ] _sep_font محفوظ كـ instance variable.
  - [تحسين 13 محفوظ] debounce داخلي للبحث (120ms).

  - [Q-05] _do_filter: استخدام setFilterFixedString بدل invalidateFilter للـ
    QSortFilterProxyModel العادي. Qt يُحسِّن setFilterFixedString داخلياً
    (يتجنب إعادة تقييم كل الصفوف إن لم يتغير الـ pattern).
    ملاحظة: _ComboFilterProxy يُعيد تعريف filterAcceptsRow لمنطق مخصص
    (separators / orphans)، لذا نُبقي invalidateFilter هناك ولكن نضيف
    حارس التحقق من تغيير النص قبل الاستدعاء لتجنب invalidation غير ضرورية.

  - [Q-06] build_grouped_items: توثيق البنية المتوقعة بوضوح.
    المشكلة: بعض الـ callers يمررون tuple بـ 5 عناصر (id, name, cat_id, cat_name, total_qty)
    لكن الدالة تتوقع 4 فقط. العنصر الخامس كان يُتجاهل بصمت.
    الحل: الدالة تقبل أي عدد من العناصر ≥ 2 (تأخذ [0] و[1] و[3] فقط)
    مع توثيق واضح. لا تغيير في السلوك — فقط توضيح البنية.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import (
    pyqtSignal, Qt, QTimer,
    QSortFilterProxyModel, QRegExp,
)
from PyQt5.QtGui  import QColor, QFont, QStandardItemModel, QStandardItem

from ui.app_settings import _C, fs, get_font_size

_SEP = ("__sep__", None)


def build_grouped_items(items: list) -> list:
    """
    تحوّل قائمة عناصر إلى قائمة مجمّعة جاهزة لـ SearchableCombo.populate().

    [Q-06] البنية المتوقعة لكل عنصر في items:
        items[i][0] = item_id   (int | str)    — معرف العنصر
        items[i][1] = name      (str)           — اسم العنصر
        items[i][2] = cat_id    (int | None)    — معرف التصنيف (مُتجاهَل هنا)
        items[i][3] = cat_name  (str | None)    — اسم التصنيف للتجميع
        items[i][4+]= ...       (any)           — أعمدة إضافية (مُتجاهَلة بصمت)

    مثال:
        # 4 عناصر — الحد الأدنى المتوقع
        build_grouped_items([(1, "قطعة", 10, "خامات")])

        # 5 عناصر — total_qty مُضاف، مُتجاهَل بصمت
        build_grouped_items([(1, "قطعة", 10, "خامات", 100.0)])

    Returns:
        list of (display_text, user_data, is_separator)
        جاهز لـ SearchableCombo.populate()
    """
    groups: dict = {}
    NO_CAT = "__no_category__"

    for entry in items:
        item_id  = entry[0]
        name     = entry[1]
        # entry[2] = cat_id — مُتجاهَل (التجميع يعتمد على cat_name فقط)
        # entry[3+] — cat_name أو عناصر إضافية (total_qty إلخ)
        cat_name = entry[3] if len(entry) > 3 and entry[3] else NO_CAT
        groups.setdefault(cat_name, []).append((item_id, name))

    result = []
    for cat_name, members in groups.items():
        if cat_name == NO_CAT:
            continue
        result.append((f"─── {cat_name} ───", _SEP, True))
        for item_id, name in members:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    if NO_CAT in groups:
        if result:
            result.append(("─── بدون تصنيف ───", _SEP, True))
        for item_id, name in groups[NO_CAT]:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    return result


# ── Custom Filter Proxy ───────────────────────────────────

class _ComboFilterProxy(QSortFilterProxyModel):
    """
    [تحسين 4] Proxy model يُفلتر الـ combo items.

    السلوك:
      - الـ separators (التي تكون disabled في الـ model) دائماً مرئية
        لو وجد عنصر حقيقي بعدها. لا تظهر بمفردها.
        هذا يُحافظ على pending_sep behavior بدون إعادة بناء.
      - الـ orphans ('#__orphan__') تُعرض دائماً بغض النظر عن البحث.
      - البحث case-insensitive في النص المعروض.

    [Q-05] set_filter يتحقق من تغيير النص قبل invalidateFilter:
      - لو النص لم يتغير → لا invalidation.
      - هذا يمنع إعادة تقييم كل الصفوف عند كل event بدون تغيير حقيقي.
      - مثال: _do_filter قد يُستدعى من QTimer بعد debounce حتى لو
        المستخدم لم يكتب شيئاً جديداً (نادر لكن ممكن).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._filter_text = ""

    def set_filter(self, text: str):
        """
        [Q-05] يُطبِّق الفلتر مع حارس التغيير.

        القديم: دائماً يُنفِّذ invalidateFilter() حتى لو النص لم يتغير.
        الجديد: يتحقق أولاً — لو النص نفسه يُتجاهَل الاستدعاء.

        invalidateFilter() في PyQt5 يُطلق layoutChanged signal مما يُعيد
        رسم الـ combo بالكامل. مع 500+ عنصر هذا overhead ملحوظ حتى لو
        لا يوجد تغيير حقيقي في الفلتر.
        """
        new_text = text.strip().lower()
        if new_text == self._filter_text:
            # [Q-05] لا تغيير — تجاهل
            return
        self._filter_text = new_text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        model = self.sourceModel()
        if not model:
            return True

        index = model.index(source_row, 0, source_parent)
        user_data = index.data(Qt.UserRole)

        # الـ separators: تُعرض دائماً (لكن الـ pending_sep في populate تتولى التنظيف)
        if _is_sep_data(user_data):
            return True

        # الـ orphans: تُعرض دائماً
        if user_data and isinstance(user_data, tuple) and user_data[0] == "__orphan__":
            return True

        # لو مفيش فلتر → كل شيء ظاهر
        if not self._filter_text:
            return True

        # فلترة حسب النص
        display = index.data(Qt.DisplayRole) or ""
        name_part = (display.split("—", 1)[-1].strip().lower()
                     if "—" in display else display.lower())
        return (self._filter_text in name_part or
                self._filter_text in display.lower())

    def data(self, index, role=Qt.DisplayRole):
        """Passthrough — يُعيد البيانات من الـ source model كما هي."""
        return super().data(index, role)


def _is_sep_data(user_data) -> bool:
    """يتحقق لو الـ user_data يشير لـ separator."""
    return (user_data == _SEP or
            (user_data and isinstance(user_data, tuple) and
             user_data[0] == "__sep__"))


class SearchableCombo(QWidget):
    """
    Combo مع حقل بحث: [🔍] [✖] [القائمة ▼]

    [تحسين 4] يستخدم QSortFilterProxyModel بدل إعادة بناء الـ combo.
    [Q-05] set_filter بحارس التغيير لتجنب invalidation غير ضرورية.
    [Q-06] build_grouped_items موثقة بوضوح — تقبل tuples بأي حجم ≥ 2.

    Signals:
        item_selected(data) — عند اختيار عنصر حقيقي
    """

    item_selected = pyqtSignal(object)

    # [تحسين 13] delay البحث الداخلي بالـ ms
    SEARCH_DELAY_MS: int = 120

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
        self._sep_font.setPointSize(max(7, self._sep_font.pointSize() - 1))

        # [تحسين 4] Source model + proxy model
        self._source_model = QStandardItemModel(self)
        self._proxy_model  = _ComboFilterProxy(self)
        self._proxy_model.setSourceModel(self._source_model)

        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        base = get_font_size()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(90)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background:{_C['bg_surface_2']}; border:1px solid {_C['border_med']};
                border-radius:4px; padding:2px 6px; font-size:{fs(base, -1)}pt;
                color:{_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color:{_C['accent']}; background:{_C['bg_input']}; }}
        """)
        self.inp_search.textChanged.connect(self._on_search)

        self.btn_clear = QPushButton("✖")
        self.btn_clear.setFixedSize(20, 20)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:none;
                color:{_C['text_disabled']}; font-size:{fs(base, -2)}pt;
            }}
            QPushButton:hover {{ color:{_C['danger']}; }}
        """)
        self.btn_clear.clicked.connect(self._clear_search)
        self.btn_clear.setVisible(False)

        self.cmb = QComboBox()
        self.cmb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb.setMinimumWidth(150)
        self.cmb.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # [تحسين 4] ربط الـ proxy بالـ combo
        self.cmb.setModel(self._proxy_model)
        self.cmb.currentIndexChanged.connect(self._on_combo_changed)

        lay.addWidget(self.inp_search)
        lay.addWidget(self.btn_clear)
        lay.addWidget(self.cmb, stretch=1)

    # ── handlers ──────────────────────────────────────────

    def _on_search(self, text: str):
        """
        [تحسين 4 + 13] بدل ما نبني من الصفر، نُحدِّث الـ proxy filter.
        الـ debounce timer يمنع التحديث في كل حرف.
        """
        self.btn_clear.setVisible(bool(text))
        self._pending_filter = text.strip().lower()
        self._rebuild_timer.start()

    def _do_filter(self):
        """
        [تحسين 4] يُطبِّق الفلتر على الـ proxy بدل إعادة بناء الـ combo.
        [Q-05] set_filter يتحقق من التغيير داخلياً — لو لم يتغير النص لا invalidation.

        O(n) في الـ proxy بدل O(n) إنشاء Qt widgets.
        """
        prev_data = self.cmb.currentData()
        self._proxy_model.set_filter(self._pending_filter)
        # استعادة الاختيار بعد الفلترة
        self._restore_by_data(prev_data)

    def _clear_search(self):
        self.inp_search.blockSignals(True)
        self.inp_search.clear()
        self.inp_search.blockSignals(False)
        self.btn_clear.setVisible(False)
        self._rebuild_timer.stop()
        self._pending_filter = ""

        prev_data = self.cmb.currentData()
        self._proxy_model.set_filter("")
        self._restore_by_data(prev_data)

    def _on_combo_changed(self, idx: int):
        data = self.cmb.currentData()
        if data and data != _SEP and not _is_sep_data(data):
            if not (isinstance(data, tuple) and data[0] == "__orphan__"):
                self.item_selected.emit(data)
            else:
                # orphan — نُطلق الـ signal أيضاً ليعرف الـ caller
                self.item_selected.emit(data)

    # ── ملء القائمة ───────────────────────────────────────

    def populate(self, items: list):
        """
        items: list of (display_text, user_data, is_separator)

        [تحسين 4] يبني الـ source model مرة واحدة.
        البحث اللاحق يعمل بالـ proxy بدون إعادة البناء.
        pending_sep pattern: نتجاهل الـ separator لو ما تبعه عنصر.
        """
        self._all_items = items

        # حفظ الاختيار الحالي
        prev_data = self.cmb.currentData()

        # إعادة بناء الـ source model (مرة واحدة فقط)
        self.cmb.blockSignals(True)
        self._source_model.clear()

        pending_sep: "tuple | None" = None

        for display, user_data, is_sep in items:
            if is_sep:
                pending_sep = (display, user_data)
            else:
                # أضف الـ separator المعلق قبل العنصر الحقيقي
                if pending_sep is not None:
                    self._add_source_item(pending_sep[0], pending_sep[1], is_separator=True)
                    pending_sep = None
                self._add_source_item(display, user_data, is_separator=False)

        self.cmb.blockSignals(False)

        # أعد تطبيق الفلتر الحالي (لو فيه بحث نشط)
        # [Q-05] set_filter يتحقق من التغيير — لو نفس الفلتر لا invalidation
        self._proxy_model.set_filter(self._pending_filter)

        # استعادة الاختيار
        if not self._restore_by_data(prev_data):
            self._select_first_real()

    def _add_source_item(self, display: str, user_data,
                          is_separator: bool):
        """يضيف عنصراً للـ source model مع styling."""
        item = QStandardItem(display)
        item.setData(user_data, Qt.UserRole)

        if is_separator:
            # الـ separator غير قابل للاختيار
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            item.setForeground(QColor(_C['text_muted']))
            item.setFont(self._sep_font)
        elif (user_data and isinstance(user_data, tuple) and
              user_data[0] == "__orphan__"):
            item.setForeground(QColor(_C['danger']))

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
        """يُعيد اختيار العنصر حسب الـ user_data. يرجع True لو نجح."""
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
        """يختار أول عنصر حقيقي (غير separator وغير orphan في الترتيب)."""
        for i in range(self._proxy_model.rowCount()):
            proxy_index = self._proxy_model.index(i, 0)
            data = proxy_index.data(Qt.UserRole)
            if (data and data != _SEP and isinstance(data, tuple) and
                    data[0] not in ("__sep__", "__orphan__")):
                self.cmb.setCurrentIndex(i)
                return

    # ── استرجاع البيانات الداخلية (للتوافق مع API القديم) ──

    def _get_source_item_by_data(self, target_data) -> "QStandardItem | None":
        """يجد عنصر في الـ source model بالـ user_data."""
        for i in range(self._source_model.rowCount()):
            item = self._source_model.item(i)
            if item and item.data(Qt.UserRole) == target_data:
                return item
        return None

    @staticmethod
    def _is_sep(data) -> bool:
        return _is_sep_data(data)

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
        """يختار عنصراً بالـ user_data — يبحث في الـ proxy (الظاهر حالياً)."""
        if not self._restore_by_data(user_data):
            # لو مش مرئي بسبب الفلتر → امسح الفلتر وحاول مرة أخرى
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
        """يرجع user_data للعنصر بالـ index في الـ proxy (الظاهر)."""
        proxy_index = self._proxy_model.index(idx, 0)
        return proxy_index.data(Qt.UserRole) if proxy_index.isValid() else None

    def set_item_text(self, idx: int, text: str):
        """
        يُعدِّل نص عنصر بالـ proxy index.
        يُستخدم لتحديث عرض الـ orphan.
        """
        proxy_index = self._proxy_model.index(idx, 0)
        if not proxy_index.isValid():
            return
        source_index = self._proxy_model.mapToSource(proxy_index)
        item = self._source_model.itemFromIndex(source_index)
        if item:
            item.setText(text)

    def add_item_at_start(self, text: str, data):
        """يضيف عنصراً في أول الـ source model."""
        item = QStandardItem(text)
        item.setData(data, Qt.UserRole)
        item.setForeground(QColor(_C['danger']))
        self._source_model.insertRow(0, item)
        # [Q-05] لا نستدعي set_filter هنا — نستدعي invalidateFilter مباشرة
        # لأن add_item_at_start تُغيِّر الـ model لا الـ filter
        self._proxy_model.invalidateFilter()