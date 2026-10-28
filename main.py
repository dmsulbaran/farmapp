import sys
import sqlite3
import csv
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                               QWidget, QPushButton, QLineEdit, QSpinBox, 
                               QDoubleSpinBox, QFormLayout, QMessageBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QFileDialog, QTabWidget, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QShortcut, QKeySequence
from database import init_local_db

class FarmAppAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FarmApp - Sistema Administrativo (Fase 3: Facturación Activa)")
        self.resize(1000, 750)

        init_local_db()
        self.current_total = 0.0 # Variable para llevar la cuenta de la factura

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.setStyleSheet("QTabBar::tab { padding: 10px; font-size: 14px; font-weight: bold; }")

        self.tab_pos = QWidget()
        self.tab_inventory = QWidget()

        self.tabs.addTab(self.tab_pos, "💰 Punto de Venta (Caja)")
        self.tabs.addTab(self.tab_inventory, "📦 Gestión de Inventario")

        self.build_pos_tab()
        self.build_inventory_tab()
        self.load_inventory()

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
        self.input_barcode.setPlaceholderText("Escanea el código, escribe el ID o nombre y presiona ENTER...")
        self.input_barcode.setStyleSheet("padding: 15px; font-size: 18px; border: 2px solid #3498db; border-radius: 5px;")
        
        # MAGIA AQUÍ: Al presionar Enter, procesa el producto
        self.input_barcode.returnPressed.connect(self.process_barcode)
        scan_layout.addWidget(self.input_barcode)

        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(5)
        self.pos_table.setHorizontalHeaderLabels(["Cód.", "Descripción del Producto", "Cant.", "Precio Unit.", "Subtotal"])
        self.pos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        shortcuts_layout = QGridLayout()
        btn_f2 = QPushButton("F2 - Buscar")
        btn_f2.setStyleSheet("padding: 10px; background-color: #34495e; color: white; font-weight: bold; font-size: 14px;")
        btn_f4 = QPushButton("F4 - Descuento")
        btn_f4.setStyleSheet("padding: 10px; background-color: #9b59b6; color: white; font-weight: bold; font-size: 14px;")
        btn_f8 = QPushButton("F8 - Pago")
        btn_f8.setStyleSheet("padding: 10px; background-color: #f39c12; color: white; font-weight: bold; font-size: 14px;")
        btn_f12 = QPushButton("F12 - COBRAR E IMPRIMIR")
        btn_f12.setStyleSheet("padding: 10px; background-color: #e74c3c; color: white; font-weight: bold; font-size: 16px;")

        shortcuts_layout.addWidget(btn_f2, 0, 0)
        shortcuts_layout.addWidget(btn_f4, 0, 1)
        shortcuts_layout.addWidget(btn_f8, 0, 2)
        shortcuts_layout.addWidget(btn_f12, 0, 3)

        layout.addWidget(self.pos_total_label)
        layout.addLayout(scan_layout)
        layout.addWidget(self.pos_table)
        layout.addLayout(shortcuts_layout)
        self.tab_pos.setLayout(layout)

    # --- LÓGICA DE ESCANEO Y FACTURACIÓN ---
    def process_barcode(self):
        query = self.input_barcode.text().strip()
        if not query: return
        
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            # Buscamos si coincide con el ID exacto o si parte del nombre se parece
            cursor.execute('SELECT id, product_name, price, stock FROM inventory WHERE id = ? OR product_name LIKE ?', (query, f"%{query}%"))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                item_id, name, price, stock = result
                
                # Insertar nueva fila en la factura
                row_count = self.pos_table.rowCount()
                self.pos_table.insertRow(row_count)
                
                self.pos_table.setItem(row_count, 0, QTableWidgetItem(str(item_id)))
                self.pos_table.setItem(row_count, 1, QTableWidgetItem(name))
                self.pos_table.setItem(row_count, 2, QTableWidgetItem("1"))
                self.pos_table.setItem(row_count, 3, QTableWidgetItem(f"$ {price:.2f}"))
                self.pos_table.setItem(row_count, 4, QTableWidgetItem(f"$ {price:.2f}"))
                
                # Actualizar el total gigante
                self.current_total += price
                self.pos_total_label.setText(f"TOTAL: $ {self.current_total:.2f}")
                
                # Limpiar la barra para el siguiente escaneo
                self.input_barcode.clear()
            else:
                QMessageBox.warning(self, "No encontrado", f"No hay stock o no existe: '{query}'")
                self.input_barcode.clear()
                
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))

    # --- ATAJOS Y EL RESTO DEL CÓDIGO (Fase 1 y 2) ---
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
        self.btn_save.setStyleSheet("padding: 8px; background-color: #2ecc71; color: white; font-weight: bold;")
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

    def shortcut_f2_search(self):
        self.tabs.setCurrentIndex(0)
        self.input_barcode.setFocus()
        QMessageBox.information(self, "Buscador Inteligente", "Has presionado F2.\nLa barra de escaneo está lista.")

    def shortcut_f4_discount(self):
        self.tabs.setCurrentIndex(0)
        QMessageBox.warning(self, "Aplicar Descuento", "Has presionado F4.\nAquí el gerente autorizará descuentos.")

    def shortcut_f8_payment(self):
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(self, "Método de Pago", f"Has presionado F8.\nMonto a cobrar: $ {self.current_total:.2f}")

    def shortcut_f12_checkout(self):
        self.tabs.setCurrentIndex(0)
        QMessageBox.critical(self, "Facturar e Imprimir", "Has presionado F12.\n¡Venta procesada y ticket enviado a impresión!")
        # Reiniciar factura
        self.pos_table.setRowCount(0)
        self.current_total = 0.0
        self.pos_total_label.setText("TOTAL: $ 0.00")

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo CSV", "", "Archivos CSV (*.csv)")
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
            QMessageBox.information(self, "Éxito", "Importación masiva completada.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def filter_table(self, text):
        for row in range(self.inventory_table.rowCount()):
            item = self.inventory_table.item(row, 1)
            if item:
                self.inventory_table.setRowHidden(row, not (text.lower() in item.text().lower()))

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
                    item_stock.setBackground(QColor("#e74c3c"))
                    item_stock.setForeground(QColor("white"))
                elif stock_value <= 15:
                    item_stock.setBackground(QColor("#f1c40f"))
                    item_stock.setForeground(QColor("black"))
                else:
                    item_stock.setBackground(QColor("#2ecc71"))
                    item_stock.setForeground(QColor("white"))
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
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FarmAppAdmin()
    window.show()
    sys.exit(app.exec())