import sqlite3

# Intenta importar colorama para mejorar la legibilidad en terminal;
# si no está instalado, usa cadenas vacías para no interrumpir la ejecución.
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class _SinColor:
        GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = RESET_ALL = ""
    Fore = Style = _SinColor()

NOMBRE_BD = "inventario.db"


def conectar_bd():
    """Crea y retorna una conexión a la base de datos SQLite."""
    return sqlite3.connect(NOMBRE_BD)


def inicializar_bd():
    """Crea la tabla 'productos' si aún no existe."""
    sql = """
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL,
        categoria TEXT
    )
    """
    try:
        # El bloque 'with' confirma los cambios automáticamente si no hay errores.
        with conectar_bd() as conexion:
            conexion.execute(sql)
    except sqlite3.Error as error:
        print(f"{Fore.RED}Error al inicializar la base de datos: {error}")


def pedir_texto_obligatorio(mensaje):
    """Solicita un texto no vacío y devuelve el valor limpio."""
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print(f"{Fore.YELLOW}Este campo es obligatorio y no puede quedar vacío.")


def pedir_entero(mensaje, minimo=None):
    """Solicita un número entero válido, opcionalmente mayor o igual a 'minimo'."""
    while True:
        entrada = input(mensaje).strip()
        try:
            numero = int(entrada)
            if minimo is not None and numero < minimo:
                print(f"{Fore.YELLOW}Ingresá un número entero mayor o igual a {minimo}.")
                continue
            return numero
        except ValueError:
            print(f"{Fore.RED}Entrada inválida. Debés ingresar un número entero.")


def pedir_flotante(mensaje, mayor_que_cero=False):
    """Solicita un número decimal válido (acepta coma o punto)."""
    while True:
        # Reemplaza la coma por punto para aceptar decimales en formato local.
        entrada = input(mensaje).strip().replace(",", ".")
        try:
            numero = float(entrada)
            if mayor_que_cero and numero <= 0:
                print(f"{Fore.YELLOW}El valor debe ser mayor que cero.")
                continue
            return numero
        except ValueError:
            print(f"{Fore.RED}Entrada inválida. Debés ingresar un número válido.")


def mostrar_productos(filas):
    """Imprime una lista de tuplas de productos de forma ordenada."""
    if not filas:
        print(f"{Fore.YELLOW}No hay productos para mostrar.")
        return

    print(f"\n{Fore.CYAN}{'-' * 85}")
    for prod in filas:
        prod_id, nombre, descripcion, cantidad, precio, categoria = prod
        desc_texto = descripcion if descripcion else "Sin descripción"
        cat_texto = categoria if categoria else "Sin categoría"
        print(
            f"{Fore.GREEN}ID: {prod_id} {Style.RESET_ALL}| "
            f"Nombre: {nombre} | "
            f"Categoría: {cat_texto} | "
            f"Cantidad: {cantidad} | "
            f"Precio: ${precio:.2f} | "
            f"Desc: {desc_texto}"
        )
    print(f"{Fore.CYAN}{'-' * 85}")


def registrar_producto():
    """Registra un nuevo producto en la tabla 'productos'."""
    print(f"\n{Fore.CYAN}--- Registrar nuevo producto ---")
    nombre = pedir_texto_obligatorio("Nombre del producto: ")
    descripcion = input("Descripción (opcional): ").strip()
    cantidad = pedir_entero("Cantidad disponible: ", minimo=0)
    precio = pedir_flotante("Precio: ", mayor_que_cero=True)
    categoria = input("Categoría (opcional): ").strip()

    # Los marcadores '?' evitan la inyección SQL al pasar los datos como parámetros.
    sql = """
    INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
    VALUES (?, ?, ?, ?, ?)
    """
    try:
        with conectar_bd() as conexion:
            conexion.execute(sql, (nombre, descripcion, cantidad, precio, categoria))
        print(f"{Fore.GREEN}Producto '{nombre}' registrado con éxito.")
    except sqlite3.Error as error:
        print(f"{Fore.RED}No se pudo registrar el producto: {error}")


