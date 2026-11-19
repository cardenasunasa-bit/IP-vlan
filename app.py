import io
import sqlite3
import ipaddress
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-por-otra"
DB = "clientes.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS asignaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                ip TEXT NOT NULL,
                vlan INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                nota TEXT,
                UNIQUE (ip, vlan)
            )
        """)


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    with get_db() as conn:
        if q:
            like = f"%{q}%"
            filas = conn.execute(
                "SELECT * FROM asignaciones WHERE cliente LIKE ? OR ip LIKE ? OR CAST(vlan AS TEXT) LIKE ?",
                (like, like, like),
            ).fetchall()
        else:
            filas = conn.execute("SELECT * FROM asignaciones").fetchall()
    filas = sorted(filas, key=lambda f: (f["vlan"], ipaddress.ip_address(f["ip"])))
    return render_template("index.html", filas=filas, q=q)


@app.route("/agregar", methods=["POST"])
def agregar():
    cliente = request.form.get("cliente", "").strip()
    ip = request.form.get("ip", "").strip()
    vlan = request.form.get("vlan", "").strip()
    nota = request.form.get("nota", "").strip()

    if not cliente or not ip or not vlan:
        flash("Cliente, IP y VLAN son obligatorios.", "error")
        return redirect(url_for("index"))

    try:
        ip = str(ipaddress.ip_address(ip))
    except ValueError:
        flash("La IP no es valida.", "error")
        return redirect(url_for("index"))

    if not vlan.isdigit() or not (1 <= int(vlan) <= 4094):
        flash("La VLAN debe ser un numero entre 1 y 4094.", "error")
        return redirect(url_for("index"))

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO asignaciones (cliente, ip, vlan, fecha, nota) VALUES (?, ?, ?, ?, ?)",
                (cliente, ip, int(vlan), datetime.now().strftime("%Y-%m-%d %H:%M"), nota),
            )
        flash(f"Guardado: {cliente} con IP {ip} en VLAN {vlan}.", "ok")
    except sqlite3.IntegrityError:
        with get_db() as conn:
            otro = conn.execute(
                "SELECT cliente FROM asignaciones WHERE ip = ? AND vlan = ?", (ip, int(vlan))
            ).fetchone()
        flash(f"CONFLICTO: la IP {ip} ya esta en uso en la VLAN {vlan} por el cliente {otro['cliente']}.", "error")
    return redirect(url_for("index"))


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    with get_db() as conn:
        conn.execute("DELETE FROM asignaciones WHERE id = ?", (id,))
    flash("Registro eliminado. La IP quedo libre.", "ok")
    return redirect(url_for("index"))


@app.route("/exportar")
def exportar():
    with get_db() as conn:
        filas = conn.execute("SELECT * FROM asignaciones").fetchall()
    filas = sorted(filas, key=lambda f: (f["vlan"], ipaddress.ip_address(f["ip"])))

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
    return send_file(
        buf,
        as_attachment=True,
        download_name=nombre,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
