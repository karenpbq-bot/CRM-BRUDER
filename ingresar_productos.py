import sqlite3

def registrar_producto():
    conexion = sqlite3.connect('inventario_aceites.db')
    cursor = conexion.cursor()

    print("--- REGISTRO TÉCNICO DE PRODUCTO ---")
    nombre = input("Nombre del aceite: ")
    marca = input("Marca: ")
    
    print("Presentación: 1. Botella | 2. Balde")
    opcion = input("Opción: ")

    if opcion == "1":
        unidad_base = "Botella"
        u_por_caja = int(input("¿Cuántas botellas trae la caja?: "))
        cajas_hoy = int(input("¿Cuántas CAJAS tienes?: "))
        sueltas_hoy = int(input("¿Cuántas BOTELLAS sueltas?: "))
        stock_total = (cajas_hoy * u_por_caja) + sueltas_hoy
        
        # EXPLICACIÓN: Pedimos costo por la unidad mínima (botella)
        costo = float(input("¿Cuánto te cuesta CADA BOTELLA? (S/): "))
        precio = float(input("¿A cuánto vendes CADA BOTELLA? (S/): "))
    else:
        unidad_base = "Balde"
        u_por_caja = 1
        stock_total = int(input("¿Cuántos BALDES tienes?: "))
        costo = float(input("¿Cuánto te cuesta CADA BALDE? (S/): "))
        precio = float(input("¿A cuánto vendes CADA BALDE? (S/): "))

    # GUARDADO: Nota que no enviamos la fecha, ¡SQLite la pone solo!
    cursor.execute('''
        INSERT INTO productos (nombre, marca, unidad_base, unidades_por_caja, 
                             stock_total_unidades, costo_unidad, precio_venta)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (nombre, marca, unidad_base, u_por_caja, stock_total, costo, precio))

    conexion.commit()
    conexion.close()
    print(f"\n¡Éxito! Registrado el {nombre} con costo S/ {costo}")

registrar_producto()