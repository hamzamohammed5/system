"""
ui/tabs/costing/shared/bom_scenarios_panel.py
==================================
_BomScenariosPanel — لوحة إدارة سيناريوهات BOM.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedComboBox

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_XS, FS_SM, FS_LG
from ui.constants import (
    SCENARIOS_PANEL_H, SCENARIOS_PANEL_MARGIN_H, SCENARIOS_PANEL_MARGIN_V,
    SCENARIOS_PANEL_SPACING, SCENARIOS_PANEL_CMB_MIN_W, SCENARIOS_PANEL_CMB_MIN_H,
    SCENARIOS_PANEL_CMB_RADIUS, SCENARIOS_PANEL_CMB_PAD_V, SCENARIOS_PANEL_CMB_PAD_H,
    SCENARIOS_PANEL_BTN_MIN_H, SCENARIOS_PANEL_BTN_RADIUS, SCENARIOS_PANEL_BTN_PAD_V,
    SCENARIOS_PANEL_BTN_PAD_H, SCENARIOS_PANEL_FRAME_RADIUS,
    SCENARIOS_PANEL_BTN_DEFAULT_W, SCENARIOS_PANEL_BTN_RENAME_W,
    SCENARIOS_PANEL_BTN_CLONE_W, SCENARIOS_PANEL_BTN_ADD_W, SCENARIOS_PANEL_BTN_DEL_W,
)


from .bom_scenarios._memory_scenarios import MemoryScenariosMixin
from .bom_scenarios._db_scenarios     import DbScenariosMixin


class _BomScenariosPanel(QFrame, MemoryScenariosMixin, DbScenariosMixin, WidgetMixin):
    """
    لوحة أفقية تعرض السيناريوهات وتتيح التبديل بينها.

    Signals:
        scenario_changed(scenario_id) — يُطلق عند تغيير السيناريو الحالي
    """

    scenario_changed = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._item_id    = None
        self._scenarios  = []
        self._current_id = None
        self._in_memory  = True
        self._build()
        self._init_memory_scenario()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self.setFrameShape(QFrame.StyledPanel)
        self._apply_frame_style()
        self.setFixedHeight(SCENARIOS_PANEL_H)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(SCENARIOS_PANEL_MARGIN_H, SCENARIOS_PANEL_MARGIN_V,
                               SCENARIOS_PANEL_MARGIN_H, SCENARIOS_PANEL_MARGIN_V)
        lay.setSpacing(SCENARIOS_PANEL_SPACING)

        lbl_icon = QLabel(tr("scenarios_panel_target_icon"))
        lbl_icon.setStyleSheet(f"background:transparent; border:none; font-size:{FS_LG}px;")
        lay.addWidget(lbl_icon)

        lbl = QLabel(f"{tr('scenario')}:")
        lbl.setStyleSheet(
            f"font-weight:bold; font-size:{FS_SM}px; color:{_C['purple']};"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl)

        self.cmb_scenarios = ThemedComboBox()
        self.cmb_scenarios.setMinimumWidth(SCENARIOS_PANEL_CMB_MIN_W)
        self.cmb_scenarios.setMinimumHeight(SCENARIOS_PANEL_CMB_MIN_H)
        self._apply_combo_style()
        self.cmb_scenarios.currentIndexChanged.connect(self._on_scenario_changed)
        lay.addWidget(self.cmb_scenarios)

        self.lbl_default_badge = QLabel(f"{tr('scenarios_panel_star_badge')}{tr('default_scenario')}")
        self.lbl_default_badge.setStyleSheet(
            f"color:{_C['warning']}; font-weight:bold; font-size:{FS_XS}px;"
            "border:none; background:transparent;"
        )
        self.lbl_default_badge.setVisible(False)
        lay.addWidget(self.lbl_default_badge)

        lay.addStretch()

        self.btn_set_default = self._make_btn(
            f"{tr('scenarios_panel_btn_star_icon')}{tr('default_scenario')}", SCENARIOS_PANEL_BTN_DEFAULT_W,
            _C['warning_bg'], _C['warning'], _C['warning_border'], _C['warning_bg'],
        )
        self.btn_set_default.setToolTip(tr("set_as_default"))
        self.btn_set_default.clicked.connect(self._set_default)
        lay.addWidget(self.btn_set_default)

        btn_rename = self._make_btn(
            f"{tr('scenarios_panel_btn_edit_icon')}{tr('edit')}", SCENARIOS_PANEL_BTN_RENAME_W,
            _C['orange_bg'], _C['orange'], _C['orange_border'], _C['orange_bg'],
        )
        btn_rename.setToolTip(tr("rename_scenario"))
        btn_rename.clicked.connect(self._rename)
        lay.addWidget(btn_rename)

        btn_clone = self._make_btn(
            f"{tr('scenarios_panel_btn_clone_icon')}{tr('clone')}", SCENARIOS_PANEL_BTN_CLONE_W,
            _C['info_bg'], _C['info'], _C['info_border'], _C['info_bg'],
        )
        btn_clone.setToolTip(tr("clone_scenario"))
        btn_clone.clicked.connect(self._clone)
        lay.addWidget(btn_clone)

        btn_add = self._make_btn(
            f"{tr('scenarios_panel_btn_add_icon')}{tr('new')}", SCENARIOS_PANEL_BTN_ADD_W,
            _C['success_bg'], _C['success'], _C['success_border'], _C['success_bg'],
        )
        btn_add.setToolTip(tr("add_scenario"))
        btn_add.clicked.connect(self._add_new)
        lay.addWidget(btn_add)

        btn_del = self._make_btn(
            tr("scenarios_panel_btn_del_icon"), SCENARIOS_PANEL_BTN_DEL_W,
            _C['danger_bg'], _C['danger'], _C['danger_border'], _C['danger_bg'],
        )
        btn_del.setToolTip(tr("delete"))
        btn_del.clicked.connect(self._delete)
        lay.addWidget(btn_del)

    def _refresh_style(self, *_):
        """يُطبق الـ stylesheet عند تغيير الثيم أو حجم الخط."""
        self._apply_frame_style()
        if hasattr(self, "cmb_scenarios"):
            self._apply_combo_style()

    def _apply_frame_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['purple_bg']};
                border: 1px solid {_C['purple_border']};
                border-radius: {SCENARIOS_PANEL_FRAME_RADIUS}px;
            }}
        """)

    def _apply_combo_style(self):
        self.cmb_scenarios.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']};
                border: 1px solid {_C['purple_border']};
                border-radius: {SCENARIOS_PANEL_CMB_RADIUS}px;
                padding: {SCENARIOS_PANEL_CMB_PAD_V}px {SCENARIOS_PANEL_CMB_PAD_H}px;
                font-size: {FS_SM}px;
                color: {_C['purple']};
            }}
            QComboBox:focus {{ border-color: {_C['purple']}; }}
            QComboBox::drop-down {{ border: none; }}
        """)

    @staticmethod
    def _make_btn(text: str, width: int,
                  bg: str, fg: str, border: str, hover: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(SCENARIOS_PANEL_BTN_MIN_H)
        btn.setFixedWidth(width)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: {SCENARIOS_PANEL_BTN_RADIUS}px;
                font-size: {FS_XS}px;
                font-weight: bold;
                padding: {SCENARIOS_PANEL_BTN_PAD_V}px {SCENARIOS_PANEL_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:disabled {{
                background: {_C['bg_surface']};
                color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """)
        return btn

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def clear(self):
        """مسح اللوحة والرجوع لـ in-memory mode."""
        self._init_memory_scenario()

    def current_scenario_id(self) -> int | None:
        return self._current_id

    def is_in_memory(self) -> bool:
        return self._in_memory

    # ══════════════════════════════════════════════════════
    # بناء الـ Combo
    # ══════════════════════════════════════════════════════

    def _rebuild_combo(self):
        self.cmb_scenarios.blockSignals(True)
        self.cmb_scenarios.clear()
        for sc in self._scenarios:
            star = tr("bom_scenario_star_icon") if sc["is_default"] else ""
            self.cmb_scenarios.addItem(f"{star}{sc['name']}", sc["id"])
        for i, sc in enumerate(self._scenarios):
            if sc["id"] == self._current_id:
                self.cmb_scenarios.setCurrentIndex(i)
                break
        self.cmb_scenarios.blockSignals(False)

    def _sync_current(self):
        sc_id = self.cmb_scenarios.currentData()
        self._current_id = sc_id

        is_default = any(
            sc["id"] == sc_id and sc["is_default"]
            for sc in self._scenarios
        )
        self.lbl_default_badge.setVisible(is_default)
        self.btn_set_default.setEnabled(not is_default and sc_id is not None)

    # ══════════════════════════════════════════════════════
    # Signal handler
    # ══════════════════════════════════════════════════════

    def _on_scenario_changed(self, _):
        self._sync_current()
        if self._current_id is not None:
            self.scenario_changed.emit(self._current_id)

    # ══════════════════════════════════════════════════════
    # أزرار
    # ══════════════════════════════════════════════════════

    def _set_default(self):
        if self._current_id is None:
            return
        if self._in_memory:
            self._memory_set_default(self._current_id)
        else:
            self._db_set_default(self._current_id)

    def _rename(self):
        if self._current_id is None:
            return
        current_name = next(
            (sc["name"] for sc in self._scenarios if sc["id"] == self._current_id),
            ""
        )
        name, ok = QInputDialog.getText(
            self, tr("rename_scenario"), tr("new_name"), text=current_name
        )
        if not ok or not name.strip():
            return
        if self._in_memory:
            self._memory_rename(self._current_id, name.strip())
        else:
            self._db_rename(self._current_id, name.strip())

    def _clone(self):
        if self._current_id is None:
            return
        current_name = next(
            (sc["name"] for sc in self._scenarios if sc["id"] == self._current_id),
            ""
        )
        default_name = f"{tr('copy_of')} {current_name}" if current_name else tr("new_scenario")
        name, ok = QInputDialog.getText(
            self, tr("clone_scenario"), tr("new_scenario_name"), text=default_name
        )
        if not ok or not name.strip():
            return
        if self._in_memory:
            new_id = self._memory_clone(self._current_id, name.strip())
            self._current_id = new_id
            self._rebuild_combo()
            self._sync_current()
            self.scenario_changed.emit(new_id)
        else:
            new_id = self._db_clone(self._current_id, name.strip())
            if new_id is not None:
                self._current_id = new_id
                self._reload()
                self.scenario_changed.emit(new_id)

    def _add_new(self):
        count = len(self._scenarios) + 1
        name, ok = QInputDialog.getText(
            self, tr("new_scenario"), tr("scenario_name"),
            text=f"{tr('scenario')} {count}"
        )
        if not ok or not name.strip():
            return
        if self._in_memory:
            new_id = self._memory_add_new(name.strip())
            self._current_id = new_id
            self._rebuild_combo()
            self._sync_current()
            self.scenario_changed.emit(new_id)
        else:
            new_id = self._db_add_new(name.strip())
            if new_id is not None:
                self._current_id = new_id
                self._reload()
                self.scenario_changed.emit(new_id)

    def _delete(self):
        if self._current_id is None:
            return
        if len(self._scenarios) <= 1:
            QMessageBox.warning(self, tr("warning"), tr("cannot_delete_last_scenario"))
            return
        current_name = next(
            (sc["name"] for sc in self._scenarios if sc["id"] == self._current_id),
            ""
        )
        reply = QMessageBox.question(
            self, tr("confirm_delete"),
            tr("delete_scenario_confirm_msg").format(name=current_name),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        if self._in_memory:
            if self._memory_delete(self._current_id):
                self._rebuild_combo()
                self._sync_current()
                if self._current_id is not None:
                    self.scenario_changed.emit(self._current_id)
        else:
            if self._db_delete(self._current_id):
                self._current_id = None
                self._reload()
            else:
                QMessageBox.warning(self, tr("error"), tr("delete_scenario_failed"))