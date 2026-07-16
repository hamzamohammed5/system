"""
ui/tabs/costing/raw/raw_table_panel.py
========================================
RawTablePanel — جدول الخامات مع دعم العناصر المشتركة/المنشورة.

يرث من BaseListPanel + SharedOpsMixin.
- لا بناء جدول يدوي
- لا _load / _apply_filter يدوي
- كل shared logic عبر SharedOpsMixin

[Feature] عمود expand: زرار سهم في أول كل صف بيفتح/يقفل صف فرعي تحته
      فيه mini-جدول لعرض variants الخامة (للقراءة فقط). الزرار بيبان
      بس للخامات المحلية اللي عندها variants فعلاً — العناصر المشتركة
      مالهاش زرار خالص (item_id بتاعها من قاعدة بيانات شركة تانية).
"""

from PyQt5.QtGui  import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTableWidgetItem,
)

from ui.widgets.base.list_panel        import BaseListPanel
from ui.widgets.mixins.shared_ops      import SharedOpsMixin
from ui.widgets.tables.tables          import (
    make_item, colored_item, make_table, refresh_table_styles,
    make_splitter_table_guarded, fit_splitter_table,
)
from ui.widgets.components.button      import make_btn
from ui.widgets.dialogs.confirm        import confirm_delete          # ✅ كان: ui.helpers
from ui.widgets.core.events            import emit_company_data_changed
from ui.widgets.core.i18n              import tr
from ui.tabs.costing.shared._utils     import (
    to_dict, SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG,
)
from ui.tabs.companies.shared_items_mixin import (
    get_shared_raws, get_published_local_names, is_shared_id,
)
from services.costing.variant_service  import VariantService
from ui.theme                          import _C


# ارتفاع الصف الفرعي (شاشة الـ variants المصغّرة) بالبكسل
_VARIANTS_SUBROW_H = 130


