"""
Interfaz de finanzas para María.
Estética warm minimalista coherente con la ventana de notas.
"""
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QFrame,
    QScrollArea, QProgressBar, QApplication, QMenu, QDateEdit,
    QMessageBox, QInputDialog, QDialog, QSizePolicy, QCheckBox
)
from PyQt5.QtGui import QColor, QFont
from datetime import datetime, timedelta
from .logica_finanzas import gestor

# ─────────────────────────────────────────────────────────────
# 🎨 PALETA — cálida, de bajo contraste (coherente con notas)
# ─────────────────────────────────────────────────────────────
BG_APP = "#242730"          # fondo general (grafito cálido)
BG_PANEL = "#2b2e38"        # sidebar / paneles
BG_INPUT = "#1d2028"        # campos de texto
BG_INPUT_HOVER = "#20232c"
BORDE = "#3c3f4a"
BORDE_SUAVE = "#33363f"
TEXTO_PRINCIPAL = "#ded8ca"   # hueso cálido
TEXTO_SECUNDARIO = "#8f8b83"  # gris cálido para metadatos
TEXTO_TERCIARIO = "#6b6860"
ACENTO = "#c17a56"           # terracota — color de marca
ACENTO_HOVER = "#d38f6c"
ACENTO_SUAVE = "rgba(193, 122, 86, 0.16)"
DORADO = "#c9a24b"           # para elementos destacados/positivos
DORADO_SUAVE = "rgba(201, 162, 75, 0.18)"
PELIGRO = "#a15c52"
PELIGRO_HOVER = "#b76f64"
POSITIVO = "#8f9d7a"         # verde cálido suave para positivos
NEGATIVO = "#a15c52"         # mismo que PELIGRO

QSS_FINANZAS = f"""
QWidget#FinanzasWindow {{ background-color: {BG_APP}; }}
QFrame#panel {{ background-color: {BG_PANEL}; border: 1px solid {BORDE}; border-radius: 10px; }}
QFrame#card_meta {{
    background-color: {BG_PANEL}; border: 1px solid {BORDE};
    border-radius: 8px;
}}
QFrame#card_meta.completada {{
    background-color: #1a241f; border: 1px solid {DORADO};
    border-radius: 8px;
}}
QFrame#card_meta.libre {{
    background-color: #1d242b; border: 1px solid #3a4a5c;
    border-radius: 8px;
}}
QTabWidget::pane {{ border: none; background-color: {BG_APP}; }}
QTabBar::tab {{
    background: {BG_PANEL}; color: {TEXTO_SECUNDARIO}; padding: 8px 16px;
    border: 1px solid {BORDE}; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    margin-right: 2px; font-size: 12px;
}}
QTabBar::tab:selected {{ background: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; }}
QTabBar::tab:hover {{ background: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; }}
QLabel {{ color: {TEXTO_PRINCIPAL}; font-size: 12px; }}
QLabel#titulo {{ color: {TEXTO_PRINCIPAL}; font-size: 16px; font-weight: 600; }}
QLabel#saldo {{ color: {TEXTO_PRINCIPAL}; font-size: 28px; font-weight: 700; }}
QLabel#positivo {{ color: {POSITIVO}; }}
QLabel#negativo {{ color: {NEGATIVO}; }}
QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
    background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
    border: 1px solid {BORDE}; border-radius: 6px;
    padding: 6px 10px; font-size: 12px;
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border-color: {ACENTO};
}}
QDateEdit:disabled, QDoubleSpinBox:disabled {{
    background-color: {BG_APP}; color: {TEXTO_TERCIARIO}; border-color: {BORDE};
}}
QTableWidget {{
    background-color: {BG_APP}; color: {TEXTO_PRINCIPAL};
    border: 1px solid {BORDE}; gridline-color: {BORDE};
    font-size: 12px;
}}
QTableWidget::item {{ padding: 4px; }}
QTableWidget::item:selected {{ background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; }}
QHeaderView::section {{
    background-color: {BG_PANEL}; color: {TEXTO_SECUNDARIO};
    padding: 6px; border: none; border-bottom: 1px solid {BORDE};
    font-weight: 600;
}}
QPushButton#btn_primario {{
    background-color: {ACENTO}; color: {BG_APP}; border: none;
    border-radius: 6px; padding: 6px 14px; font-weight: 600;
}}
QPushButton#btn_primario:hover {{ background-color: {ACENTO_HOVER}; }}
QPushButton#btn_secundario {{
    background-color: {BG_PANEL}; color: {TEXTO_PRINCIPAL}; 
    border: 1px solid {BORDE}; border-radius: 6px; padding: 6px 14px;
}}
QPushButton#btn_secundario:hover {{ background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; }}
QPushButton#btn_peligro {{
    background-color: transparent; color: {TEXTO_SECUNDARIO}; border: 1px solid {BORDE};
    border-radius: 6px; padding: 4px 10px; font-size: 11px;
}}
QPushButton#btn_peligro:hover {{ background-color: {PELIGRO}; color: {TEXTO_PRINCIPAL}; border-color: {PELIGRO}; }}
QPushButton#btn_cerrar {{
    background: transparent; color: {TEXTO_SECUNDARIO}; border: none; font-size: 14px;
}}
QPushButton#btn_cerrar:hover {{ color: {PELIGRO}; }}
QPushButton#btn_rapido {{
    background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; border: 1px solid {BORDE};
    border-radius: 6px; padding: 8px 12px; font-weight: 600; font-size: 12px;
}}
QPushButton#btn_rapido:hover {{ background-color: {ACENTO}; color: {BG_APP}; border-color: {ACENTO}; }}
QProgressBar {{
    border: none; background-color: {BG_INPUT}; border-radius: 4px; height: 10px;
}}
QProgressBar::chunk {{ background-color: {ACENTO}; border-radius: 4px; }}
QScrollBar:vertical {{ border: none; background: transparent; width: 6px; }}
QScrollBar::handle:vertical {{ background: {BORDE}; border-radius: 3px; }}
QCheckBox {{ color: {TEXTO_PRINCIPAL}; font-size: 12px; spacing: 6px; }}
QCheckBox::indicator {{
    width: 14px; height: 14px; border-radius: 3px;
    border: 1px solid {BORDE}; background: {BG_PANEL};
}}
QCheckBox::indicator:checked {{
    background: {ACENTO}; border-color: {ACENTO};
}}
QCheckBox::indicator:hover {{ border-color: {ACENTO_HOVER}; }}
"""

