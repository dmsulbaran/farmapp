import sys
import sqlite3
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                               QWidget, QPushButton, QLineEdit, QSpinBox, 
                               QDoubleSpinBox, QFormLayout, QMessageBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from database import init_local_db

class FarmAppAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FarmApp - Sistema Administrativo (Fase 2)")
        self.resize(800, 700) # Ventana un poco más grande para la tabla

        init_local_db()

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.title = QLabel("FarmApp Admin\nDashboard Local-First")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        
        # --- CAMPOS DEL FORMULARIO ---
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

        self.btn_save = QPushButton("Guardar Producto")
        self.btn_save.setStyleSheet("padding: 8px; background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_product)

        # --- TABLA DE INVENTARIO (FASE 2) ---
        self.table_label = QLabel("Inventario Local (Caché SQLite):")
        self.table_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(4)
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Producto", "Stock", "Precio"])
        # Hacer que las columnas se estiren para ocupar todo el ancho
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # --- ENSAMBLAJE ---
        main_layout.addWidget(self.title)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.btn_save)
        main_layout.addWidget(self.table_label)
        main_layout.addWidget(self.inventory_table)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Cargar los datos apenas se abre la app
        self.load_inventory()

    def load_inventory(self):
        """Lee la base de datos SQLite y llena la tabla."""
        try:
            conn = sqlite3.connect('farmapp_cache.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, product_name, stock, price FROM inventory')
            rows = cursor.fetchall()
            conn.close()

            # Configurar cantidad de filas en la tabla
            self.inventory_table.setRowCount(len(rows))

            # Rellenar celdas
            for row_idx, row_data in enumerate(rows):
                # ID
                self.inventory_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
                # Nombre
                self.inventory_table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
                # Stock
                self.inventory_table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))
                # Precio (formateado)
                self.inventory_table.setItem(row_idx, 3, QTableWidgetItem(f"$ {row_data[3]:.2f}"))
                
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
            git add .
            # Limpiar formulario
            self.input_name.clear()
            self.input_stock.setValue(0)
            self.input_price.setValue(0.0)
            
            # ¡Recargar la tabla automáticamente para ver el nuevo producto!
            self.load_inventory()
            
        except Exception as e:
            QMessageBox.critical(self, "Error de BD", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FarmAppAdmin()
    window.show()
    sys.exit(app.exec())