class RawTablePanel(BaseListPanel, SharedOpsMixin):
    """
    جدول الخامات — يرث من BaseListPanel.

    BaseListPanel يوفر:
      - بناء الجدول
      - FilterBar (بحث + تصنيف)
      - _load / _apply_filter
      - section label
      - bus.data_changed auto-connect
    """

    COLUMNS            = ["", tr("raw_col_id"), tr("raw_col_name"), tr("raw_col_category"),
                           tr("raw_col_total_price"), tr("raw_col_qty"), tr("raw_col_unit_price"),
                           tr("raw_col_actions")]
    # [توحيد الجداول] STRETCH_COL = -1 بدل 1 — الالتزام بالنمط الموحّد
    # لكل الجداول في المشروع (نفس _orders_list_panel.py). لما STRETCH_COL
    # بيتحدد بعمود معين مع باقي الأعمدة Interactive، الـ header بيتصرف
    # بشكل معكوس بصريًا في RTL (سحب حد عمود بيحرك الأعمدة التانية بعكس
    # الاتجاه). الحل الموحّد: -1 يخلي كل الأعمدة Interactive حرة +
    # stretchLastSection=True ياخد الفراغ الباقي، وده السلوك السليم.
    #
    # [تصحيح] كانت اتغيّرت لـ 2 بالغلط في محاولة سابقة لحل مشكلة عرض
    # الجدول — ده خطأ ومخالف للقاعدة الإلزامية في هذا المشروع. رجّعناها
    # -1. مشكلة "الجدول مش بياخد عرض كافي" ليها حل مختلف تمامًا (توسيع
    # حساب fit_splitter_table نفسها في list_panel.py)، مش عن طريق كسر
    # قاعدة STRETCH_COL.
    STRETCH_COL        = -1
    # [Fix - عمود ID/الاسم بيتقص] عمود 1 (ID) وعمود 2 (الاسم) طول
    # نصهم متغيّر (اسم خامة ممكن يطول) فمحتاجين سقف أعلى من
    # COL_MAX_WIDTH العام. لاحظ إنه سقف محدود مش None (بلا سقف
    # خالص) — لو صف واحد بس (حتى شير مشترك من شركة تانية) عنده
    # اسم طويل جدًا/غير طبيعي، لازم الجدول يوقف عند حد معقول ويسيب
    # المستخدم يوسّع العمود يدويًا لو حابب، مش يمدد الجدول كله لعرض
    # ضخم يطلعله scrollbar أفقي. راجع تعليق COL_MAX_WIDTHS في
    # list_panel.py للتفاصيل الكاملة.
    COL_MAX_WIDTHS     = {1: 90, 2: 260}
    EMPTY_ICON         = tr("raw_empty_icon")
    EMPTY_TITLE        = tr("no_raws")
    LIST_TITLE         = tr("raw_table_list_title")
    ADD_TEXT           = ""
    SHOW_CATEGORY      = True
    FILTER_SCOPE       = "raw"
    # [Fix] شلنا القيمة الصريحة لعمود 0 (كانت {0: 32, ...}) — كانت
    # استثناء يدوي بيخلي عمود الـ expand يتصرف مختلف عن باقي الأعمدة.
    # دلوقتي عمود 0 بياخد عرضه الابتدائي من TABLE_COL_DEFAULT_W زي أي
    # عمود من غير قيمة صريحة، وبعدين auto_fit_columns بتظبطه تلقائيًا
    # من محتواه الفعلي (نفس آلية أي عمود تاني في الجدول، بدون تمييز).
    COL_WIDTHS         = {1: 45, 3: 110, 4: 90, 5: 90, 6: 95, 7: 90}
    CONNECT_BUS        = True

    def __init__(self, conn, input_panel=None, parent=None):
        self._input_panel      = input_panel
        self._published_names  = set()
        # [Feature] item_id مفتوحة حاليًا (صف الـ variants ظاهر تحتها) —
        # set بدل bool واحد عشان تدعم فتح أكتر من صف في نفس الوقت.
        self._expanded_ids: set = set()
        # item_id → count الـ variants (0 = مفيش، فالزرار محتجب).
        # بيتحسب دفعة واحدة في _load_rows عشان نتجنب query لكل صف
        # وقت الرسم (_fill_row بتتنفذ لكل صف/كل refresh).
        self._variant_counts: dict = {}
        super().__init__(conn, parent)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        from dataclasses import asdict
        from services.shared.item_service import ItemService
        local_rows = [asdict(r) for r in ItemService(self.conn).list_by_type("raw")]
        self._published_names = get_published_local_names("raw")
        shared_rows = get_shared_raws(local_rows)

        # [Feature] زرار عرض الـ variants بيبان للخامات المحلية بس.
        # العناصر المشتركة (shared_rows) ممكن يكون item_id بتاعها من
        # قاعدة بيانات شركة تانية غير self.conn الحالي — فـ
        # VariantService(self.conn) مش هيقدر يجيب variants صحيحة ليها
        # أصلاً. بدل ما نعرض بيانات غلط أو نعمل query عبر قواعد بيانات
        # متعددة، بنفصل بوضوح: الـ variants المعروضة هنا محلية فقط.
        svc = VariantService(self.conn)
        counts = {}
        for row in local_rows:
            item_id = row.get("id")
            if item_id is None:
                continue
            try:
                counts[item_id] = len(svc.list(item_id))
            except Exception:
                counts[item_id] = 0
        self._variant_counts = counts

        return local_rows + shared_rows

    # ══════════════════════════════════════════════════════
    # تحديث تلقائي عند تغيّر بيانات الشركة
    # ══════════════════════════════════════════════════════
    # [FIX] WidgetMixin._on_data_change بينادي self._refresh_data(company_id)
    # عند bus.company_data_changed — مش self.refresh().
    # BaseListPanel معرّفش _refresh_data (الافتراضي في WidgetMixin no-op)،
    # فكان الجدول مش بيتحدث بعد فك ربط عنصر مشترك (unlink_from_company) —
    # علامة 🔗 كانت تفضل ظاهرة لحد ما حاجة تانية تعمل refresh() كامل بالصدفة
    # (زي حذف العنصر من كل الشركات).
    # الحل: تعريف _refresh_data هنا لينادي self.refresh() الموروثة من
    # BaseListPanel، واللي بتعيد _load_rows() (وبالتالي get_published_local_names)
    # وتطبّق الفلتر من جديد.
    def _refresh_data(self, company_id=None):
        self.refresh()

    # ══════════════════════════════════════════════════════
    # ملء الجدول
    # ══════════════════════════════════════════════════════

    def _fill_row(self, table, r: int, row: dict):
        from models.costing_base import raw_unit_price

        is_shared    = row.get("_is_shared", False) or row.get("is_shared", False)
        is_published = (
            not is_shared and
            str(row.get("name", "")).strip().lower() in self._published_names
        )

        prefix = tr("table_shared_prefix") if is_shared else (tr("table_published_prefix") if is_published else "")
        color = (
                SHARED_COLOR()    if is_shared    else
                PUBLISHED_COLOR() if is_published else
                None
            )

        tq     = row.get("total_qty")
        price  = float(row.get("price", 0))
        unit   = (price / float(tq)) if (tq and float(tq) > 0 and is_shared) \
                 else raw_unit_price(row)

        # [Feature] عمود 0 — زرار expand (سهم) — يتضاف كـ cell widget
        # بعد ما نملى باقي الأعمدة، عشان يعرف حالة الفتح الحالية.
        item_id = row.get("id")

        # [Fix] عمود الـ ID (عمود 1) كان بيتستبدل بالكامل بأيقونة نصية
        # (table_shared_icon / table_published_icon) للعناصر المشتركة/
        # المنشورة، وهي نص يونيكودي عادي مش مضمون الدعم في كل الفونتات
        # (نفس علة سهم الـ expand ▼/▶ اللي كانت بتظهر مربع فاضي). لكن
        # المشكلة الأعمق: حتى لو الرمز كان ظاهر، كان بيخفي الـ ID الفعلي
        # للعنصر بالكامل — والمستخدم هنا محتاج الرقم يفضل ظاهر دايمًا في
        # عمود الـ ID (تمييز العنصر المشترك/المنشور بيتم أصلاً عن طريق
        # الـ prefix + اللون على عمود الاسم، مش لازم يتكرر بإخفاء الرقم).
        # الحل: عمود الـ ID بيعرض str(id) دايمًا بغض النظر عن is_shared/
        # is_published.
        id_text = str(row.get("id", ""))
        id_item = make_item(id_text, user_data=row.get("id"))
        table.setItem(r, 1, id_item)
        table.setItem(r, 2, colored_item(prefix + row.get("name", ""), color=color))
        table.setItem(r, 3, colored_item(row.get("category_name") or tr("dash"), color=color))
        table.setItem(r, 4, colored_item(f"{price:.2f}", color=color))
        table.setItem(r, 5, colored_item(str(tq) if tq is not None else tr("dash"), color=color))
        table.setItem(r, 6, colored_item(f"{unit:.4f}", color=color))

        if color:
            bg = SHARED_BG() if is_shared else PUBLISHED_BG()
            for col in range(1, table.columnCount()):
                itm = table.item(r, col)
                if itm:
                    itm.setBackground(QColor(bg))
                    itm.setForeground(QColor(color))

        self._fill_expand_cell(table, r, row, is_shared)
        self._fill_actions_cell(table, r, row, is_shared)

    def _fill_expand_cell(self, table, r: int, row: dict, is_shared: bool):
        """
        يبني خلية عمود 0 — زرار سهم بسيط لفتح/قفل صف variants الخامة.
        بيبان بس للخامات المحلية (مش المشتركة) اللي عندها variants
        فعلاً (self._variant_counts[item_id] > 0).

        [Fix] الزرار بيستخدم icon="chevron_right"/"chevron_down" من
        ICON_PATHS في button.py (SVG مرسوم بالكود) بدل النص اليونيكودي
        ▼/▶ اللي كان بيتقص أو يبان كمربع/حرف غريب في بعض الفونتات.
        مع compact=True عشان حجم الزرار (مربع بالكامل) يتحسب من قياس
        الأيقونة الفعلي + هامش صغير ثابت، مش من منطق زرار نص عادي
        (اللي كان بيدّي عرض/ارتفاع أكبر بكتير من اللازم لمجرد سهم).
        كمان شلنا lay.addStretch() القديمة — كانت بتوسّع الـ cell
        widget نفسه (مش الزرار) عشان يملأ عرض العمود بالكامل، فكان
        العمود يبان أعرض من الزرار حتى لو الزرار نفسه صغير ومظبوط.
        دلوقتي الـ cell widget بياخد حجمه من محتواه الفعلي بس (الزرار)،
        و auto_fit_columns هي اللي بتحدد عرض العمود من sizeHint بتاع
        الـ cell widget ده.
        """
        item_id = row.get("id")
        has_variants = (not is_shared) and self._variant_counts.get(item_id, 0) > 0

        if not has_variants:
            table.setItem(r, 0, make_item(""))
            return

        is_open = item_id in self._expanded_ids
        cell = QWidget()
        lay  = QHBoxLayout(cell)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(0)

        icon_key = "chevron_down" if is_open else "chevron_right"
        btn = make_btn(style="ghost", icon=icon_key, compact=True)
        btn.setToolTip(tr("raw_variants"))
        btn.clicked.connect(lambda _=False, iid=item_id: self._toggle_variants_row(iid))
        # [Fix] الزرار كان بيبان ممتد عموديًا لملء ارتفاع الصف الكامل
        # (ROW_HEIGHT_LARGE) رغم إن make_btn بتعمل setFixedSize(side,side)
        # + setSizePolicy(Fixed,Fixed) — QHBoxLayout من غير alignment
        # صريح على الـ widget بيمدده أحيانًا ليملأ المساحة العمودية
        # المتاحة في الـ layout، حتى مع size policy مربوطة. تحديد
        # AlignCenter صراحة هنا يجبر الـ layout يحترم حجم الزرار
        # الحقيقي (side×side) ويحطه في المنتصف بدل ما يمدده.
        lay.addWidget(btn, alignment=Qt.AlignCenter)

        table.setCellWidget(r, 0, cell)

        # [Feature] لو الصف ده متفتح فعلاً (من قبل الـ refresh)، نضيف
        # الصف الفرعي بتاعه فورًا بعد صف الخامة نفسه — بيستخدم rowCount()
        # الحالي كمرجع، فمينفعش نستخدم r القادم من _fill_row مباشرة
        # (ده أصلاً r الحالي بتاع صف الخامة، مش صف جديد).
        if is_open:
            self._insert_variants_subrow(table, item_id)

    def _toggle_variants_row(self, item_id: int):
        """
        يفتح/يقفل صف الـ variants الفرعي تحت صف الخامة المحدد.
        بيعيد بناء الجدول كامل عبر _apply_filter() عشان نضمن ترتيب
        صحيح للصفوف — أرخص وأبسط من محاولة إدراج/حذف صف واحد يدويًا
        وسط جدول ممكن يكون فيه صفوف فرعية تانية مفتوحة بالفعل.
        """
        if item_id in self._expanded_ids:
            self._expanded_ids.discard(item_id)
        else:
            self._expanded_ids.add(item_id)
        self._apply_filter()

    def _insert_variants_subrow(self, table, item_id: int):
        """
        يدرج صف فرعي مباشرة بعد صف الخامة الحالي (آخر صف مُدرَج في
        الجدول لحظة الاستدعاء)، ويملأه بـ mini-جدول variants للقراءة فقط
        (splitter + جدول + spacer، نفس نمط الجدول الرئيسي).

        [Fix] السبب الحقيقي لتمدد عمود الـ expand: setSpan كانت بتبدأ
        من عمود 0 نفسه (نفس عمود الزرار) وتمتد لكل الأعمدة. عمود 0
        بالتالي كان "يملك" جزء من الخلية الممتدة الواسعة دي من ناحية
        Qt الداخلية، فلما auto_fit_columns بتحسب ResizeToContents لعمود
        0 على مستوى الجدول كله، كانت بتاخد بالها من عرض المحتوى الواسع
        ده وتوسع العمود بناءً عليه — حتى مع إخفاء الزرار الفعلي في
        صفوف تانية. الحل: نخلي الامتداد يبدأ من عمود 1 (مش 0)، فعمود
        الـ expand بيفضل بره نطاق الـ span تمامًا في كل الصفوف — خلية
        عادية زي أي عمود تاني، من غير أي تأثير من محتوى الصف الفرعي.
        عمود 0 في صف الـ variants نفسه بيتسيب فاضي (مفيش زرار فيه أصلاً،
        الصف ده مش خامة).
        """
        sub_r = table.rowCount()
        table.insertRow(sub_r)
        table.setRowHeight(sub_r, _VARIANTS_SUBROW_H)
        table.setItem(sub_r, 0, make_item(""))

        mini_splitter, mini_table = self._build_variants_mini_table(item_id)

        container = QWidget()
        outer = QHBoxLayout(container)
        outer.setContentsMargins(24, 4, 24, 4)
        outer.addWidget(mini_splitter)

        table.setSpan(sub_r, 1, 1, table.columnCount() - 1)
        table.setCellWidget(sub_r, 1, container)

    def _build_variants_mini_table(self, item_id: int):
        """
        mini-جدول للقراءة فقط بعرض variants الخامة — نفس أدوات البناء
        المركزية (make_splitter_table_guarded) بنمط compact، بدون أي
        إمكانية تعديل/حذف من هنا (التعديل الفعلي بيتم من فورم الخامة
        نفسه).

        [Fix] كانت مبنية بـ make_table() المفردة — دي بتفعّل
        hh.setStretchLastSection(True) تلقائيًا لما stretch_col=-1
        (نفس سلوك _build_table العادي)، وبما إنها مش جوه splitter+spacer
        زي بقية جداول المشروع، آخر عمود ("التكلفة للوحدة") كان بيتمدد
        لعرض الـ container كامل بدل ما ياخد عرضه الطبيعي بس — مخالف
        لقاعدة "عرض الجدول = مجموع عروض أعمدته الفعلية + spacer" في
        ملف التوحيد. الحل: نبني الـ mini كـ splitter+جدول+spacer زي
        الجدول الرئيسي بالظبط (make_splitter_table_guarded)، فالفراغ
        الزيادة بيروح لـ spacer شفاف مش لعمود التكلفة.
        بترجع (splitter, table) — الـ splitter هو اللي بيتحط في الـ
        container، والـ table نفسها بترجع منفصلة لو احتجنا نملاها.
        """
        price = 0.0
        try:
            from services.shared.item_service import ItemService
            result = ItemService(self.conn).get(item_id)
            if result:
                price = float(result.price)
        except Exception:
            pass

        mini_splitter, mini, _guard = make_splitter_table_guarded(
            columns=[tr("name"), tr("pieces_count"), tr("cost_per_unit")],
            stretch_col=-1,
            max_height=_VARIANTS_SUBROW_H - 16,
            min_height=0,
            row_height=None,
            variant="compact",
        )
        mini.setProperty("_table_variant", "compact")
        # [إصلاح ثيم] refresh_table_styles() بتدور على findChildren بس —
        # الجدول هنا مش موجود في شجرة widgets الرئيسية وقت بنائه، فبنطبق
        # الستايل مباشرة وقت الإنشاء (نفس ما كان معمول قبل كده).
        from ui.widgets.theme.table_styles import table_style
        mini.setStyleSheet(table_style("compact"))

        try:
            variants = VariantService(self.conn).list(item_id)
        except Exception:
            variants = []

        for var in variants:
            r = mini.rowCount()
            mini.insertRow(r)
            mini.setItem(r, 0, make_item(var.name))
            mini.setItem(r, 1, make_item(f"{var.pieces:,.4g}", align=Qt.AlignCenter))
            unit_cost = var.calc_unit_cost(price)
            cost_text = f"{unit_cost:.4f}  {tr('currency_abbr')}" if var.pieces > 0 and price > 0 \
                        else tr("amount_dash_placeholder")
            mini.setItem(r, 2, colored_item(cost_text, _C["accent"], align=Qt.AlignCenter))

        # [Fix] الجدول الرئيسي بياخد auto_fit_columns تلقائيًا من جوه
        # BaseListPanel._fill_table بعد كل تعبئة بيانات — الـ mini هنا
        # جدول منفصل تمامًا (مالوش BaseListPanel يديره)، فكان بيفضل
        # بعرض الأعمدة الافتراضي من _build_table (TABLE_COL_DEFAULT_W)
        # بدل ما يتظبط من محتواه الفعلي زي أي عمود في الجدول الرئيسي.
        # ده سبب إن عمود "كلفة للوحدة" كان مش بياخد عرض نصه الفعلي.
        # نفس الاستدعاء المستخدم في _auto_resize الأصلية في BaseListPanel.
        from ui.widgets.tables.tables import auto_fit_columns
        from ui.constants import COL_MIN_WIDTH, COL_MAX_WIDTH
        auto_fit_columns(
            mini, fixed_cols=list(range(mini.columnCount())),
            stretch_col=-1, min_width=COL_MIN_WIDTH, max_width=COL_MAX_WIDTH,
        )
        # [Fix] setStretchLastSection(True) بتتفعّل تلقائيًا جوه
        # _build_table لما stretch_col=-1 (نفس أي جدول بـ stretch_col=-1
        # في المشروع) — مفيدة للجدول الرئيسي لأنه بياخد الفراغ من
        # الـ splitter، لكن هنا بتخلي آخر عمود ("التكلفة للوحدة") يمتد
        # ليملأ أي فراغ داخل عرض الجدول نفسه بعد auto_fit_columns، بغض
        # النظر عن وجود الـ spacer الخارجي في mini_splitter — لأن
        # stretchLastSection بتشتغل على مستوى الـ header نفسه، مش
        # علاقة له بالـ splitter المحيط. نعطّلها صراحة هنا زي
        # make_fixed_table بالظبط، عشان عرض الجدول = مجموع عروض
        # أعمدته الفعلية فقط، والفراغ الزيادة يروح لـ spacer الشفاف.
        mini.horizontalHeader().setStretchLastSection(False)

        # [Fix] fit_splitter_table كانت بتتنادى هنا فورًا وقت الإنشاء —
        # في اللحظة دي mini_splitter لسه مش متحط جوه container ولا
        # ظاهر على الشاشة، فـ splitter.width() بيرجع صفر أو قيمة
        # افتراضية وهمية. النتيجة: fit_splitter_table كانت بتحسب
        # remaining = max(0, 0 - table_w) = 0 وبتدّي حجم بداية غلط
        # تمامًا للـ splitter، فعمود "كلفة للوحدة" (آخر عمود) كان بيبان
        # ممتد لعرض الـ container كامل بدل عرضه الطبيعي.
        # الحل: delay_ms المُعرّفة أصلاً في fit_splitter_table (بتستخدم
        # QTimer.singleShot داخليًا) بالظبط لغرض زي ده — نأجّل التنفيذ
        # لحد ما الـ event loop تخلص الدورة الحالية والـ widget يتحط
        # فعليًا في شجرة العرض (بعد ما الـ container يتضاف بـ
        # setCellWidget في المستدعي) ويتاخد حجمه الحقيقي.
        fit_splitter_table(mini_splitter, mini, delay_ms=1)

        return mini_splitter, mini

    def _fill_actions_cell(self, table, r: int, row: dict, is_shared: bool):
        """
        يبني خلية أزرار (تعديل/حذف) في عمود الأكشنز الأخير، باستخدام
        make_btn من button.py — نفس المصنع الموحد المستخدم في باقي التطبيق،
        بدل QPushButton خام بلا ستايل.

        العناصر المشتركة: زر الحذف مُعطَّل (الحذف الحقيقي بيتم من شاشة
        إدارة العناصر المشتركة، و_on_delete_item بترفضه أصلاً لو ضُغط).
        """
        item_id = row.get("id")

        cell = QWidget()
        lay  = QHBoxLayout(cell)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(4)

        btn_edit = make_btn(tr("btn_edit_short"), style="normal", fixed_size=True)
        btn_edit.setToolTip(tr("btn_edit"))
        btn_edit.clicked.connect(lambda _=False, iid=item_id: self._on_edit_item(iid))
        lay.addWidget(btn_edit)

        btn_delete = make_btn(tr("btn_delete_short"), style="danger", fixed_size=True)
        btn_delete.setToolTip(tr("btn_delete"))
        if is_shared:
            btn_delete.setEnabled(False)
        else:
            name = row.get("name", "")
            btn_delete.clicked.connect(
                lambda _=False, iid=item_id, nm=name: self._on_delete_item(iid, nm)
            )
        lay.addWidget(btn_delete)

        lay.addStretch()
        table.setCellWidget(r, 7, cell)

    # ══════════════════════════════════════════════════════
    # فلترة مخصصة (يدعم shared rows)
    # ══════════════════════════════════════════════════════

    def _match_filter(self, row: dict, query: str) -> bool:
        name = row.get("name", "")
        cat  = row.get("category_id")
        return self._filter.match(name, cat) if hasattr(self, "_filter") \
               else query.lower() in name.lower()

    # ══════════════════════════════════════════════════════
    # [Fix] override لـ selected_id / _on_select / select_item
    # ══════════════════════════════════════════════════════
    # BaseListPanel بتفترض إن الـ ID محفوظ كـ Qt.UserRole في عمود 0
    # دايمًا (selected_id, _on_select, select_item كلهم بيقروا من
    # table.item(row, 0)). بعد إضافة عمود الـ expand، عمود 0 بقى فاضي
    # أو فيه زرار السهم (cell widget بدون QTableWidgetItem عليه
    # user_data)، وعمود 1 هو اللي فيه الـ ID دلوقتي. الثلاث دوال دول
    # لازم يتقروا من عمود 1 بدل 0 عشان يفضلوا شغالين صح (تحديد صف،
    # فتح خامة بالضغط عليها من مكان تاني، إلخ).
    def selected_id(self) -> "int | None":
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 1)
        if item:
            data = item.data(Qt.UserRole)
            return int(data) if data is not None else None
        return None

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 1)
        if item:
            data = item.data(Qt.UserRole)
            if data is not None:
                self.item_selected.emit(int(data))

    def select_item(self, item_id: int):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.data(Qt.UserRole) == item_id:
                self.table.selectRow(r)
                self.item_selected.emit(item_id)
                return
        # [Fix] ماينفعش ننده super().select_item() هنا — النسخة الأصلية في
        # BaseListPanel بتدور بعمود 0 (item(r, 0)) على كل صفوف الجدول بما
        # فيها صفوف الـ variants الفرعية (اللي عمود 0 فيها cellWidget مدموج
        # بـ setSpan مش QTableWidgetItem). لو العنصر مش موجود بعمود 1،
        # مفيش داعي نكرر بحث هيفشل أو ممكن يلخبط التحديد.

    # ══════════════════════════════════════════════════════
    # أزرار إضافية
    # ══════════════════════════════════════════════════════

    def _build_extra_header_actions(self, header):
        header.add_action(tr("raw_bulk_replace_btn"),  self._bulk_replace,     "primary")
        header.add_action(tr("raw_edit_shared_btn"), self._edit_shared_selected)
        header.add_action(tr("raw_publish_btn"),    self._publish_selected)

    # ══════════════════════════════════════════════════════
    # إجراءات الأزرار
    # ══════════════════════════════════════════════════════

    def _on_add_clicked(self):
        pass

    def _on_row_double_clicked(self, item_id):
        if self._input_panel and not is_shared_id(item_id):
            self._input_panel.load_for_edit(int(item_id))

    def _bulk_replace(self):
        from PyQt5.QtWidgets import QMessageBox
        from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog

        item_id = self.selected_id()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("raw_select_first"))
            return
        if is_shared_id(item_id):
            QMessageBox.information(self, tr("warning"),
                                    tr("raw_bulk_replace_not_available"))
            return
        row = self._get_current_row_dict()
        name = row.get("name", f"ID:{item_id}") if row else f"ID:{item_id}"
        BulkReplaceDialog(
            conn=self.conn, child_type="raw",
            child_id=int(item_id), child_name=name, parent=self,
        ).exec_()

    def _edit_shared_selected(self):
        from PyQt5.QtWidgets import QMessageBox
        item_id = self.selected_id()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("raw_select_first"))
            return
        self._edit_shared_item(item_id, "raw", self)

    def _publish_selected(self):
        from PyQt5.QtWidgets import QMessageBox
        item_id = self.selected_id()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("raw_select_first"))
            return
        row = self._get_current_row_dict()
        if not row:
            return
        item_data = {
            "price":         float(row.get("price", 0.0)),
            "total_qty":     row.get("total_qty"),
            "category_name": row.get("category_name") or None,
        }
        self._publish_item(row, "raw", item_data, self)

    # ══════════════════════════════════════════════════════
    # تعديل / حذف
    # ══════════════════════════════════════════════════════

    def _on_edit_item(self, item_id):
        from PyQt5.QtWidgets import QMessageBox
        if is_shared_id(item_id):
            QMessageBox.information(
                self, tr("shared_item_title"),
                tr("raw_shared_edit_notice")
            )
            return
        if self._input_panel:
            self._input_panel.load_for_edit(int(item_id))

    def _on_delete_item(self, item_id, item_name: str):
        from PyQt5.QtWidgets import QMessageBox
        from services.shared.item_service import ItemService

        if is_shared_id(item_id):
            QMessageBox.warning(
                self, tr("shared_item_title"),
                tr("raw_shared_delete_blocked")
            )
            return
        item_id_int = int(item_id)
        if (self._input_panel and
                getattr(self._input_panel, "is_editing", False) and
                getattr(self._input_panel, "_editing_id", None) == item_id_int):
            self._input_panel._reset()
        if confirm_delete(self, item_name):
            try:
                deleted = ItemService(self.conn).delete(item_id_int)
            except Exception as e:
                QMessageBox.warning(self, tr("error"), str(e))
                return
            if not deleted:
                return
            emit_company_data_changed()

    # ══════════════════════════════════════════════════════
    # مساعد
    # ══════════════════════════════════════════════════════

    def _get_current_row_dict(self) -> dict | None:
        item_id = self.selected_id()
        if item_id is None:
            return None
        for row in self._all_rows:
            if str(row.get("id")) == str(item_id):
                return row
        return None