def listar_productos():
    """Consulta y muestra todos los productos registrados."""
    print(f"\n{Fore.CYAN}--- Listado de productos ---")
    sql = "SELECT id, nombre, descripcion, cantidad, precio, categoria FROM productos ORDER BY id ASC"
    try:
        with conectar_bd() as conexion:
            filas = conexion.execute(sql).fetchall()
        mostrar_productos(filas)
    except sqlite3.Error as error:
        print(f"{Fore.RED}Error al consultar los productos: {error}")


def buscar_productos():
    """Busca productos por ID (obligatorio) o por nombre/categoría (opcional)."""
    print(f"\n{Fore.CYAN}--- Buscar productos ---")
    print("1. Buscar por ID")
    print("2. Buscar por nombre")
    print("3. Buscar por categoría")
    opcion = input("Elegí un criterio de búsqueda: ").strip()

    try:
        with conectar_bd() as conexion:
            if opcion == "1":
                prod_id = pedir_entero("Ingresá el ID del producto: ", minimo=1)
                filas = conexion.execute(
                    "SELECT id, nombre, descripcion, cantidad, precio, categoria FROM productos WHERE id = ?",
                    (prod_id,)
                ).fetchall()
            elif opcion == "2":
                texto = pedir_texto_obligatorio("Ingresá el nombre o parte del nombre: ")
                # Usar %texto% con LIKE permite buscar coincidencias parciales.
                filas = conexion.execute(
                    "SELECT id, nombre, descripcion, cantidad, precio, categoria FROM productos WHERE nombre LIKE ?",
                    (f"%{texto}%",)
                ).fetchall()
            elif opcion == "3":
                texto = pedir_texto_obligatorio("Ingresá la categoría: ")
                # Usar %texto% con LIKE permite buscar coincidencias parciales.
                filas = conexion.execute(
                    "SELECT id, nombre, descripcion, cantidad, precio, categoria FROM productos WHERE categoria LIKE ?",
                    (f"%{texto}%",)
                ).fetchall()
            else:
                print(f"{Fore.YELLOW}Opción de búsqueda no válida.")
                return

        mostrar_productos(filas)
    except sqlite3.Error as error:
        print(f"{Fore.RED}Error durante la búsqueda: {error}")


def actualizar_producto():
    """Actualiza los datos de un producto existente identificado por su ID."""
    print(f"\n{Fore.CYAN}--- Actualizar producto ---")
    prod_id = pedir_entero("Ingresá el ID del producto a actualizar: ", minimo=1)

    try:
        with conectar_bd() as conexion:
            actual = conexion.execute(
                "SELECT id, nombre, descripcion, cantidad, precio, categoria FROM productos WHERE id = ?",
                (prod_id,)
            ).fetchone()

            if not actual:
                print(f"{Fore.YELLOW}No existe ningún producto con el ID {prod_id}.")
                return

            _, nombre_act, desc_act, cant_act, precio_act, cat_act = actual
            print(f"Editando '{nombre_act}' (dejá vacío para mantener el valor actual):")

            # Si el usuario deja el campo vacío, se conserva el valor actual del registro.
            nuevo_nombre = input(f"Nuevo nombre [{nombre_act}]: ").strip()
            nombre_final = nuevo_nombre if nuevo_nombre else nombre_act

            nueva_desc = input(f"Nueva descripción [{desc_act or 'Sin descripción'}]: ").strip()
            desc_final = nueva_desc if nueva_desc else desc_act

            nueva_cant = input(f"Nueva cantidad [{cant_act}]: ").strip()
            if nueva_cant:
                try:
                    cant_val = int(nueva_cant)
                    if cant_val < 0:
                        print(f"{Fore.RED}La cantidad no puede ser negativa. Actualización cancelada.")
                        return
                    cant_final = cant_val
                except ValueError:
                    print(f"{Fore.RED}Cantidad inválida. Actualización cancelada.")
                    return
            else:
                cant_final = cant_act

            nuevo_precio = input(f"Nuevo precio [{precio_act:.2f}]: ").strip()
            if nuevo_precio:
                try:
                    precio_val = float(nuevo_precio.replace(",", "."))
                    if precio_val <= 0:
                        print(f"{Fore.RED}El precio debe ser mayor a cero. Actualización cancelada.")
                        return
                    precio_final = precio_val
                except ValueError:
                    print(f"{Fore.RED}Precio inválido. Actualización cancelada.")
                    return
            else:
                precio_final = precio_act

            nueva_cat = input(f"Nueva categoría [{cat_act or 'Sin categoría'}]: ").strip()
            cat_final = nueva_cat if nueva_cat else cat_act

            # Los marcadores '?' evitan la inyección SQL al pasar los valores como parámetros.
            sql = """
            UPDATE productos
            SET nombre = ?, descripcion = ?, cantidad = ?, precio = ?, categoria = ?
            WHERE id = ?
            """
            conexion.execute(sql, (nombre_final, desc_final, cant_final, precio_final, cat_final, prod_id))
        print(f"{Fore.GREEN}Producto ID {prod_id} actualizado correctamente.")
    except sqlite3.Error as error:
        print(f"{Fore.RED}Error al actualizar el producto: {error}")