# ── Utilidad de formato numérico español ───────────────────
def fmt_euros(v):
    """Formatea un número como moneda española: 1.234,56 €"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = 0.0
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# ── Diálogo personalizado de aporte (tema cálido) ──────────
class DialogoAportar(QDialog):
    """Diálogo modal cálido para aportar a una meta."""
    def __init__(self, parent, nombre_meta, actual, objetivo=None, fecha_limite=None):
        super().__init__(parent)
        self._objetivo = float(objetivo) if objetivo is not None else None
        self._actual = float(actual)
        
        if self._objetivo is not None:
            self.setWindowTitle(f"Aportar a '{nombre_meta}'")
        else:
            self.setWindowTitle(f"Aportar a '{nombre_meta}' (ahorro libre)")
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(420, 380 if self._objetivo is not None else 340)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDE};
                border-radius: 12px;
            }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-size: 12px; }}
            QLabel#titulo_dialogo {{
                color: {TEXTO_PRINCIPAL}; font-size: 15px; font-weight: 600;
            }}
            QLabel#info {{ color: {TEXTO_SECUNDARIO}; font-size: 11px; }}
            QLabel#monto_display {{
                color: {DORADO}; font-size: 22px; font-weight: 700;
            }}
            QLineEdit#input_aporte {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 8px;
                padding: 10px 14px; font-size: 18px; font-weight: 600;
            }}
            QLineEdit#input_aporte:focus {{
                border-color: {ACENTO};
            }}
            QPushButton#btn_cerrar_dialogo {{
                background: transparent; color: {TEXTO_SECUNDARIO}; border: none;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton#btn_cerrar_dialogo:hover {{ color: {PELIGRO}; }}
            QPushButton#btn_confirmar {{
                background-color: {ACENTO}; color: {BG_APP}; border: none;
                border-radius: 8px; padding: 10px 20px;
                font-size: 13px; font-weight: 700;
            }}
            QPushButton#btn_confirmar:hover {{ background-color: {ACENTO_HOVER}; }}
            QPushButton#btn_confirmar:disabled {{
                background-color: {BORDE}; color: {TEXTO_SECUNDARIO};
            }}
            QPushButton#btn_cancelar_dialogo {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; border: none;
                border-radius: 8px; padding: 10px 20px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton#btn_cancelar_dialogo:hover {{ background-color: {BORDE}; }}
            QProgressBar {{
                border: none; background-color: {BG_INPUT};
                border-radius: 5px; height: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {ACENTO}; border-radius: 5px;
            }}
        """)
        self._cantidad = 0.0
        
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 18)
        root.setSpacing(12)
        
        # Cabecera
        top = QHBoxLayout()
        if self._objetivo is not None:
            titulo = QLabel(f"💎  Aportar a '{nombre_meta}'")
        else:
            titulo = QLabel(f"💰  Aportar a '{nombre_meta}' (ahorro libre)")
        titulo.setObjectName("titulo_dialogo")
        top.addWidget(titulo)
        top.addStretch()
        btn_x = QPushButton("✕")
        btn_x.setObjectName("btn_cerrar_dialogo")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        btn_x.clicked.connect(self.reject)
        top.addWidget(btn_x)
        root.addLayout(top)
        
        # Info actual / objetivo (o solo actual si es libre)
        info_layout = QHBoxLayout()
        lbl_actual = QLabel(f"Actual: {fmt_euros(self._actual)}")
        lbl_actual.setObjectName("info")
        info_layout.addWidget(lbl_actual)
        if self._objetivo is not None:
            lbl_obj = QLabel(f"Objetivo: {fmt_euros(self._objetivo)}")
            lbl_obj.setObjectName("info")
            info_layout.addStretch()
            info_layout.addWidget(lbl_obj)
        else:
            lbl_libre = QLabel("Sin objetivo fijo · acumula lo que quieras")
            lbl_libre.setStyleSheet(f"color:{DORADO}; font-size:11px; font-style:italic;")
            info_layout.addStretch()
            info_layout.addWidget(lbl_libre)
        root.addLayout(info_layout)
        
        # Barra de progreso actual (solo si hay objetivo)
        if self._objetivo is not None:
            pct_actual = min(100, (self._actual / self._objetivo * 100)) if self._objetivo > 0 else 0
            self.bar_actual = QProgressBar()
            self.bar_actual.setMaximum(100)
            self.bar_actual.setValue(int(pct_actual))
            self.bar_actual.setFormat(f"{pct_actual:.1f}% actual")
            root.addWidget(self.bar_actual)
        else:
            # Mostrar total acumulado en grande
            lbl_total = QLabel(fmt_euros(self._actual))
            lbl_total.setObjectName("monto_display")
            lbl_total.setAlignment(Qt.AlignCenter)
            lbl_total.setStyleSheet(f"color:{DORADO}; font-size:22px; font-weight:700;")
            root.addWidget(lbl_total)
        
        # Input de cantidad
        lbl_input = QLabel("Cantidad a aportar (€):")
        lbl_input.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        root.addWidget(lbl_input)
        
        self.input_cantidad = QLineEdit("0.00")
        self.input_cantidad.setObjectName("input_aporte")
        self.input_cantidad.setAlignment(Qt.AlignCenter)
        self.input_cantidad.setPlaceholderText("0,00")
        self.input_cantidad.textChanged.connect(self._actualizar_preview)
        root.addWidget(self.input_cantidad)
        
        # Preview del resultado
        if self._objetivo is not None:
            self.lbl_preview = QLabel(f"Tras el aporte: {fmt_euros(self._actual)} / {fmt_euros(self._objetivo)}")
            self.lbl_preview.setObjectName("info")
            self.lbl_preview.setAlignment(Qt.AlignCenter)
            root.addWidget(self.lbl_preview)
            # Barra de progreso preview
            self.bar_preview = QProgressBar()
            self.bar_preview.setMaximum(100)
            self.bar_preview.setValue(int(min(100, (self._actual / self._objetivo * 100)) if self._objetivo > 0 else 0))
            self.bar_preview.setFormat("0.0% tras aporte")
            self.bar_preview.setStyleSheet(f"""
                QProgressBar::chunk {{ background-color: {DORADO}; border-radius: 5px; }}
            """)
            root.addWidget(self.bar_preview)
        else:
            self.lbl_preview = QLabel(f"Tras el aporte: {fmt_euros(self._actual)}")
            self.lbl_preview.setObjectName("info")
            self.lbl_preview.setAlignment(Qt.AlignCenter)
            self.lbl_preview.setStyleSheet(f"color:{DORADO}; font-size:13px; font-weight:600;")
            root.addWidget(self.lbl_preview)
        
        # Botones de aporte rápido
        lbl_rapido = QLabel("Aporte rápido:")
        lbl_rapido.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        root.addWidget(lbl_rapido)
        rapidos = QHBoxLayout()
        rapidos.setSpacing(6)
        for importe in (5, 10, 20, 50, 100):
            btn = QPushButton(f"{importe}€")
            btn.setObjectName("btn_rapido")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, v=importe: self._set_rapido(v))
            rapidos.addWidget(btn)
        root.addLayout(rapidos)
        
        # Botones finales
        botones = QHBoxLayout()
        botones.setSpacing(8)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_cancelar_dialogo")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        self.btn_confirmar = QPushButton("✓  Aportar")
        self.btn_confirmar.setObjectName("btn_confirmar")
        self.btn_confirmar.setCursor(Qt.PointingHandCursor)
        self.btn_confirmar.setEnabled(False)
        self.btn_confirmar.clicked.connect(self._confirmar)
        botones.addWidget(self.btn_confirmar)
        root.addLayout(botones)
        
        # Enfocar el input al abrir
        self.input_cantidad.setFocus()
        self.input_cantidad.selectAll()
    
    def _set_rapido(self, valor):
        try:
            actual = float(self.input_cantidad.text().replace(",", "."))
        except (ValueError, AttributeError):
            actual = 0.0
        self.input_cantidad.setText(f"{actual + valor:.2f}")
    
    def _actualizar_preview(self, texto):
        try:
            cantidad = float(texto.replace(",", "."))
        except (ValueError, AttributeError):
            cantidad = 0.0
        
        if cantidad <= 0:
            self.btn_confirmar.setEnabled(False)
            if self._objetivo is not None:
                self.lbl_preview.setText(f"Tras el aporte: {fmt_euros(self._actual)} / {fmt_euros(self._objetivo)}")
                pct = min(100, (self._actual / self._objetivo * 100)) if self._objetivo > 0 else 0
                self.bar_preview.setValue(int(pct))
                self.bar_preview.setFormat(f"{pct:.1f}% tras aporte")
            else:
                self.lbl_preview.setText(f"Tras el aporte: {fmt_euros(self._actual)}")
            return
        
        nuevo_total = self._actual + cantidad
        self.btn_confirmar.setEnabled(True)
        
        if self._objetivo is not None:
            pct_nuevo = min(100, (nuevo_total / self._objetivo * 100)) if self._objetivo > 0 else 0
            self.lbl_preview.setText(f"Tras el aporte: {fmt_euros(nuevo_total)} / {fmt_euros(self._objetivo)}")
            self.bar_preview.setValue(int(pct_nuevo))
            self.bar_preview.setFormat(f"{pct_nuevo:.1f}% tras aporte")
            # Cambiar color si se completa
            if pct_nuevo >= 100:
                self.bar_preview.setStyleSheet(f"""
                    QProgressBar {{ border:none; background:{BG_INPUT}; border-radius:5px; height:10px; }}
                    QProgressBar::chunk {{ background-color:{DORADO}; border-radius:5px; }}
                """)
            else:
                self.bar_preview.setStyleSheet(f"""
                    QProgressBar {{ border:none; background:{BG_INPUT}; border-radius:5px; height:10px; }}
                    QProgressBar::chunk {{ background-color:{DORADO}; border-radius:5px; }}
                """)
        else:
            self.lbl_preview.setText(f"Tras el aporte: {fmt_euros(nuevo_total)}")
    
    def _confirmar(self):
        try:
            self._cantidad = float(self.input_cantidad.text().replace(",", "."))
        except (ValueError, AttributeError):
            return
        if self._cantidad > 0:
            self.accept()
    
    def get_cantidad(self):
        return self._cantidad
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._confirmar()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

