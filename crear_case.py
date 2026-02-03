import sqlite3

def inicializar_sistema():
    # Conexión al archivo de base de datos
    conn = sqlite3.connect('inventario_aceites.db')
    cur = conn.cursor()

    # Eliminamos tablas antiguas para asegurar que la nueva estructura se aplique
    tablas = ['movimientos', 'pagos', 'detalle_ventas', 'ventas', 'agenda', 'sucursales', 'clientes', 'productos']
    for t in tablas: 
        cur.execute(f"DROP TABLE IF EXISTS {t}")

    # PRODUCTOS: Mantiene unidad y stock_minimo + costo y precio
    cur.execute('''CREATE TABLE productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT, 
        marca TEXT, 
        unidad TEXT, 
        stock REAL DEFAULT 0, 
        costo REAL DEFAULT 0, 
        precio_venta REAL DEFAULT 0, 
        stock_minimo REAL DEFAULT 5)''')

    # MOVIMIENTOS: Para el historial de entradas y salidas de almacén
    cur.execute('''CREATE TABLE movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        producto_id INTEGER, 
        fecha TEXT, 
        tipo TEXT, 
        cantidad REAL, 
        costo_historico REAL, 
        precio_venta_historico REAL,
        FOREIGN KEY(producto_id) REFERENCES productos(id))''')

    # CLIENTES: Con contacto_nombre y rubro
    cur.execute('''CREATE TABLE clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre_comercial TEXT, 
        ruc_dni TEXT, 
        rubro TEXT, 
        contacto_nombre TEXT)''')

    # SUCURSALES: Con toda la información geográfica y contacto de sede
    cur.execute('''CREATE TABLE sucursales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        cliente_id INTEGER, 
        nombre_sede TEXT, 
        direccion TEXT, 
        distrito TEXT, 
        provincia TEXT, 
        zona TEXT, 
        contacto_sede TEXT, 
        telefono1 TEXT, 
        vendedor_asignado TEXT, 
        latitud TEXT, 
        longitud TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')

    # VENTAS: Con el campo vendedor para reportes de comisión
    cur.execute('''CREATE TABLE ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        cliente_id INTEGER, 
        sede_id INTEGER, 
        fecha TEXT, 
        total REAL, 
        vendedor TEXT, 
        estado_entrega TEXT DEFAULT 'Entregado')''')

    # DETALLE_VENTAS: Con precio_unitario para soportar el precio editable
    cur.execute('''CREATE TABLE detalle_ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        venta_id INTEGER, 
        producto_id INTEGER, 
        cantidad REAL, 
        precio_unitario REAL)''')

    # PAGOS: Para controlar saldos y deudas
    cur.execute('''CREATE TABLE pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        venta_id INTEGER, 
        fecha_pago TEXT, 
        monto_pagado REAL)''')

    # TABLA AGENDA: Actualizada con Zona, Contacto y Color
    cur.execute('''CREATE TABLE IF NOT EXISTS agenda (
        sede_id INTEGER PRIMARY KEY, 
        cliente_id INTEGER, 
        zona TEXT,
        fecha_visita TEXT,
        tipo_contacto TEXT,
        color TEXT,
        FOREIGN KEY(sede_id) REFERENCES sucursales(id))''')

    conn.commit()
    conn.close()
    print("✅ Base de datos reconstruida con éxito. Estructura COMPLETA y compatible.")

if __name__ == "__main__":
    inicializar_sistema()