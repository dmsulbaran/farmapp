import sys
import sqlite3
import csv
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                               QWidget, QPushButton, QLineEdit, QSpinBox, 
                               QDoubleSpinBox, QFormLayout, QMessageBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from database import init_local_db

class FarmAppAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FarmApp - Sistema Administrativo (Fase 2 Completa)")
        self.resize(850, 750)

        init_local_db()

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.title = QLabel("FarmApp Admin\nDashboard Local-First")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Ej. Paracetamol 500mg")
        
        self.input_stock = QSpinBox()
        self.input_stock.setRange(0, 10000)
        
        self.input_price = QDoubleSpinBox()
        self.input_price.setRange(0.0, 99999.99)
        self.input_price.setPrefix("$ ")

        form_layout.addRow("Nombre del Producto:", self.input_name)
        form_layout.addRow("Stock (Unidades):", self.input_stock)
        form_layout.addRow("Precio de Venta:", self.input_price)

        # --- ZONA DE BOTONES ---
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
        self.table_label = QLabel("Inventario Local:")
        self.table_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar producto al instante...")
        self.input_search.setStyleSheet("padding: 5px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.input_search.textChanged.connect(self.filter_table)

        header_layout.addWidget(self.table_label)
        header_layout.addStretch()
        header_layout.addWidget(self.input_search)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(4)
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Producto", "Stock", "Precio"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        main_layout.addWidget(self.title)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.inventory_table)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_inventory()

    def import_csv(self):
        """Abre un explorador de archivos y carga cientos de productos desde un CSV."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo CSV de inventario", "", "Archivos CSV (*.csv)")
        if not file_path:
            return # El usuario canceló la ventana
            
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # Saltar la primera fila (los títulos)
                
                count = 0
                for row in reader:
                    # El CSV debe tener 3 columnas: Nombre, Stock, Precio
                    if len(row) >= 3:
                        name = row[0].strip()
                        stock = int(row[1])
                        price = float(row[2])
                        cursor.execute('INSERT INTO inventory (product_name, stock, price) VALUES (?, ?, ?)', (name, stock, price))
                        count += 1
                        
            conn.commit()
            conn.close()
            
            self.load_inventory() # Recargar la tabla con todo lo nuevo
            self.input_search.clear()
            QMessageBox.information(self, "Éxito", f"Se importaron {count} productos correctamente al caché local.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", f"Verifica que el CSV tenga formato (Nombre,Stock,Precio).\nError: {str(e)}")

    def filter_table(self, text):
        for row in range(self.inventory_table.rowCount()):
            item = self.inventory_table.item(row, 1)
            if item:
                match = text.lower() in item.text().lower()
                self.inventory_table.setRowHidden(row, not match)

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
                
                item_id = QTableWidgetItem(str(row_data[0]))
                item_name = QTableWidgetItem(str(row_data[1]))
                item_stock = QTableWidgetItem(str(stock_value))
                item_price = QTableWidgetItem(f"$ {row_data[3]:.2f}")

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

                self.inventory_table.setItem(row_idx, 0, item_id)
                self.inventory_table.setItem(row_idx, 1, item_name)
                self.inventory_table.setItem(row_idx, 2, item_stock)
                self.inventory_table.setItem(row_idx, 3, item_price)
                
        except Exception as e:
            print("Error cargando inventario:", e)

    def save_product(self):
        name = self.input_name.text()
        stock = self.input_stock.value()
        price = self.input_price.value()

        if not name.strip():
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO inventory (product_name, stock, price) VALUES (?, ?, ?)', (name, stock, price))
            conn.commit()
            conn.close()
            
            self.input_name.clear()
            self.input_stock.setValue(0)
            self.input_price.setValue(0.0)
            
            self.load_inventory()
            self.input_search.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error de BD", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FarmAppAdmin()
    window.show()
    sys.exit(app.exec())