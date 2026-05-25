import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QLineEdit, QComboBox,
                             QPushButton, QGroupBox, QMessageBox, QSplitter,
                             QSizePolicy, QFrame, QShortcut)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas,
                                                 NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, MaxNLocator

from model import DiffractionModel
from scheme_drawing import draw_scheme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Дифракция на решётке")
        self.setMinimumSize(1300, 780)
        self._setup_ui()
        self._connect_signals()
        self._draw_initial_scheme()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ---- Left panel ----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(4)

        # Scheme canvas
        self.scheme_fig = Figure(figsize=(5, 3), dpi=100)
        self.scheme_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.scheme_canvas = FigureCanvas(self.scheme_fig)
        self.scheme_canvas.setMinimumHeight(240)
        self.scheme_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scheme_ax = self.scheme_fig.add_subplot(111)
        left_layout.addWidget(self.scheme_canvas, stretch=3)

        # Parameters
        params_frame = QWidget()
        params_layout = QVBoxLayout(params_frame)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(3)

        self.inputs = {}
        
        # Source group
        src_group = self._make_group("Источник", [
            ("a", "a (мкм):", "100"),
        ], combos=[
            ("source_type", "Форма:", ["uniform", "gaussian"]),
        ])
        params_layout.addWidget(src_group)

        # Spectrum group
        spec_group = self._make_group("Спектр", [
            ("lambda_0", "λ₀ (нм):", "550"),
            ("delta_lambda", "Δλ FWHM (нм):", "0"),
        ], combos=[
            ("spectrum_type", "Спектр:", ["mono", "gaussian"]),
        ])
        params_layout.addWidget(spec_group)
    
        # Lenses group
        lens_group = self._make_group("Линзы", [
            ("F1", "F₁ (мм):", "100"),
            ("F2", "F₂ (мм):", "100"),
        ])
        params_layout.addWidget(lens_group)

        # Grating group
        gr_group = self._make_group("Решётка", [
            ("N", "N (щелей):", "5"),
            ("b", "b (мкм):", "20"),
            ("d", "d (мкм):", "50"),
        ])
        params_layout.addWidget(gr_group)

        # Display group
        disp_group = self._make_group("Отображение", [], combos=[
            ("scale", "Масштаб I:", ["линейный", "логарифмический"]),
        ])
        params_layout.addWidget(disp_group)

        left_layout.addWidget(params_frame, stretch=2)

        # Button
        self.btn_calculate = QPushButton("Построить графики")
        self.btn_calculate.setMinimumHeight(36)
        self.btn_calculate.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-size: 13px; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #45a049; }")
        left_layout.addWidget(self.btn_calculate)

        # Trigger calculation by Enter/Return
        self.shortcut_return = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.shortcut_return.activated.connect(self._on_calculate)
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key_Enter), self)
        self.shortcut_enter.activated.connect(self._on_calculate)

        # ---- Right panel ----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)

        # Intensity plot with toolbar
        self.intensity_fig = Figure(figsize=(6, 3), dpi=100)
        self.intensity_canvas = FigureCanvas(self.intensity_fig)
        self.intensity_ax = self.intensity_fig.add_subplot(111)
        self.intensity_fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.14)

        self.intensity_toolbar = NavigationToolbar(self.intensity_canvas, right_widget)
        self.intensity_toolbar.setMaximumHeight(28)
        self.intensity_toolbar.setStyleSheet("font-size: 10px;")

        right_layout.addWidget(self.intensity_toolbar)
        right_layout.addWidget(self.intensity_canvas, stretch=1)

        # Visibility plot with toolbar
        self.visibility_fig = Figure(figsize=(6, 2.5), dpi=100)
        self.visibility_canvas = FigureCanvas(self.visibility_fig)
        self.visibility_ax = self.visibility_fig.add_subplot(111)
        self.visibility_fig.subplots_adjust(left=0.09, right=0.97, top=0.89, bottom=0.16)

        self.visibility_toolbar = NavigationToolbar(self.visibility_canvas, right_widget)
        self.visibility_toolbar.setMaximumHeight(28)
        self.visibility_toolbar.setStyleSheet("font-size: 10px;")

        right_layout.addWidget(self.visibility_toolbar)
        right_layout.addWidget(self.visibility_canvas, stretch=1)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([520, 780])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

    def _make_group(self, title, fields, combos=None):
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        grid = QGridLayout()
        grid.setContentsMargins(6, 4, 6, 4)
        grid.setVerticalSpacing(2)
        grid.setHorizontalSpacing(6)

        row = 0
        for key, label, default in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 10px;")
            edit = QLineEdit(default)
            edit.setMaximumWidth(90)
            edit.setStyleSheet("font-size: 10px;")
            edit.returnPressed.connect(self._on_calculate)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(edit, row, 1)
            self.inputs[key] = edit
            row += 1

        if combos:
            for key, label, items in combos:
                lbl = QLabel(label)
                lbl.setStyleSheet("font-size: 10px;")
                combo = QComboBox()
                combo.addItems(items)
                combo.setMaximumWidth(140)
                combo.setStyleSheet("font-size: 10px;")
                grid.addWidget(lbl, row, 0)
                grid.addWidget(combo, row, 1)
                self.inputs[key] = combo
                row += 1

        group.setLayout(grid)
        return group

    def _connect_signals(self):
        self.btn_calculate.clicked.connect(self._on_calculate)

    def _draw_initial_scheme(self):
        params = self._get_display_params_for_scheme()
        draw_scheme(self.scheme_ax, params)
        self.scheme_canvas.draw()

    def _get_display_params_for_scheme(self):
        def safe_float(key, default):
            try:
                return float(self.inputs[key].text())
            except (ValueError, AttributeError):
                return default

        def safe_int(key, default):
            try:
                return int(float(self.inputs[key].text()))
            except (ValueError, AttributeError):
                return default

        return {
            "a": safe_float("a", 100),
            "F1": safe_float("F1", 100),
            "F2": safe_float("F2", 100),
            "N": safe_int("N", 5),
            "b": safe_float("b", 20),
            "d": safe_float("d", 50),
            "lambda_0": safe_float("lambda_0", 550),
            "delta_lambda": safe_float("delta_lambda", 0),
        }

    def _read_params(self):
        """Read and validate all parameters. Returns dict or raises ValueError."""
        p = {}
        p["a"] = float(self.inputs["a"].text())
        p["F1"] = float(self.inputs["F1"].text())
        p["F2"] = float(self.inputs["F2"].text())
        p["N"] = int(float(self.inputs["N"].text()))
        p["b"] = float(self.inputs["b"].text())
        p["d"] = float(self.inputs["d"].text())
        p["lambda_0"] = float(self.inputs["lambda_0"].text())
        p["delta_lambda"] = float(self.inputs["delta_lambda"].text())
        p["spectrum_type"] = self.inputs["spectrum_type"].currentText()
        p["source_type"] = self.inputs["source_type"].currentText()
        p["scale"] = self.inputs["scale"].currentText()

        if p["a"] < 0:
            raise ValueError("Размер источника a должен быть ≥ 0")
        if p["F1"] <= 0 or p["F2"] <= 0:
            raise ValueError("Фокусные расстояния должны быть > 0")
        if p["N"] < 1:
            raise ValueError("Число щелей N должно быть ≥ 1")
        if p["b"] <= 0:
            raise ValueError("Ширина щели b должна быть > 0")
        if p["d"] <= 0:
            raise ValueError("Период решётки d должен быть > 0")
        if p["b"] > p["d"]:
            raise ValueError("Ширина щели b должна быть ≤ периода d")
        if p["lambda_0"] <= 0:
            raise ValueError("Длина волны λ₀ должна быть > 0")
        if p["delta_lambda"] < 0:
            raise ValueError("Ширина спектра Δλ должна быть ≥ 0")

        return p

    def _on_calculate(self):
        """Compute I(Y), V(Y) and build their plots"""
        try:
            p = self._read_params()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка параметров", str(e))
            return

        # Update scheme
        draw_scheme(self.scheme_ax, p)
        self.scheme_canvas.draw()

        # Create model
        model = DiffractionModel(
            a=p["a"], F1=p["F1"], F2=p["F2"],
            N=p["N"], b=p["b"], d=p["d"],
            lambda_0=p["lambda_0"], delta_lambda=p["delta_lambda"],
            spectrum_type=p["spectrum_type"], source_type=p["source_type"]
        )

        Y = model.get_Y_range()
        I_total = model.compute_total(Y)

        # Compute ideal reference if source is not ideal
        is_ideal = (p["a"] < 1e-6) and (p["delta_lambda"] < 1e-6)
        I_ideal = None if is_ideal else model.compute_ideal(Y)

        Y_vis, V_vis = model.compute_visibility(Y, I_total)

        self._update_plots(Y, I_total, I_ideal, Y_vis, V_vis, p)

    def _format_axis(self, ax):
        """Apply dense tick grid to an axis."""
        ax.xaxis.set_major_locator(MaxNLocator(nbins=12))
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        ax.grid(True, which='major', alpha=0.4, linewidth=0.8)
        ax.grid(True, which='minor', alpha=0.15, linewidth=0.4)
        ax.tick_params(which='both', direction='in', top=True, right=True)
        ax.tick_params(which='major', length=5)
        ax.tick_params(which='minor', length=2.5)

    def _update_plots(self, Y, I_total, I_ideal, Y_vis, V_vis, params):
        # Choose display units
        Y_max_abs = np.max(np.abs(Y))
        if Y_max_abs < 1e-4:
            Y_display = Y * 1e6
            x_unit = "мкм"
        elif Y_max_abs < 0.1:
            Y_display = Y * 1e3
            x_unit = "мм"
        else:
            Y_display = Y * 100
            x_unit = "см"

        log_scale = params["scale"] == "логарифмический"

        # ---- Intensity ----
        ax = self.intensity_ax
        ax.clear()

        if log_scale:
            I_plot = np.copy(I_total)
            I_plot[I_plot < 1e-10] = 1e-10
            if I_ideal is not None:
                I_id = np.copy(I_ideal)
                I_id[I_id < 1e-10] = 1e-10
                ax.semilogy(Y_display, I_id, color='#CCCCCC', linewidth=1.0,
                            label='Идеальный источник', zorder=1)
            ax.semilogy(Y_display, I_plot, color='#1976D2', linewidth=0.8,
                        label='I(Y)', zorder=2)
            ax.set_ylim(1e-4, 2)
        else:
            if I_ideal is not None:
                ax.plot(Y_display, I_ideal, color='#CCCCCC', linewidth=1.0,
                        label='Идеальный источник', zorder=1)
            ax.plot(Y_display, I_total, color='#1976D2', linewidth=0.8,
                    label='I(Y)', zorder=2)
            ax.set_ylim(-0.03, 1.08)

        ax.set_xlim(Y_display[0], Y_display[-1])
        ax.set_xlabel(f"Y ({x_unit})", fontsize=10)
        ax.set_ylabel("I / I_max", fontsize=10)
        ax.set_title("Интенсивность на экране", fontsize=11)
        ax.legend(fontsize=8, loc='upper right')
        self._format_axis(ax)
        self.intensity_canvas.draw()
        self.intensity_toolbar.update()

        # ---- Visibility ----
        ax2 = self.visibility_ax
        ax2.clear()

        if len(Y_vis) > 0:
            if Y_max_abs < 1e-4:
                Y_vis_d = Y_vis * 1e6
            elif Y_max_abs < 0.1:
                Y_vis_d = Y_vis * 1e3
            else:
                Y_vis_d = Y_vis * 100
            ax2.plot(Y_vis_d, V_vis, 'o-', color='#E65100',
                     markersize=4, linewidth=1.0)
        else:
            ax2.text(0.5, 0.5, "Недостаточно максимумов\nдля расчёта видности",
                     transform=ax2.transAxes, ha='center', va='center',
                     fontsize=11, color='gray')

        ax2.axhline(y=1.0, color='gray', linestyle='--', linewidth=0.7, alpha=0.5)
        ax2.set_xlim(Y_display[0], Y_display[-1])
        ax2.set_ylim(-0.05, 1.1)
        ax2.set_xlabel(f"Y ({x_unit})", fontsize=10)
        ax2.set_ylabel("V", fontsize=10)
        ax2.set_title("Видность", fontsize=11)
        self._format_axis(ax2)
        self.visibility_canvas.draw()

        self.visibility_toolbar.update()