# Control de IP y VLAN para ISP

App web con login para registrar la IP y la VLAN de cada cliente, evitar duplicados dentro de la misma VLAN y exportar todo a Excel (ordenado por VLAN e IP).

- Usuario por defecto: `admin123`
- Contrasena por defecto: `admin`
- Cambialos con las variables `APP_USER` y `APP_PASSWORD` antes de usar datos reales.

## Probar en tu computador

    python -m venv venv
    source venv/bin/activate        (en Windows: venv\Scripts\activate)
    pip install -r requirements.txt
    python app.py

Abre http://localhost:5000 (sin DATABASE_URL usa un archivo SQLite local).

## Ponerla en internet (gratis)

### 1. Base de datos en Neon (para que los datos no se borren)
1. Crea una cuenta en https://neon.tech y un proyecto nuevo.
2. Copia la cadena de conexion ("Connection string"), algo como
   `postgresql://usuario:clave@host/neondb?sslmode=require`.

### 2. Aplicacion en Render
1. Sube este proyecto a tu repositorio de GitHub.
2. En https://render.com entra con GitHub y elige New > Blueprint (o New > Web Service).
3. Selecciona el repositorio. Render lee `render.yaml`.
4. Cuando pida `DATABASE_URL`, pega la cadena de Neon.
5. Cambia `APP_USER` y `APP_PASSWORD` por unos propios.
6. Pulsa Deploy. Al terminar tendras un link publico `https://control-ip-vlan-xxxx.onrender.com`.

Nota: en el plan gratis de Render la pagina se duerme si nadie la usa y tarda cerca de un minuto en despertar.

## Regla anti-duplicados
La tabla tiene una restriccion UNIQUE sobre la pareja (IP, VLAN): la misma IP puede estar en VLANs distintas, pero no repetirse dentro de la misma VLAN.
