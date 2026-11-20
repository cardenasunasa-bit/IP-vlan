import io
import os
import sqlite3
import secrets
import ipaddress
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_file, session, abort)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-local-solo-para-pruebas")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Usuario y contraseña (se pueden cambiar con variables de entorno)
APP_USER = os.environ.get("APP_USER", "admin123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "admin")

# Si existe DATABASE_URL (PostgreSQL) se usa esa base; si no, SQLite local
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith("postgres")

if USE_PG:
    import psycopg2
    import psycopg2.extras
    INTEGRITY_ERRORS = (psycopg2.IntegrityError,)
else:
    INTEGRITY_ERRORS = (sqlite3.IntegrityError,)


def get_db():
    if USE_PG:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect(os.environ.get("SQLITE_PATH", "clientes.db"))
    conn.row_factory = sqlite3.Row
    return conn


def run(sql, params=(), fetch=None, commit=False):
    """Ejecuta una consulta. Usa ? como marcador; se adapta solo a PostgreSQL."""
    if USE_PG:
        sql = sql.replace("?", "%s")
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        result = None
        if fetch == "all":
            result = [dict(r) for r in cur.fetchall()]
        elif fetch == "one":
            r = cur.fetchone()
            result = dict(r) if r else None
        if commit:
            conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    pk = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    run(f"""
        CREATE TABLE IF NOT EXISTS asignaciones (
            id {pk},
            cliente TEXT NOT NULL,
            ip TEXT NOT NULL,
            vlan INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            nota TEXT,
            UNIQUE (ip, vlan)
        )
    """, commit=True)


# ---------- Seguridad: login y CSRF ----------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("auth"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.before_request
def csrf_protect():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    if request.method == "POST":
        token = request.form.get("csrf_token", "")
        if not secrets.compare_digest(token, session["csrf"]):
            abort(400, "Token de seguridad invalido. Recarga la pagina.")


@app.context_processor
def inject_csrf():
    return {"csrf_token": session.get("csrf", "")}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("usuario", "")
        p = request.form.get("password", "")
        ok_u = secrets.compare_digest(u.encode(), APP_USER.encode())
        ok_p = secrets.compare_digest(p.encode(), APP_PASSWORD.encode())
        if ok_u and ok_p:
            session["auth"] = True
            return redirect(url_for("index"))
        flash("Usuario o contrasena incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/salud")
def salud():
    return "ok"


# ---------- Utilidades ----------

def validar(cliente, ip, vlan):
    if not cliente or not ip or not vlan:
        return None, None, "Cliente, IP y VLAN son obligatorios."
    try:
        ip = str(ipaddress.ip_address(ip))
    except ValueError:
        return None, None, "La IP no es valida."
    if not vlan.isdigit() or not (1 <= int(vlan) <= 4094):
        return None, None, "La VLAN debe ser un numero entre 1 y 4094."
    return ip, int(vlan), None


def ordenar(filas):
    return sorted(filas, key=lambda f: (f["vlan"], ipaddress.ip_address(f["ip"])))


# ---------- Pantallas ----------

@app.route("/")
@login_required
def index():
    texto = request.args.get("q", "").strip()
    if texto:
        like = f"%{texto.lower()}%"
        filas = run(
            "SELECT * FROM asignaciones WHERE LOWER(cliente) LIKE ? OR ip LIKE ? "
            "OR CAST(vlan AS TEXT) LIKE ?", (like, like, like), fetch="all")
    else:
        filas = run("SELECT * FROM asignaciones", fetch="all")
    filas = ordenar(filas)
    total_vlans = len({f["vlan"] for f in filas})
    return render_template("index.html", filas=filas, q=texto, total_vlans=total_vlans)


@app.route("/agregar", methods=["POST"])
@login_required
def agregar():
    cliente = request.form.get("cliente", "").strip()
    ip, vlan, error = validar(cliente, request.form.get("ip", "").strip(),
                              request.form.get("vlan", "").strip())
    nota = request.form.get("nota", "").strip()
    if error:
        flash(error, "error")
        return redirect(url_for("index"))
    try:
        run("INSERT INTO asignaciones (cliente, ip, vlan, fecha, nota) VALUES (?, ?, ?, ?, ?)",
            (cliente, ip, vlan, datetime.now().strftime("%Y-%m-%d %H:%M"), nota), commit=True)
        flash(f"Guardado: {cliente} con IP {ip} en VLAN {vlan}.", "ok")
    except INTEGRITY_ERRORS:
        otro = run("SELECT cliente FROM asignaciones WHERE ip = ? AND vlan = ?",
                   (ip, vlan), fetch="one")
        flash(f"CONFLICTO: la IP {ip} ya esta en uso en la VLAN {vlan} "
              f"por el cliente {otro['cliente']}.", "error")
    return redirect(url_for("index"))


@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    fila = run("SELECT * FROM asignaciones WHERE id = ?", (id,), fetch="one")
    if not fila:
        flash("Ese registro no existe.", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        ip, vlan, error = validar(cliente, request.form.get("ip", "").strip(),
                                  request.form.get("vlan", "").strip())
        nota = request.form.get("nota", "").strip()
        if error:
            flash(error, "error")
            return render_template("editar.html", f=fila)
        try:
            run("UPDATE asignaciones SET cliente=?, ip=?, vlan=?, nota=? WHERE id=?",
                (cliente, ip, vlan, nota, id), commit=True)
            flash("Registro actualizado.", "ok")
            return redirect(url_for("index"))
        except INTEGRITY_ERRORS:
            otro = run("SELECT cliente FROM asignaciones WHERE ip = ? AND vlan = ?",
                       (ip, vlan), fetch="one")
            flash(f"CONFLICTO: la IP {ip} ya esta en uso en la VLAN {vlan} "
                  f"por el cliente {otro['cliente']}.", "error")
            return render_template("editar.html", f=fila)
    return render_template("editar.html", f=fila)


@app.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    run("DELETE FROM asignaciones WHERE id = ?", (id,), commit=True)
    flash("Registro eliminado. La IP quedo libre.", "ok")
    return redirect(url_for("index"))


@app.route("/exportar")
@login_required
def exportar():
    filas = ordenar(run("SELECT * FROM asignaciones", fetch="all"))
    wb = Workbook()
    ws = wb.active
    ws.title = "IP por VLAN"
    ws.append(["VLAN", "IP", "Cliente", "Fecha", "Nota"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(horizontal="center")
    for f in filas:
        ws.append([f["vlan"], f["ip"], f["cliente"], f["fecha"], f["nota"] or ""])
    for col, ancho in zip("ABCDE", [10, 18, 32, 20, 40]):
        ws.column_dimensions[col].width = ancho
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    nombre = f"ip_vlan_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=nombre,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
