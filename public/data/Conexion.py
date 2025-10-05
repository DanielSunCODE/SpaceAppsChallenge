import psycopg2

try:
    # Conexión a PostgreSQL
    conn = psycopg2.connect(
        host="192.168.1.72",   # IP del servidor
        port=5432,             # Puerto por defecto de PostgreSQL
        dbname="Proyecto",     # Nombre de la base de datos
        user="user1",          # Usuario
        password="user1"       # Contraseña
    )

    print("✅ Conexión exitosa a la base de datos 'Proyecto'")

    # Crear cursor para ejecutar consultas
    cur = conn.cursor()

    # Ejecutar SELECT sobre la tabla LOCALIDAD
    cur.execute("SELECT * FROM LOCALIDAD;")

    # Obtener los resultados
    filas = cur.fetchall()

    print("\n📋 Resultados de la tabla LOCALIDAD:")
    print("-" * 40)

    # Mostrar cada fila
    if filas:
        for fila in filas:
            print(fila)
    else:
        print("⚠️ No hay registros en la tabla LOCALIDAD.")

except psycopg2.Error as e:
    print("❌ Error al conectar o ejecutar la consulta:", e)

finally:
    # Cerrar cursor y conexión
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals() and conn:
        conn.close()
        print("\n🔒 Conexión cerrada correctamente.")