# ── Diálogo de edición de meta ────────────────────────────
class DialogoEditarMeta(QDialog):
    """Diálogo modal cálido para editar nombre/objetivo/fecha de una meta."""
    def __init__(self, parent, nombre, objetivo, fecha_limite):
        super().__init__(parent)
        self.setWindowTitle("Editar meta")
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(420, 340)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDE};
                border-radius: 12px;
            }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-size: 12px; }}
            QLabel#titulo_dialogo {{
                color: {TEXTO_PRINCIPAL}; font-size: 15px; font-weight: 600;
            }}
            QLineEdit, QDateEdit, QDoubleSpinBox {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 6px;
                padding: 8px 12px; font-size: 13px;
            }}
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus {{ border-color: {ACENTO}; }}
            QDateEdit:disabled, QDoubleSpinBox:disabled {{
                background-color: {BG_INPUT}; color: {TEXTO_TERCIARIO}; border-color: {BORDE};
            }}
            QPushButton#btn_cerrar_dialogo {{
                background: transparent; color: {TEXTO_SECUNDARIO}; border: none;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton#btn_cerrar_dialogo:hover {{ color: {PELIGRO}; }}
            QPushButton#btn_confirmar {{
                background-color: {ACENTO}; color: {BG_APP}; border: none;
                border-radius: 8px; padding: 8px 18px;
                font-size: 13px; font-weight: 700;
            }}
            QPushButton#btn_confirmar:hover {{ background-color: {ACENTO_HOVER}; }}
            QPushButton#btn_cancelar_dialogo {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL}; border: none;
                border-radius: 8px; padding: 8px 18px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton#btn_cancelar_dialogo:hover {{ background-color: {BORDE}; }}
            QCheckBox {{ color: {TEXTO_PRINCIPAL}; font-size: 12px; spacing: 6px; }}
            QCheckBox::indicator {{
                width: 14px; height: 14px; border-radius: 3px;
                border: 1px solid {BORDE}; background: {BG_PANEL};
            }}
            QCheckBox::indicator:checked {{
                background: {ACENTO}; border-color: {ACENTO};
            }}
            QCheckBox::indicator:hover {{ border-color: {ACENTO_HOVER}; }}
        """)
        self._resultado = None
        
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 18)
        root.setSpacing(10)
        
        # Cabecera
        top = QHBoxLayout()
        titulo = QLabel("️  Editar meta")
        titulo.setObjectName("titulo_dialogo")
        top.addWidget(titulo)
        top.addStretch()
        btn_x = QPushButton("✕")
        btn_x.setObjectName("btn_cerrar_dialogo")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        btn_x.clicked.connect(self.reject)
        top.addWidget(btn_x)
        root.addLayout(top)
        
        # Nombre
        root.addWidget(QLabel("Nombre:"))
        self.input_nombre = QLineEdit(nombre)
        self.input_nombre.setPlaceholderText("Nombre de la meta")
        root.addWidget(self.input_nombre)
        
        # Objetivo + checkbox sin objetivo
        obj_layout = QHBoxLayout()
        self.input_objetivo = QDoubleSpinBox()
        self.input_objetivo.setDecimals(2)
        self.input_objetivo.setMaximum(9999999)
        self.input_objetivo.setPrefix("€ ")
        self.input_objetivo.setValue(float(objetivo) if objetivo is not None else 0.0)
        obj_layout.addWidget(self.input_objetivo, 1)
        self.chk_sin_objetivo = QCheckBox("  Sin objetivo fijo")
        self.chk_sin_objetivo.setChecked(objetivo is None)
        self.chk_sin_objetivo.toggled.connect(self._toggle_objetivo)
        obj_layout.addWidget(self.chk_sin_objetivo)
        root.addLayout(obj_layout)
        self._toggle_objetivo(self.chk_sin_objetivo.isChecked())
        
        # Fecha límite + checkbox sin límite
        fecha_layout = QHBoxLayout()
        self.input_fecha = QDateEdit()
        self.input_fecha.setCalendarPopup(True)
        self.input_fecha.setDisplayFormat("dd/MM/yyyy")
        if fecha_limite:
            try:
                self.input_fecha.setDate(datetime.strptime(fecha_limite, "%Y-%m-%d").date())
            except Exception:
                self.input_fecha.setDate(datetime.now().date())
        else:
            self.input_fecha.setDate(datetime.now().date())
        fecha_layout.addWidget(self.input_fecha, 1)
        self.chk_sin_limite = QCheckBox("📅  Sin fecha límite")
        self.chk_sin_limite.setChecked(not bool(fecha_limite))
        self.chk_sin_limite.toggled.connect(self._toggle_fecha)
        fecha_layout.addWidget(self.chk_sin_limite)
        root.addLayout(fecha_layout)
        self._toggle_fecha(self.chk_sin_limite.isChecked())
        
        # Botones
        botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_cancelar_dialogo")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        btn_ok = QPushButton("✓  Guardar")
        btn_ok.setObjectName("btn_confirmar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self._guardar)
        botones.addWidget(btn_ok)
        root.addLayout(botones)
        
        self.input_nombre.setFocus()
        self.input_nombre.selectAll()
    
    def _toggle_objetivo(self, activado):
        """Deshabilita el QDoubleSpinBox cuando se marca 'sin objetivo fijo'."""
        self.input_objetivo.setEnabled(not activado)
    
    def _toggle_fecha(self, activado):
        """Deshabilita el QDateEdit cuando se marca 'sin fecha límite'."""
        self.input_fecha.setEnabled(not activado)
    
    def _guardar(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            return
        # Objetivo: None si está marcado, si no el valor del spinbox
        if self.chk_sin_objetivo.isChecked():
            objetivo = None
        else:
            objetivo = self.input_objetivo.value()
            if objetivo <= 0:
                return
        # Fecha: None si está marcado, si no la fecha
        if self.chk_sin_limite.isChecked():
            fecha = None
        else:
            fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        self._resultado = (nombre, objetivo, fecha)
        self.accept()
    
    def get_resultado(self):
        return self._resultado
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._guardar()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

# ── Diálogo de calculadora mental (sin persistencia) ───────
class DialogoCalculadoraDinero(QDialog):
    """Calculadora mental rápida: suma y resta cantidades sin guardar nada.
    Útil para verificar cálculos antes de aportar a una meta."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("🧮  Calculadora")
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(440, 420)
        self._total = 0.0
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDE};
                border-radius: 12px;
            }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-size: 12px; }}
            QLabel#titulo_dialogo {{
                color: {TEXTO_PRINCIPAL}; font-size: 15px; font-weight: 600;
            }}
            QLabel#info {{ color: {TEXTO_SECUNDARIO}; font-size: 11px; }}
            QLabel#monto_display {{
                color: {DORADO}; font-size: 30px; font-weight: 700;
                padding: 10px 0;
            }}
            QLineEdit#input_cantidad {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 8px;
                padding: 10px 14px; font-size: 16px; font-weight: 600;
            }}
            QLineEdit#input_cantidad:focus {{ border-color: {ACENTO}; }}
            QPushButton#btn_cerrar_dialogo {{
                background: transparent; color: {TEXTO_SECUNDARIO}; border: none;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton#btn_cerrar_dialogo:hover {{ color: {PELIGRO}; }}
            QPushButton#btn_rapido {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 6px;
                padding: 8px 10px; font-weight: 600; font-size: 12px;
            }}
            QPushButton#btn_rapido:hover {{
                background-color: {ACENTO}; color: {BG_APP}; border-color: {ACENTO};
            }}
            QPushButton#btn_rapido.menos {{
                color: {NEGATIVO};
            }}
            QPushButton#btn_rapido.menos:hover {{
                background-color: {PELIGRO}; color: {TEXTO_PRINCIPAL}; border-color: {PELIGRO};
            }}
            QPushButton#btn_reset {{
                background-color: {BG_INPUT}; color: {TEXTO_SECUNDARIO};
                border: 1px solid {BORDE}; border-radius: 8px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton#btn_reset:hover {{
                background-color: {PELIGRO}; color: {TEXTO_PRINCIPAL}; border-color: {PELIGRO};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 18)
        root.setSpacing(12)

        # Cabecera
        top = QHBoxLayout()
        titulo = QLabel("🧮  Calculadora mental")
        titulo.setObjectName("titulo_dialogo")
        top.addWidget(titulo)
        top.addStretch()
        btn_x = QPushButton("✕")
        btn_x.setObjectName("btn_cerrar_dialogo")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        btn_x.clicked.connect(self.reject)
        top.addWidget(btn_x)
        root.addLayout(top)

        # Info
        info = QLabel("Suma y resta sin guardar nada · solo para verificar")
        info.setObjectName("info")
        info.setAlignment(Qt.AlignCenter)
        root.addWidget(info)

        # Display del total (seleccionable + botón copiar)
        total_row = QHBoxLayout()
        total_row.setSpacing(8)

        self.lbl_total = QLabel(fmt_euros(0.0))
        self.lbl_total.setObjectName("monto_display")
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_total.setCursor(Qt.IBeamCursor)
        self.lbl_total.setToolTip("Click y arrastra para seleccionar el texto")
        total_row.addWidget(self.lbl_total, 1)

        self.btn_copiar = QPushButton("📋")
        self.btn_copiar.setFixedSize(36, 36)
        self.btn_copiar.setCursor(Qt.PointingHandCursor)
        self.btn_copiar.setToolTip("Copiar resultado al portapapeles")
        self.btn_copiar.setStyleSheet(f"""
        QPushButton {{
          background-color: {BG_INPUT};
          color: {TEXTO_SECUNDARIO};
          border: 1px solid {BORDE};
          border-radius: 6px;
          font-size: 16px;
         }}
        QPushButton:hover {{
          background-color: {ACENTO};
          color: {BG_APP};
          border-color: {ACENTO};
         }}
        """)
        self.btn_copiar.clicked.connect(self._copiar_resultado)
        total_row.addWidget(self.btn_copiar)

        root.addLayout(total_row)

        # Input cantidad personalizada
        lbl_input = QLabel("Cantidad personalizada:")
        lbl_input.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        root.addWidget(lbl_input)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self.input_cantidad = QLineEdit("0.00")
        self.input_cantidad.setObjectName("input_cantidad")
        self.input_cantidad.setAlignment(Qt.AlignCenter)
        self.input_cantidad.setPlaceholderText("0,00")
        input_row.addWidget(self.input_cantidad, 1)

        btn_mas = QPushButton("+")
        btn_mas.setObjectName("btn_rapido")
        btn_mas.setFixedSize(44, 40)
        btn_mas.setCursor(Qt.PointingHandCursor)
        btn_mas.setToolTip("Sumar cantidad")
        btn_mas.clicked.connect(lambda: self._aplicar_custom(1))
        input_row.addWidget(btn_mas)

        btn_menos = QPushButton("−")
        btn_menos.setObjectName("btn_rapido")
        btn_menos.setProperty("class", "menos")
        btn_menos.setStyleSheet(
            f"background-color:{BG_INPUT}; color:{NEGATIVO}; border:1px solid {BORDE};"
            f"border-radius:6px; padding:8px 10px; font-weight:700; font-size:16px;"
        )
        btn_menos.setFixedSize(44, 40)
        btn_menos.setCursor(Qt.PointingHandCursor)
        btn_menos.setToolTip("Restar cantidad")
        btn_menos.clicked.connect(lambda: self._aplicar_custom(-1))
        input_row.addWidget(btn_menos)
        root.addLayout(input_row)

        # Botones rápidos de suma
        lbl_rapido = QLabel("Sumar rápido:")
        lbl_rapido.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        root.addWidget(lbl_rapido)
        rapidos_mas = QHBoxLayout()
        rapidos_mas.setSpacing(6)
        for importe in (5, 10, 20, 50, 100):
            btn = QPushButton(f"+{importe}€")
            btn.setObjectName("btn_rapido")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, v=importe: self._aplicar(v))
            rapidos_mas.addWidget(btn)
        root.addLayout(rapidos_mas)

        # Botones rápidos de resta (para corregir errores)
        lbl_rapido_menos = QLabel("Restar rápido (si te equivocas):")
        lbl_rapido_menos.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        root.addWidget(lbl_rapido_menos)
        rapidos_menos = QHBoxLayout()
        rapidos_menos.setSpacing(6)
        for importe in (5, 10, 20, 50, 100):
            btn = QPushButton(f"−{importe}€")
            btn.setObjectName("btn_rapido")
            btn.setProperty("class", "menos")
            btn.setStyleSheet(
                f"background-color:{BG_INPUT}; color:{NEGATIVO}; border:1px solid {BORDE};"
                f"border-radius:6px; padding:8px 10px; font-weight:600; font-size:12px;"
            )
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, v=importe: self._aplicar(-v))
            rapidos_menos.addWidget(btn)
        root.addLayout(rapidos_menos)

        # Botón reset
        botones = QHBoxLayout()
        botones.setSpacing(8)
        btn_reset = QPushButton("🔄  Reiniciar a 0")
        btn_reset.setObjectName("btn_reset")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reset)
        botones.addWidget(btn_reset)
        botones.addStretch()
        root.addLayout(botones)

        self.input_cantidad.setFocus()
        self.input_cantidad.selectAll()

    def _aplicar(self, valor):
        """Suma o resta un valor fijo al total."""
        self._total += valor
        self._actualizar_display()

    def _aplicar_custom(self, signo):
        """Suma o resta la cantidad escrita en el input."""
        try:
            cantidad = float(self.input_cantidad.text().replace(",", "."))
        except (ValueError, AttributeError):
            cantidad = 0.0
        if cantidad <= 0:
            return
        self._total += signo * cantidad
        self._actualizar_display()
        # Limpiar input para el siguiente uso
        self.input_cantidad.setText("0.00")
        self.input_cantidad.setFocus()
        self.input_cantidad.selectAll()

    def _reset(self):
        self._total = 0.0
        self._actualizar_display()

    def _actualizar_display(self):
        self.lbl_total.setText(fmt_euros(self._total))
        # Color según el signo del total
        if self._total > 0:
            color = DORADO
        elif self._total < 0:
            color = NEGATIVO
        else:
            color = TEXTO_SECUNDARIO
        self.lbl_total.setStyleSheet(
            f"color:{color}; font-size:30px; font-weight:700; padding:10px 0;"
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Enter suma la cantidad del input (comportamiento natural)
            self._aplicar_custom(1)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def _copiar_resultado(self):
      """Copia el resultado al portapapeles con feedback visual."""
      texto = self.lbl_total.text()
      clipboard = QApplication.clipboard()
      clipboard.setText(texto)
    
      # Feedback visual: cambiar icono y color del botón
      self.btn_copiar.setText("✓")
      self.btn_copiar.setStyleSheet(f"""
        QPushButton {{
            background-color: {POSITIVO};
            color: {BG_APP};
            border: 1px solid {POSITIVO};
            border-radius: 6px;
            font-size: 16px;
            font-weight: 700;
        }}
      """)
      self.btn_copiar.setToolTip("✓ Copiado al portapapeles")
    
      # Restaurar el botón después de 1.5 segundos
      from PyQt5.QtCore import QTimer
      QTimer.singleShot(1500, self._restaurar_boton_copiar)

    def _restaurar_boton_copiar(self):
      """Restaura el botón de copiar a su estado original."""
      self.btn_copiar.setText("📋")
      self.btn_copiar.setStyleSheet(f"""
        QPushButton {{
            background-color: {BG_INPUT};
            color: {TEXTO_SECUNDARIO};
            border: 1px solid {BORDE};
            border-radius: 6px;
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: {ACENTO};
            color: {BG_APP};
            border-color: {ACENTO};
        }}
     """)
      self.btn_copiar.setToolTip("Copiar resultado al portapapeles")

# ── Ventana principal de finanzas ──────────────────────────
class VentanaFinanzas(QWidget):
    def __init__(self, maria=None):
        super().__init__()
        self.maria = maria
        self.setObjectName("FinanzasWindow")
        self.setStyleSheet(QSS_FINANZAS)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(820, 560)
        self.setMinimumSize(720, 480)
        self._drag_pos = None
        self._construir_ui()
        self._refrescar_todo()
    
    # ── UI ─────────────────────────────────────────────────
    def _construir_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        contenedor = QFrame()
        contenedor.setObjectName("panel")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(14, 10, 14, 14)
        layout.setSpacing(10)
        
        # Barra superior
        top = QHBoxLayout()
        titulo = QLabel(" Finanzas")
        titulo.setObjectName("titulo")
        top.addWidget(titulo)
        top.addStretch()
        btn_calc = QPushButton("🧮 Calculadora")
        btn_calc.setCursor(Qt.PointingHandCursor)
        btn_calc.setToolTip("Calculadora mental (sin guardar)")
        btn_calc.setStyleSheet(f"""
          QPushButton {{
          background-color: {DORADO_SUAVE};
          color: {DORADO};
          border: 1px solid {DORADO};
          border-radius: 6px;
          padding: 4px 10px;
          font-size: 12px;
          font-weight: 600;
          }}
          QPushButton:hover {{
          background-color: {DORADO};
          color: {BG_APP};
          }}
        """)
        btn_calc.clicked.connect(self._abrir_calculadora)
        top.addWidget(btn_calc)

        btn_cerrar = QPushButton("✕")
        
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setFixedSize(28, 28)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        top.addWidget(btn_cerrar)
        layout.addLayout(top)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_dashboard(), "Dashboard")
        self.tabs.addTab(self._tab_transacciones(), "Transacciones")
        self.tabs.addTab(self._tab_presupuestos(), "Presupuestos")
        self.tabs.addTab(self._tab_ahorros(), "Ahorros")
        self.tabs.addTab(self._tab_categorias(), "Categorías")
        layout.addWidget(self.tabs)
        root.addWidget(contenedor)
    
    # ── Dashboard ──────────────────────────────────────────
    def _tab_dashboard(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        self.lbl_saldo = QLabel("0,00 €")
        self.lbl_saldo.setObjectName("saldo")
        self.lbl_saldo.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_saldo)
        cards = QHBoxLayout()
        self.card_ingresos = self._card("Ingresos", "0,00 €", POSITIVO)
        self.card_gastos = self._card("Gastos", "0,00 €", PELIGRO)
        self.card_balance = self._card("Balance", "0,00 €", DORADO)
        cards.addWidget(self.card_ingresos["frame"])
        cards.addWidget(self.card_gastos["frame"])
        cards.addWidget(self.card_balance["frame"])
        lay.addLayout(cards)
        lay.addWidget(QLabel("Gastos por categoría (mes actual)"))
        self.contenedor_categorias = QVBoxLayout()
        lay.addLayout(self.contenedor_categorias)
        lay.addStretch()
        return w
    
    def _card(self, titulo, valor, color):
        frame = QFrame()
        frame.setObjectName("panel")
        frame.setStyleSheet(f"#panel {{ border-left: 3px solid {color}; }}")
        l = QVBoxLayout(frame)
        l.setContentsMargins(12, 10, 12, 10)
        t = QLabel(titulo)
        t.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        v = QLabel(valor)
        v.setStyleSheet(f"color:{color}; font-size:20px; font-weight:700;")
        l.addWidget(t)
        l.addWidget(v)
        return {"frame": frame, "valor": v}
    
    # ── Transacciones ──────────────────────────────────────
    def _tab_transacciones(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        form = QHBoxLayout()
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["gasto", "ingreso"])
        self.combo_tipo.setFixedWidth(90)
        self.input_monto = QDoubleSpinBox()
        self.input_monto.setDecimals(2)
        self.input_monto.setMaximum(9999999)
        self.input_monto.setPrefix("€ ")
        self.input_monto.setFixedWidth(110)
        self.combo_categoria = QComboBox()
        self._recargar_categorias_combo()
        self.combo_tipo.currentTextChanged.connect(self._recargar_categorias_combo)
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descripción (opcional)")
        btn_add = QPushButton("+ Añadir")
        btn_add.setObjectName("btn_primario")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._agregar_desde_form)
        form.addWidget(self.combo_tipo)
        form.addWidget(self.input_monto)
        form.addWidget(self.combo_categoria)
        form.addWidget(self.input_desc, 1)
        form.addWidget(btn_add)
        lay.addLayout(form)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Tipo", "Categoría", "Monto", "Descripción"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._menu_tabla)
        lay.addWidget(self.tabla, 1)
        return w
    
    def _recargar_categorias_combo(self):
        tipo = self.combo_tipo.currentText()
        self.combo_categoria.clear()
        for cat in gestor.listar_categorias(tipo=tipo):
            self.combo_categoria.addItem(cat["nombre"])
    
    def _agregar_desde_form(self):
        monto = self.input_monto.value()
        if monto <= 0:
            return
        ok, msg = gestor.agregar_transaccion(
            tipo=self.combo_tipo.currentText(),
            monto=monto,
            categoria=self.combo_categoria.currentText(),
            descripcion=self.input_desc.text().strip(),
        )
        if ok:
            self.input_monto.setValue(0)
            self.input_desc.clear()
            self._refrescar_todo()
            if self.maria:
                self.maria.agregar_b(f"💰 {msg}", False)
    
    def _menu_tabla(self, pos):
        fila = self.tabla.rowAt(pos.y())
        if fila < 0:
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{BG_PANEL}; color:{TEXTO_PRINCIPAL}; border:1px solid {BORDE}; border-radius:6px; padding:4px; }}
            QMenu::item {{ padding:6px 20px; }}
            QMenu::item:selected {{ background:{BG_INPUT}; }}
        """)
        acc = menu.addAction("Eliminar transacción")
        accion = menu.exec_(self.tabla.mapToGlobal(pos))
        if accion == acc:
            id_ = self.tabla.item(fila, 0).data(Qt.UserRole)
            gestor.eliminar_transaccion(id_)
            self._refrescar_todo()
    
    # ── Presupuestos ───────────────────────────────────────
    def _tab_presupuestos(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        form = QHBoxLayout()
        self.combo_pres_cat = QComboBox()
        self._recargar_categorias_presupuesto()
        self.input_limite = QDoubleSpinBox()
        self.input_limite.setDecimals(2)
        self.input_limite.setMaximum(999999)
        self.input_limite.setPrefix("€ ")
        btn = QPushButton("Fijar límite mensual")
        btn.setObjectName("btn_primario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._fijar_presupuesto)
        form.addWidget(QLabel("Categoría:"))
        form.addWidget(self.combo_pres_cat)
        form.addWidget(QLabel("Límite:"))
        form.addWidget(self.input_limite)
        form.addWidget(btn)
        form.addStretch()
        lay.addLayout(form)
        self.contenedor_presupuestos = QVBoxLayout()
        lay.addLayout(self.contenedor_presupuestos)
        lay.addStretch()
        return w
    
    def _recargar_categorias_presupuesto(self):
        self.combo_pres_cat.clear()
        for cat in gestor.listar_categorias(tipo="gasto"):
            self.combo_pres_cat.addItem(cat["nombre"])
    
    def _fijar_presupuesto(self):
        cat = self.combo_pres_cat.currentText()
        limite = self.input_limite.value()
        if limite <= 0 or not cat:
            return
        ahora = datetime.now()
        gestor.fijar_presupuesto(cat, limite, ahora.month, ahora.year)
        self.input_limite.setValue(0)
        self._refrescar_presupuestos()
    
    # ── AHORROS (METAS) ────────────────────────────────────
    def _tab_ahorros(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        # Resumen superior
        resumen = QHBoxLayout()
        self.lbl_total_ahorrado = QLabel("0,00 €")
        self.lbl_total_ahorrado.setStyleSheet(f"color:{POSITIVO}; font-size:18px; font-weight:700;")
        self.lbl_total_pendiente = QLabel("0,00 €")
        self.lbl_total_pendiente.setStyleSheet(f"color:{DORADO}; font-size:18px; font-weight:700;")
        card_ahorrado = self._card_mini("Total ahorrado", self.lbl_total_ahorrado, POSITIVO)
        card_pendiente = self._card_mini("Objetivo pendiente", self.lbl_total_pendiente, DORADO)
        resumen.addWidget(card_ahorrado)
        resumen.addWidget(card_pendiente)
        lay.addLayout(resumen)
        # Formulario crear meta
        form = QHBoxLayout()
        self.input_meta_nombre = QLineEdit()
        self.input_meta_nombre.setPlaceholderText("Nombre de la meta:")
        self.input_meta_objetivo = QDoubleSpinBox()
        self.input_meta_objetivo.setDecimals(2)
        self.input_meta_objetivo.setMaximum(9999999)
        self.input_meta_objetivo.setPrefix("€ ")
        self.input_meta_objetivo.setFixedWidth(120)
        self.input_meta_fecha = QDateEdit()
        self.input_meta_fecha.setCalendarPopup(True)
        self.input_meta_fecha.setDate(datetime.now().date())
        self.input_meta_fecha.setDisplayFormat("dd/MM/yyyy")
        self.input_meta_fecha.setFixedWidth(110)
        # Checkbox "sin objetivo fijo"
        self.chk_sin_objetivo = QCheckBox("💭 Sin objetivo")
        self.chk_sin_objetivo.setStyleSheet(f"color:{DORADO}; font-size:11px;")
        self.chk_sin_objetivo.toggled.connect(self._toggle_objetivo_meta)
        # Checkbox "sin fecha límite"
        self.chk_sin_limite = QCheckBox("📅 Sin fecha")
        self.chk_sin_limite.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        self.chk_sin_limite.toggled.connect(self._toggle_fecha_meta)
        btn_crear = QPushButton("+ Crear meta")
        btn_crear.setObjectName("btn_primario")
        btn_crear.setCursor(Qt.PointingHandCursor)
        btn_crear.clicked.connect(self._crear_meta)
        form.addWidget(self.input_meta_nombre, 2)
        form.addWidget(self.input_meta_objetivo)
        form.addWidget(self.chk_sin_objetivo)
        form.addWidget(self.input_meta_fecha)
        form.addWidget(self.chk_sin_limite)
        form.addWidget(btn_crear)
        lay.addLayout(form)
        # Lista de metas
        self.contenedor_metas = QVBoxLayout()
        lay.addLayout(self.contenedor_metas)
        lay.addStretch()
        return w
    
    def _toggle_objetivo_meta(self, activado):
        """Deshabilita el QDoubleSpinBox del objetivo cuando se marca 'sin objetivo'."""
        self.input_meta_objetivo.setEnabled(not activado)
    
    def _toggle_fecha_meta(self, activado):
        """Deshabilita el QDateEdit cuando se marca 'sin fecha límite'."""
        self.input_meta_fecha.setEnabled(not activado)
    
    def _card_mini(self, titulo, valor_widget, color):
        frame = QFrame()
        frame.setObjectName("panel")
        frame.setStyleSheet(f"#panel {{ border-left: 3px solid {color}; }}")
        l = QVBoxLayout(frame)
        l.setContentsMargins(12, 8, 12, 8)
        t = QLabel(titulo)
        t.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
        l.addWidget(t)
        l.addWidget(valor_widget)
        return frame
    
    def _crear_meta(self):
        nombre = self.input_meta_nombre.text().strip()
        if not nombre:
            return
        # Objetivo: None si está marcado, si no el valor del spinbox
        if self.chk_sin_objetivo.isChecked():
            objetivo = None
        else:
            objetivo = self.input_meta_objetivo.value()
            if objetivo <= 0:
                return
        # Fecha: None si está marcado, si no la fecha
        if self.chk_sin_limite.isChecked():
            fecha = None
        else:
            fecha = self.input_meta_fecha.date().toString("yyyy-MM-dd")
        ok, msg = gestor.crear_meta(nombre, objetivo=objetivo, fecha_limite=fecha)
        if ok:
            self.input_meta_nombre.clear()
            self.input_meta_objetivo.setValue(0)
            self.chk_sin_objetivo.setChecked(False)
            self.input_meta_objetivo.setEnabled(True)
            self.chk_sin_limite.setChecked(False)
            self.input_meta_fecha.setEnabled(True)
            self._refrescar_ahorros()
            if self.maria:
                self.maria.agregar_b(f"🎯 {msg}", False)
    
    def _aportar_a_meta(self, id_meta, nombre):
        """Abre el diálogo personalizado cálido para aportar a una meta."""
        metas = gestor.listar_metas()
        meta = next((m for m in metas if m["id"] == id_meta), None)
        if not meta:
            return
        actual = float(meta["actual"])
        objetivo = meta["objetivo"]  # Puede ser None
        fecha_limite = meta["fecha_limite"]
        dlg = DialogoAportar(self, nombre, actual, objetivo, fecha_limite)
        if dlg.exec_() == QDialog.Accepted:
            cantidad = dlg.get_cantidad()
            if cantidad > 0:
                gestor.aportar_a_meta(id_meta, cantidad)
                self._refrescar_ahorros()
                if self.maria:
                    self.maria.agregar_b(f" Aportados {cantidad:.2f}€ a la meta '{nombre}'.", False)
    
    def _editar_meta(self, id_meta, nombre, objetivo, fecha_limite):
        """Abre el diálogo para editar nombre/objetivo/fecha de una meta."""
        dlg = DialogoEditarMeta(self, nombre, objetivo, fecha_limite)
        if dlg.exec_() == QDialog.Accepted:
            resultado = dlg.get_resultado()
            if resultado:
                nuevo_nombre, nuevo_objetivo, nueva_fecha = resultado
                metas = gestor.listar_metas()
                meta = next((m for m in metas if m["id"] == id_meta), None)
                if meta:
                    actual = float(meta["actual"])
                    gestor.eliminar_meta(id_meta)
                    with gestor._conexion() as c:
                        c.execute(
                            "INSERT INTO metas (id, nombre, objetivo, actual, fecha_limite) "
                            "VALUES (?,?,?,?,?)",
                            (id_meta, nuevo_nombre, nuevo_objetivo, actual, nueva_fecha),
                        )
                    self._refrescar_ahorros()
                    if self.maria:
                        self.maria.agregar_b(f"✏️ Meta '{nuevo_nombre}' actualizada.", False)
    
    def _eliminar_meta(self, id_meta, nombre):
        resp = QMessageBox.question(
            self, "Eliminar meta",
            f"¿Seguro que quieres eliminar la meta '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            gestor.eliminar_meta(id_meta)
            self._refrescar_ahorros()
    
    # ── Categorías ────────────────────────────────────────
    def _tab_categorias(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        form = QHBoxLayout()
        self.input_cat_nombre = QLineEdit()
        self.input_cat_nombre.setPlaceholderText("Nombre de la categoría")
        self.combo_cat_tipo = QComboBox()
        self.combo_cat_tipo.addItems(["gasto", "ingreso"])
        btn = QPushButton("+ Crear")
        btn.setObjectName("btn_primario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._crear_categoria)
        form.addWidget(self.input_cat_nombre, 1)
        form.addWidget(self.combo_cat_tipo)
        form.addWidget(btn)
        lay.addLayout(form)
        self.contenedor_cats = QVBoxLayout()
        lay.addLayout(self.contenedor_cats)
        lay.addStretch()
        return w

    def _abrir_calculadora(self):
     """Abre la calculadora mental (no guarda nada en la BD)."""
     dlg = DialogoCalculadoraDinero(self)
     dlg.setAttribute(Qt.WA_DeleteOnClose) 
     dlg.show()
    
    def _crear_categoria(self):
        nombre = self.input_cat_nombre.text().strip()
        if not nombre:
            return
        ok, msg = gestor.agregar_categoria(nombre, self.combo_cat_tipo.currentText())
        self.input_cat_nombre.clear()
        self._refrescar_categorias()
        self._recargar_categorias_combo()
        self._recargar_categorias_presupuesto()
    
    # ─ Refrescos ──────────────────────────────────────────
    def _refrescar_todo(self):
        ahora = datetime.now()
        self._refrescar_dashboard(ahora.month, ahora.year)
        self._refrescar_tabla()
        self._refrescar_presupuestos()
        self._refrescar_ahorros()
        self._refrescar_categorias()
    
    def _refrescar_dashboard(self, mes, anio):
        b = gestor.balance(mes=mes, anio=anio)
        self.lbl_saldo.setText(fmt_euros(b["balance"]))
        self.lbl_saldo.setStyleSheet(
            (f"color:{POSITIVO};" if b["balance"] >= 0 else f"color:{NEGATIVO};")
            + "font-size:28px; font-weight:700;"
        )
        self.card_ingresos["valor"].setText(fmt_euros(b["ingresos"]))
        self.card_gastos["valor"].setText(fmt_euros(b["gastos"]))
        self.card_balance["valor"].setText(fmt_euros(b["balance"]))
        while self.contenedor_categorias.count():
            item = self.contenedor_categorias.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        gastos_cat = gestor.gastos_por_categoria(mes=mes, anio=anio)
        max_gasto = int(max((g["total"] for g in gastos_cat), default=1) or 1)
        for g in gastos_cat:
            fila = QHBoxLayout()
            lbl = QLabel(f"{g['categoria']}: {fmt_euros(g['total'])}")
            lbl.setFixedWidth(200)
            bar = QProgressBar()
            bar.setMaximum(max_gasto)
            bar.setValue(int(g["total"]))
            bar.setFormat(f"{g['total']/max_gasto*100:.0f}%")
            fila.addWidget(lbl)
            fila.addWidget(bar, 1)
            cont = QWidget()
            cont.setLayout(fila)
            self.contenedor_categorias.addWidget(cont)
    
    def _refrescar_tabla(self):
        trans = gestor.listar_transacciones(limite=100)
        self.tabla.setRowCount(len(trans))
        for r, t in enumerate(trans):
            fecha_item = QTableWidgetItem(t["fecha"])
            fecha_item.setData(Qt.UserRole, t["id"])
            self.tabla.setItem(r, 0, fecha_item)
            self.tabla.setItem(r, 1, QTableWidgetItem(t["tipo"].capitalize()))
            self.tabla.setItem(r, 2, QTableWidgetItem(t["categoria"]))
            signo = "-" if t["tipo"] == "gasto" else "+"
            color = PELIGRO if t["tipo"] == "gasto" else POSITIVO
            monto_item = QTableWidgetItem(f"{signo}{fmt_euros(t['monto'])}")
            monto_item.setForeground(QColor(color))
            self.tabla.setItem(r, 3, monto_item)
            self.tabla.setItem(r, 4, QTableWidgetItem(t["descripcion"] or ""))
    
    def _refrescar_presupuestos(self):
        while self.contenedor_presupuestos.count():
            item = self.contenedor_presupuestos.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        ahora = datetime.now()
        for p in gestor.estado_presupuestos(ahora.month, ahora.year):
            fila = QHBoxLayout()
            lbl = QLabel(f"{p['categoria']}: {fmt_euros(p['gastado'])} / {fmt_euros(p['limite'])}")
            lbl.setFixedWidth(280)
            bar = QProgressBar()
            bar.setMaximum(100)
            bar.setValue(min(100, int(p["porcentaje"])))
            if p["porcentaje"] >= 100:
                bar.setStyleSheet(f"QProgressBar::chunk {{ background-color:{PELIGRO}; }}")
            elif p["porcentaje"] >= 80:
                bar.setStyleSheet(f"QProgressBar::chunk {{ background-color:#d4a85a; }}")
            fila.addWidget(lbl)
            fila.addWidget(bar, 1)
            restante = QLabel(f"Restan {fmt_euros(p['restante'])}")
            restante.setStyleSheet(f"color:{TEXTO_SECUNDARIO};")
            fila.addWidget(restante)
            cont = QWidget()
            cont.setLayout(fila)
            self.contenedor_presupuestos.addWidget(cont)
    
    def _refrescar_ahorros(self):
        """Redibuja la lista de metas de ahorro."""
        while self.contenedor_metas.count():
            item = self.contenedor_metas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        metas = gestor.listar_metas()
        total_ahorrado = 0.0
        total_objetivo = 0.0
        hoy = datetime.now().date()
        if not metas:
            vacio = QLabel("No hay metas de ahorro. Crea una arriba para empezar.")
            vacio.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:12px; font-style:italic; padding:14px;")
            vacio.setAlignment(Qt.AlignCenter)
            self.contenedor_metas.addWidget(vacio)
        else:
            for m in metas:
                id_meta = m["id"]
                nombre = m["nombre"]
                objetivo = m["objetivo"]  # Puede ser None
                actual = float(m["actual"])
                fecha_lim = m["fecha_limite"]
                total_ahorrado += actual
                # Calcular días restantes (solo si hay fecha límite)
                dias_restantes = None
                if fecha_lim:
                    try:
                        f_lim = datetime.strptime(fecha_lim, "%Y-%m-%d").date()
                        dias_restantes = (f_lim - hoy).days
                    except Exception:
                        pass
                # Tarjeta de la meta
                card = QFrame()
                card.setObjectName("card_meta")
                if objetivo is not None:
                    # Meta con objetivo fijo
                    porcentaje = (actual / objetivo * 100) if objetivo > 0 else 0
                    restante = max(0.0, objetivo - actual)
                    total_objetivo += objetivo
                    completada = porcentaje >= 100
                    if completada:
                        card.setProperty("class", "completada")
                        card.setStyleSheet(f"""
                            #card_meta {{ background-color:#1a241f; border:1px solid {DORADO}; border-radius:8px; }}
                        """)
                else:
                    # Meta sin objetivo fijo (ahorro libre)
                    porcentaje = None
                    restante = None
                    completada = False
                    card.setProperty("class", "libre")
                    card.setStyleSheet(f"""
                        #card_meta {{ background-color:#1d242b; border:1px solid #3a4a5c; border-radius:8px; }}
                    """)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(12, 10, 12, 10)
                card_layout.setSpacing(6)
                # Fila superior: nombre + fecha + botones
                top = QHBoxLayout()
                if objetivo is not None:
                    lbl_nombre = QLabel(f"🎯  {nombre}")
                else:
                    lbl_nombre = QLabel(f"💰  {nombre}")
                lbl_nombre.setStyleSheet(f"color:{TEXTO_PRINCIPAL}; font-size:13px; font-weight:600;")
                top.addWidget(lbl_nombre)
                # Indicador de fecha (o "sin límite")
                if fecha_lim and dias_restantes is not None:
                    if dias_restantes < 0:
                        texto_fecha = f"⚠️ Vencida hace {abs(dias_restantes)} días"
                        color_fecha = PELIGRO
                    elif dias_restantes == 0:
                        texto_fecha = "️ ¡Hoy es el límite!"
                        color_fecha = "#d4a85a"
                    elif dias_restantes <= 30:
                        texto_fecha = f"🕐 Faltan {dias_restantes} días"
                        color_fecha = "#d4a85a"
                    else:
                        texto_fecha = f"📅 Faltan {dias_restantes} días"
                        color_fecha = TEXTO_SECUNDARIO
                    lbl_fecha = QLabel(texto_fecha)
                    lbl_fecha.setStyleSheet(f"color:{color_fecha}; font-size:11px;")
                    top.addWidget(lbl_fecha)
                else:
                    # Sin fecha límite
                    lbl_fecha = QLabel("📅 Sin límite")
                    lbl_fecha.setStyleSheet(f"color:{TEXTO_TERCIARIO}; font-size:11px; font-style:italic;")
                    top.addWidget(lbl_fecha)
                top.addStretch()
                # Monto: diferente si hay objetivo o no
                if objetivo is not None:
                    lbl_monto = QLabel(f"{fmt_euros(actual)} / {fmt_euros(objetivo)}")
                else:
                    lbl_monto = QLabel(f"💰 {fmt_euros(actual)}")
                lbl_monto.setStyleSheet(f"color:{TEXTO_PRINCIPAL}; font-size:12px; font-weight:600;")
                top.addWidget(lbl_monto)
                # Botón editar
                btn_editar = QPushButton("✏️")
                btn_editar.setObjectName("btn_secundario")
                btn_editar.setCursor(Qt.PointingHandCursor)
                btn_editar.setFixedSize(28, 28)
                btn_editar.setToolTip("Editar meta")
                btn_editar.clicked.connect(
                    lambda _, i=id_meta, n=nombre, o=objetivo, fl=fecha_lim:
                    self._editar_meta(i, n, o, fl)
                )
                top.addWidget(btn_editar)
                btn_aportar = QPushButton("+ Aportar")
                btn_aportar.setObjectName("btn_secundario")
                btn_aportar.setCursor(Qt.PointingHandCursor)
                btn_aportar.setFixedWidth(85)
                btn_aportar.clicked.connect(
                    lambda _, i=id_meta, n=nombre: self._aportar_a_meta(i, n)
                )
                top.addWidget(btn_aportar)
                btn_eliminar = QPushButton("✕")
                btn_eliminar.setObjectName("btn_peligro")
                btn_eliminar.setCursor(Qt.PointingHandCursor)
                btn_eliminar.setFixedSize(28, 28)
                btn_eliminar.setToolTip("Eliminar meta")
                btn_eliminar.clicked.connect(
                    lambda _, i=id_meta, n=nombre: self._eliminar_meta(i, n)
                )
                top.addWidget(btn_eliminar)
                card_layout.addLayout(top)
                # Barra de progreso (solo si hay objetivo)
                if objetivo is not None:
                    bar = QProgressBar()
                    bar.setMaximum(100)
                    bar.setValue(min(100, int(porcentaje)))
                    bar.setFormat(f"{porcentaje:.1f}%")
                    if porcentaje >= 100:
                        bar.setStyleSheet(f"""
                            QProgressBar {{ border:none; background:{BG_INPUT}; border-radius:5px; height:10px; }}
                            QProgressBar::chunk {{ background-color:{DORADO}; border-radius:5px; }}
                        """)
                    elif porcentaje >= 70:
                        bar.setStyleSheet(f"""
                            QProgressBar {{ border:none; background:{BG_INPUT}; border-radius:5px; height:10px; }}
                            QProgressBar::chunk {{ background-color:{ACENTO}; border-radius:5px; }}
                        """)
                    elif porcentaje >= 40:
                        bar.setStyleSheet(f"""
                            QProgressBar {{ border:none; background:{BG_INPUT}; border-radius:5px; height:10px; }}
                            QProgressBar::chunk {{ background-color:{DORADO}; border-radius:5px; }}
                        """)
                    else:
                        bar.setStyleSheet(f"""
                            QProgressBar {{ border:none; background:{BG_INPUT}; border-radius:5px; height:10px; }}
                            QProgressBar::chunk {{ background-color:{TEXTO_SECUNDARIO}; border-radius:5px; }}
                        """)
                    card_layout.addWidget(bar)
                    # Pie: estado
                    if porcentaje >= 100:
                        lbl_estado = QLabel("🎉 ¡Meta completada!")
                        lbl_estado.setStyleSheet(f"color:{DORADO}; font-size:11px; font-weight:700;")
                    else:
                        lbl_estado = QLabel(f"Faltan {fmt_euros(restante)}")
                        lbl_estado.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:11px;")
                    card_layout.addWidget(lbl_estado)
                else:
                    # Sin objetivo: mostrar total acumulado en grande
                    lbl_acumulado = QLabel(f"Acumulado: {fmt_euros(actual)}")
                    lbl_acumulado.setStyleSheet(f"color:{DORADO}; font-size:12px; font-weight:600;")
                    card_layout.addWidget(lbl_acumulado)
                    lbl_libre = QLabel("Ahorro libre · decide cuando quieras")
                    lbl_libre.setStyleSheet(f"color:{TEXTO_TERCIARIO}; font-size:10px; font-style:italic;")
                    card_layout.addWidget(lbl_libre)
                self.contenedor_metas.addWidget(card)
        # Actualizar resumen superior
        self.lbl_total_ahorrado.setText(fmt_euros(total_ahorrado))
        self.lbl_total_pendiente.setText(fmt_euros(max(0.0, total_objetivo - total_ahorrado)))
    
    def _refrescar_categorias(self):
        while self.contenedor_cats.count():
            item = self.contenedor_cats.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for tipo in ("ingreso", "gasto"):
            header = QLabel(f"  {tipo.upper()}S")
            header.setStyleSheet(f"color:{TEXTO_SECUNDARIO}; font-size:10px; font-weight:700;")
            self.contenedor_cats.addWidget(header)
            for cat in gestor.listar_categorias(tipo=tipo):
                lbl = QLabel(f"●  {cat['nombre']}")
                lbl.setStyleSheet(f"color:{cat['color']};")
                self.contenedor_cats.addWidget(lbl)
    
    # ─ Arrastre ───────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)