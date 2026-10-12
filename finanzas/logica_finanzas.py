"""
Gestor de finanzas local para María.
Persistencia SQLite, cero APIs externas, cero telemetría.
"""
import os
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

RUTA_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finanzas.db")


class GestorFinanzas:
    """Núcleo de datos: transacciones, categorías, presupuestos y metas."""

    def __init__(self, ruta_db=None):
        self.ruta_db = ruta_db or RUTA_DB
        self._init_db()

    # ── Conexión ───────────────────────────────────────────────
    @contextmanager
    def _conexion(self):
        conn = sqlite3.connect(self.ruta_db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conexion() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    tipo TEXT NOT NULL CHECK(tipo IN ('gasto','ingreso')),
                    color TEXT DEFAULT '#238636'
                );
                CREATE TABLE IF NOT EXISTS transacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL CHECK(tipo IN ('gasto','ingreso')),
                    monto REAL NOT NULL,
                    categoria TEXT NOT NULL,
                    descripcion TEXT,
                    fecha TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS presupuestos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria TEXT NOT NULL,
                    limite_mensual REAL NOT NULL,
                    mes INTEGER NOT NULL,
                    anio INTEGER NOT NULL,
                    UNIQUE(categoria, mes, anio)
                );
                CREATE TABLE IF NOT EXISTS metas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    objetivo REAL,
                    actual REAL DEFAULT 0,
                    fecha_limite TEXT
                );
            """)

            # ── Migración: hacer 'objetivo' nullable si era NOT NULL ──
            # SQLite no soporta ALTER COLUMN, así que recreamos la tabla
            # solo si detectamos que la columna objetivo es NOT NULL.
            try:
                info = c.execute("PRAGMA table_info(metas)").fetchall()
                col_obj = next((col for col in info if col["name"] == "objetivo"), None)
                if col_obj and col_obj["notnull"] == 1:
                    # Migrar: recrear tabla sin NOT NULL en objetivo
                    c.executescript("""
                        CREATE TABLE metas_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            objetivo REAL,
                            actual REAL DEFAULT 0,
                            fecha_limite TEXT
                        );
                        INSERT INTO metas_new SELECT id, nombre, objetivo, actual, fecha_limite FROM metas;
                        DROP TABLE metas;
                        ALTER TABLE metas_new RENAME TO metas;
                    """)
            except Exception:
                pass  # Si algo falla, seguimos adelante

            # Categorías por defecto (solo si la tabla está vacía)
            if c.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
                defaults = [
                    ("Comida", "gasto", "#e5a04a"),
                    ("Transporte", "gasto", "#5b9bd5"),
                    ("Ocio", "gasto", "#c06cc7"),
                    ("Hogar", "gasto", "#8b949e"),
                    ("Salud", "gasto", "#e5534b"),
                    ("Otros gastos", "gasto", "#6e7681"),
                    ("Nómina", "ingreso", "#238636"),
                    ("Otros ingresos", "ingreso", "#2ea043"),
                ]
                c.executemany(
                    "INSERT INTO categorias (nombre, tipo, color) VALUES (?,?,?)",
                    defaults,
                )

    # ── Categorías ─────────────────────────────────────────────
    def listar_categorias(self, tipo=None):
        with self._conexion() as c:
            if tipo:
                return c.execute(
                    "SELECT * FROM categorias WHERE tipo=? ORDER BY nombre", (tipo,)
                ).fetchall()
            return c.execute("SELECT * FROM categorias ORDER BY tipo, nombre").fetchall()

    def agregar_categoria(self, nombre, tipo, color="#238636"):
        with self._conexion() as c:
            try:
                c.execute(
                    "INSERT INTO categorias (nombre, tipo, color) VALUES (?,?,?)",
                    (nombre.strip(), tipo, color),
                )
                return True, f"Categoría '{nombre}' creada."
            except sqlite3.IntegrityError:
                return False, f"La categoría '{nombre}' ya existe."

    # ── Transacciones ──────────────────────────────────────────
    def agregar_transaccion(self, tipo, monto, categoria, descripcion="", fecha=None):
        if monto <= 0:
            return False, "El monto debe ser mayor que cero."
        fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._conexion() as c:
            c.execute(
                """INSERT INTO transacciones
                   (tipo, monto, categoria, descripcion, fecha)
                   VALUES (?,?,?,?,?)""",
                (tipo, float(monto), categoria, descripcion, fecha),
            )
        return True, f"{'Gasto' if tipo=='gasto' else 'Ingreso'} de {monto:.2f}€ registrado."

    def listar_transacciones(self, limite=50, tipo=None, mes=None, anio=None):
        query = "SELECT * FROM transacciones WHERE 1=1"
        params = []
        if tipo:
            query += " AND tipo=?"
            params.append(tipo)
        if mes and anio:
            query += " AND strftime('%m', fecha)=? AND strftime('%Y', fecha)=?"
            params += [f"{mes:02d}", str(anio)]
        query += " ORDER BY fecha DESC LIMIT ?"
        params.append(limite)
        with self._conexion() as c:
            return c.execute(query, params).fetchall()

    def eliminar_transaccion(self, id_transaccion):
        with self._conexion() as c:
            c.execute("DELETE FROM transacciones WHERE id=?", (id_transaccion,))

    # ── Consultas / Estadísticas ───────────────────────────────
    def balance(self, mes=None, anio=None):
        ingresos, gastos = 0.0, 0.0
        with self._conexion() as c:
            if mes and anio:
                filas = c.execute(
                    """SELECT tipo, SUM(monto) FROM transacciones
                       WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=?
                       GROUP BY tipo""",
                    (f"{mes:02d}", str(anio)),
                ).fetchall()
            else:
                filas = c.execute(
                    "SELECT tipo, SUM(monto) FROM transacciones GROUP BY tipo"
                ).fetchall()
            for f in filas:
                if f["tipo"] == "ingreso":
                    ingresos = f[1] or 0
                else:
                    gastos = f[1] or 0
        return {
            "ingresos": ingresos,
            "gastos": gastos,
            "balance": ingresos - gastos,
        }

    def gastos_por_categoria(self, mes=None, anio=None):
        with self._conexion() as c:
            if mes and anio:
                filas = c.execute(
                    """SELECT categoria, SUM(monto) as total
                       FROM transacciones
                       WHERE tipo='gasto'
                         AND strftime('%m', fecha)=? AND strftime('%Y', fecha)=?
                       GROUP BY categoria ORDER BY total DESC""",
                    (f"{mes:02d}", str(anio)),
                ).fetchall()
            else:
                filas = c.execute(
                    """SELECT categoria, SUM(monto) as total
                       FROM transacciones WHERE tipo='gasto'
                       GROUP BY categoria ORDER BY total DESC"""
                ).fetchall()
            return [dict(f) for f in filas]

    # ── Presupuestos ───────────────────────────────────────────
    def fijar_presupuesto(self, categoria, limite, mes, anio):
        with self._conexion() as c:
            c.execute(
                """INSERT INTO presupuestos (categoria, limite_mensual, mes, anio)
                   VALUES (?,?,?,?)
                   ON CONFLICT(categoria, mes, anio) DO UPDATE
                   SET limite_mensual=excluded.limite_mensual""",
                (categoria, float(limite), mes, anio),
            )
        return True, f"Presupuesto de {limite}€ fijado para '{categoria}'."

    def estado_presupuestos(self, mes, anio):
        with self._conexion() as c:
            presupuestos = c.execute(
                "SELECT * FROM presupuestos WHERE mes=? AND anio=?", (mes, anio)
            ).fetchall()
            resultado = []
            for p in presupuestos:
                gastado = c.execute(
                    """SELECT COALESCE(SUM(monto),0) FROM transacciones
                       WHERE tipo='gasto' AND categoria=?
                         AND strftime('%m', fecha)=? AND strftime('%Y', fecha)=?""",
                    (p["categoria"], f"{mes:02d}", str(anio)),
                ).fetchone()[0]
                resultado.append({
                    "categoria": p["categoria"],
                    "limite": p["limite_mensual"],
                    "gastado": gastado,
                    "restante": p["limite_mensual"] - gastado,
                    "porcentaje": (gastado / p["limite_mensual"] * 100)
                    if p["limite_mensual"] > 0 else 0,
                })
            return resultado

    # ── Metas de ahorro ────────────────────────────────────────
    def crear_meta(self, nombre, objetivo=None, fecha_limite=None):
        """Crea una meta. objetivo=None significa 'sin objetivo fijo' (ahorro libre)."""
        with self._conexion() as c:
            c.execute(
                "INSERT INTO metas (nombre, objetivo, actual, fecha_limite) VALUES (?,?,?,?)",
                (nombre, float(objetivo) if objetivo is not None else None, 0.0, fecha_limite),
            )
        if objetivo is None:
            return True, f"Meta '{nombre}' creada (ahorro libre)."
        return True, f"Meta '{nombre}' creada."

    def aportar_a_meta(self, id_meta, cantidad):
        with self._conexion() as c:
            c.execute(
                "UPDATE metas SET actual = actual + ? WHERE id=?",
                (float(cantidad), id_meta),
            )
        return True

    def listar_metas(self):
        with self._conexion() as c:
            return c.execute("SELECT * FROM metas ORDER BY id").fetchall()

    def eliminar_meta(self, id_meta):
        with self._conexion() as c:
            c.execute("DELETE FROM metas WHERE id=?", (id_meta,))
        return True


# Instancia global compartida con María
gestor = GestorFinanzas()