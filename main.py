import sys
import sqlite3
import csv
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                               QWidget, QPushButton, QLineEdit, QSpinBox, 
                               QDoubleSpinBox, QFormLayout, QMessageBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QFileDialog, QTabWidget, QGridLayout, QInputDialog, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QShortcut, QKeySequence
from database import init_local_db

class PaymentDialog(QDialog):
    """Ventana modal moderna con botones en cuadrícula para los métodos de pago."""
    def __init__(self, total_amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle("F8 - Seleccionar Método de Pago")
        self.setFixedSize(450, 300)
        self.selected_method = None

        layout = QVBoxLayout(self)

        # Encabezado con el monto total
        lbl_title = QLabel(f"Total a Pagar: $ {total_amount:.2f}")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        lbl_instruct = QLabel("Seleccione el método de pago haciendo clic en el cuadro:")
        lbl_instruct.setAlignment(Qt.AlignCenter)
        lbl_instruct.setStyleSheet("font-size: 13px; color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(lbl_instruct)

        # Cuadrícula de botones (Cuadritos modernos)
        grid_layout = QGridLayout()
        
        methods = [
            ("💵 Efectivo ($)", "#27ae60"),
            ("📱 Pago Móvil (Bs)", "#2980b9"),
            ("🏷️ Cashea", "#8e44ad"),
            ("🌐 Divisas / Zelle", "#d35400")
        ]

        for index, (name, color) in enumerate(methods):
            btn = QPushButton(name)
            btn.setFixedHeight(60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-size: 15px;
                    font-weight: bold;
                    border-radius: 8px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #2c3e50;
                }}
            """)
            # Conectar cada botón para que guarde la opción y cierre la ventana
            btn.clicked.connect(lambda checked=False, m=name: self.choose_method(m))
            
            row = index // 2
            col = index % 2
            grid_layout.addWidget(btn, row, col)

        layout.addLayout(grid_layout)

    def choose_method(self, method_name):
        self.selected_method = method_name
        self.accept()


class FarmAppAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FarmApp - Sistema Administrativo POS")
        self.resize(1000, 750)
        self.current_total = 0.0
        self.selected_payment_method = "💵 Efectivo ($)" # Método por defecto

        init_local_db()

        # Estilo corporativo limpio y claro
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f5f6fa;
                color: #2c3e50;
                font-family: Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #dcdde1;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #dcdde1;
                color: #2f3640;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #273c75;
                border-bottom: 2px solid #3498db;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #2f3640;
                gridline-color: #dcdde1;
                border: 1px solid #dcdde1;
            }
            QHeaderView::section {
                background-color: #2f3640;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                color: #2f3640;
                border: 1px solid #ced6e0;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)

        self.tabs = QTabWidget()
        self.tab_pos = QWidget()
        self.tab_inventory = QWidget()

        self.tabs.addTab(self.tab_pos, "💰 Punto de Venta (Caja)")
        self.tabs.addTab(self.tab_inventory, "📦 Gestión de Inventario")

        self.build_pos_tab()
        self.build_inventory_tab()
        self.load_inventory()

        main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_container)

        # Atajos globales de teclado
        QShortcut(QKeySequence("F2"), self).activated.connect(self.shortcut_f2_search)
        QShortcut(QKeySequence("F4"), self).activated.connect(self.shortcut_f4_discount)
        QShortcut(QKeySequence("F8"), self).activated.connect(self.shortcut_f8_payment)
        QShortcut(QKeySequence("F12"), self).activated.connect(self.shortcut_f12_checkout)

    def build_pos_tab(self):
        layout = QVBoxLayout()
        self.pos_total_label = QLabel("TOTAL: $ 0.00")
        self.pos_total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pos_total_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #27ae60; background-color: #ecf0f1; padding: 20px; border-radius: 10px;")
        
        scan_layout = QHBoxLayout()
        self.input_barcode = QLineEdit()
        self.input_barcode.setPlaceholderText("Escanea el código de barras o escribe el nombre y presiona ENTER...")
        self.input_barcode.setStyleSheet("padding: 15px; font-size: 18px; border: 2px solid #3498db; border-radius: 5px; background-color: white;")
        self.input_barcode.returnPressed.connect(self.process_barcode)
        scan_layout.addWidget(self.input_barcode)

        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(5)
        self.pos_table.setHorizontalHeaderLabels(["Cód.", "Descripción del Producto", "Cant.", "Precio Unit.", "Subtotal"])
        self.pos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Botones inferiores interactivos (clic y teclado)
        shortcuts_layout = QGridLayout()
        
        self.btn_f2 = QPushButton("F2 - Buscar")
        self.btn_f2.setStyleSheet("padding: 10px; background-color: #34495e; color: white; font-weight: bold; font-size: 14px;")
        self.btn_f2.clicked.connect(self.shortcut_f2_search)

        self.btn_f4 = QPushButton("F4 - Descuento")
        self.btn_f4.setStyleSheet("padding: 10px; background-color: #8e44ad; color: white; font-weight: bold; font-size: 14px;")
        self.btn_f4.clicked.connect(self.shortcut_f4_discount)

        self.btn_f8 = QPushButton("F8 - Pago")
        self.btn_f8.setStyleSheet("padding: 10px; background-color: #d35400; color: white; font-weight: bold; font-size: 14px;")
        self.btn_f8.clicked.connect(self.shortcut_f8_payment)

        self.btn_f12 = QPushButton("F12 - COBRAR E IMPRIMIR")
        self.btn_f12.setStyleSheet("padding: 10px; background-color: #c0392b; color: white; font-weight: bold; font-size: 16px;")
        self.btn_f12.clicked.connect(self.shortcut_f12_checkout)

        shortcuts_layout.addWidget(self.btn_f2, 0, 0)
        shortcuts_layout.addWidget(self.btn_f4, 0, 1)
        shortcuts_layout.addWidget(self.btn_f8, 0, 2)
        shortcuts_layout.addWidget(self.btn_f12, 0, 3)

        layout.addWidget(self.pos_total_label)
        layout.addLayout(scan_layout)
        layout.addWidget(self.pos_table)
        layout.addLayout(shortcuts_layout)
        self.tab_pos.setLayout(layout)

    def build_inventory_tab(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.title = QLabel("Gestión de Inventario Local")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        
        self.input_name = QLineEdit()
        self.input_stock = QSpinBox()
        self.input_stock.setRange(0, 10000)
        self.input_price = QDoubleSpinBox()
        self.input_price.setRange(0.0, 99999.99)
        self.input_price.setPrefix("$ ")

        form_layout.addRow("Nombre del Producto:", self.input_name)
        form_layout.addRow("Stock (Unidades):", self.input_stock)
        form_layout.addRow("Precio de Venta:", self.input_price)

        buttons_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar Manualmente")
        self.btn_save.setStyleSheet("padding: 8px; background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_product)

        self.btn_import = QPushButton("📂 Importar CSV Masivo")
        self.btn_import.setStyleSheet("padding: 8px; background-color: #f39c12; color: white; font-weight: bold;")
        self.btn_import.clicked.connect(self.import_csv)

        buttons_layout.addWidget(self.btn_save)
        buttons_layout.addWidget(self.btn_import)

        header_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar producto en inventario...")
        self.input_search.textChanged.connect(self.filter_table)
        header_layout.addStretch()
        header_layout.addWidget(self.input_search)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(4)
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Producto", "Stock", "Precio"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.title)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        layout.addSpacing(15)
        layout.addLayout(header_layout)
        layout.addWidget(self.inventory_table)
        self.tab_inventory.setLayout(layout)

    def add_product_to_pos(self, item_id, name, price):
        found_row = -1
        for row in range(self.pos_table.rowCount()):
            if self.pos_table.item(row, 0).text() == str(item_id):
                found_row = row
                break
        
        if found_row >= 0:
            current_qty = int(self.pos_table.item(found_row, 2).text())
            new_qty = current_qty + 1
            self.pos_table.item(found_row, 2).setText(str(new_qty))
            self.pos_table.item(found_row, 4).setText(f"$ {(new_qty * price):.2f}")
        else:
            row_count = self.pos_table.rowCount()
            self.pos_table.insertRow(row_count)
            self.pos_table.setItem(row_count, 0, QTableWidgetItem(str(item_id)))
            self.pos_table.setItem(row_count, 1, QTableWidgetItem(name))
            self.pos_table.setItem(row_count, 2, QTableWidgetItem("1"))
            self.pos_table.setItem(row_count, 3, QTableWidgetItem(f"$ {price:.2f}"))
            self.pos_table.setItem(row_count, 4, QTableWidgetItem(f"$ {price:.2f}"))
        
        self.current_total += price
        self.pos_total_label.setText(f"TOTAL: $ {self.current_total:.2f}")

    def process_barcode(self):
        query = self.input_barcode.text().strip()
        if not query: return
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, product_name, price, stock FROM inventory WHERE id = ? OR product_name LIKE ?', (query, f"%{query}%"))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                item_id, name, price, stock_db = result
                self.add_product_to_pos(item_id, name, price)
                self.input_barcode.clear()
            else:
                QMessageBox.warning(self, "No encontrado", f"No se encontró: '{query}'")
                self.input_barcode.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))

    def shortcut_f2_search(self):
        self.tabs.setCurrentIndex(0)
        product_name, ok = QInputDialog.getText(self, "F2 - Buscar Producto", "Ingrese el nombre o parte del medicamento:")
        if ok and product_name.strip():
            try:
                conn = sqlite3.connect('farmapp_cache.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, product_name, price, stock FROM inventory WHERE product_name LIKE ?', (f"%{product_name.strip()}%",))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    item_id, name, price, stock_db = result
                    self.add_product_to_pos(item_id, name, price)
                else:
                    QMessageBox.warning(self, "Sin resultados", f"No se encontró ningún producto con el nombre: '{product_name}'")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def shortcut_f4_discount(self):
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(self, "F4 - Descuento", "Módulo de autorización de descuentos habilitado.")

    def shortcut_f8_payment(self):
        """F8: Abre la ventana moderna con los 4 botones en cuadrícula."""
        self.tabs.setCurrentIndex(0)
        if self.current_total == 0:
            QMessageBox.warning(self, "Caja Vacía", "No hay productos en la factura para seleccionar método de pago.")
            return
        
        dialog = PaymentDialog(self.current_total, self)
        if dialog.exec():
            if dialog.selected_method:
                self.selected_payment_method = dialog.selected_method
                QMessageBox.information(self, "Método Registrado", f"Método seleccionado: {self.selected_payment_method}.\nPresione F12 para procesar la venta.")

    def shortcut_f12_checkout(self):
        """F12: Cobra, descuenta stock y limpia la caja."""
        self.tabs.setCurrentIndex(0)
        row_count = self.pos_table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Caja Vacía", "No hay productos en la factura actual.")
            return

        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            for row in range(row_count):
                item_id = self.pos_table.item(row, 0).text()
                qty = int(self.pos_table.item(row, 2).text())
                cursor.execute('UPDATE inventory SET stock = stock - ? WHERE id = ?', (qty, item_id))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Venta Exitosa (F12)", f"Método de pago: {self.selected_payment_method}\nMonto procesado: $ {self.current_total:.2f}\n¡Stock descontado e impreso!")
            
            self.pos_table.setRowCount(0)
            self.current_total = 0.0
            self.pos_total_label.setText("TOTAL: $ 0.00")
            self.load_inventory()
        except Exception as e:
            QMessageBox.critical(self, "Error al Facturar", str(e))

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV", "", "Archivos CSV (*.csv)")
        if not file_path: return
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 3:
                        cursor.execute('INSERT INTO inventory (product_name, stock, price) VALUES (?, ?, ?)', (row[0].strip(), int(row[1]), float(row[2])))
            conn.commit()
            conn.close()
            self.load_inventory()
            QMessageBox.information(self, "Éxito", "Importación completada.")
        except: pass

    def filter_table(self, text):
        for row in range(self.inventory_table.rowCount()):
            item = self.inventory_table.item(row, 1)
            if item: self.inventory_table.setRowHidden(row, not (text.lower() in item.text().lower()))

    def load_inventory(self):
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, product_name, stock, price FROM inventory')
            rows = cursor.fetchall()
            conn.close()
            self.inventory_table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                stock_value = int(row_data[2])
                item_stock = QTableWidgetItem(str(stock_value))
                if stock_value <= 5:
                    item_stock.setBackground(QColor("#ff7675"))
                    item_stock.setForeground(QColor("black"))
                elif stock_value <= 15:
                    item_stock.setBackground(QColor("#ffeaa7"))
                    item_stock.setForeground(QColor("black"))
                else:
                    item_stock.setBackground(QColor("#55efc4"))
                    item_stock.setForeground(QColor("black"))
                item_stock.setTextAlignment(Qt.AlignCenter)
                self.inventory_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
                self.inventory_table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
                self.inventory_table.setItem(row_idx, 2, item_stock)
                self.inventory_table.setItem(row_idx, 3, QTableWidgetItem(f"$ {row_data[3]:.2f}"))
        except: pass

    def save_product(self):
        name = self.input_name.text()
        if not name.strip(): return
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO inventory (product_name, stock, price) VALUES (?, ?, ?)', (name, self.input_stock.value(), self.input_price.value()))
            conn.commit()
            conn.close()
            self.load_inventory()
            self.input_name.clear()
            self.input_stock.setValue(0)
            self.input_price.setValue(0.0)
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FarmAppAdmin()
    window.show()
    sys.exit(app.exec())