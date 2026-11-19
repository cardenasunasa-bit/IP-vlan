# Control de IP y VLAN para ISP

App web para registrar IP y VLAN por cliente, evitar duplicados dentro de la misma VLAN y exportar a Excel ordenado por VLAN e IP.

## Instalacion

    python -m venv venv
    source venv/bin/activate        (en Windows: venv\Scripts\activate)
    pip install -r requirements.txt
    python app.py

Abre http://localhost:5000 en el navegador.

## Regla anti-duplicados

La tabla tiene una restriccion UNIQUE sobre la pareja IP y VLAN. La misma IP puede existir en VLANs distintas, pero no repetirse dentro de la misma VLAN.