def eliminar_producto():
    """Elimina un producto por su ID tras solicitar confirmación."""
    print(f"\n{Fore.CYAN}--- Eliminar producto ---")
    prod_id = pedir_entero("Ingresá el ID del producto a eliminar: ", minimo=1)

    try:
        with conectar_bd() as conexion:
            producto = conexion.execute(
                "SELECT id, nombre FROM productos WHERE id = ?",
                (prod_id,)
            ).fetchone()

            if not producto:
                print(f"{Fore.YELLOW}No se encontró ningún producto con el ID {prod_id}.")
                return

            _, nombre = producto
            confirmacion = input(
                f"{Fore.YELLOW}¿Seguro que querés eliminar '{nombre}' (ID {prod_id})? (s/n): "
            ).strip().lower()

            if confirmacion == "s":
                # El marcador '?' evita la inyección SQL en el borrado por ID.
                conexion.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
                print(f"{Fore.GREEN}Producto '{nombre}' eliminado.")
            else:
                print("Operación cancelada.")
    except sqlite3.Error as error:
        print(f"{Fore.RED}Error al eliminar el producto: {error}")


def reporte_bajo_stock():
    """Muestra productos con cantidad igual o inferior a un límite dado."""
    print(f"\n{Fore.CYAN}--- Reporte de bajo stock ---")
    limite = pedir_entero("Mostrar productos con cantidad igual o menor a: ", minimo=0)

    sql = """
    SELECT id, nombre, descripcion, cantidad, precio, categoria
    FROM productos
    WHERE cantidad <= ?
    ORDER BY cantidad ASC, id ASC
    """
    try:
        with conectar_bd() as conexion:
            filas = conexion.execute(sql, (limite,)).fetchall()
        print(f"\nProductos con stock <= {limite}:")
        mostrar_productos(filas)
    except sqlite3.Error as error:
        print(f"{Fore.RED}Error al generar el reporte: {error}")


def mostrar_menu():
    """Imprime las opciones del menú principal en la terminal."""
    print(f"\n{Fore.MAGENTA}=== GESTIÓN DE INVENTARIO ===")
    print("1. Registrar producto")
    print("2. Visualizar productos")
    print("3. Actualizar producto (por ID)")
    print("4. Eliminar producto (por ID)")
    print("5. Buscar producto")
    print("6. Reporte de bajo stock")
    print("7. Salir")


def main():
    """Bucle principal de la aplicación."""
    inicializar_bd()
    while True:
        mostrar_menu()
        opcion = input(f"\n{Fore.CYAN}Seleccioná una opción: ").strip()

        if opcion == "1":
            registrar_producto()
        elif opcion == "2":
            listar_productos()
        elif opcion == "3":
            actualizar_producto()
        elif opcion == "4":
            eliminar_producto()
        elif opcion == "5":
            buscar_productos()
        elif opcion == "6":
            reporte_bajo_stock()
        elif opcion == "7":
            print(f"{Fore.GREEN}¡Hasta luego!")
            break
        else:
            print(f"{Fore.YELLOW}Opción no válida. Elegí un número del 1 al 7.")


if __name__ == "__main__":
    main()
