# Gestor IP + VLAN para ISP

## Publicación en GitHub Pages
Para que la aplicación web funcione en GitHub Pages, el archivo principal debe llamarse `index.html` y estar en la raíz del repositorio.

## Funciones
- Registrar direcciones IPv4 y VLAN.
- Sugerir VLAN según el patrón 10.x.0.x (por ejemplo, 10.1.0.x -> VLAN 101).
- Evitar duplicados de la combinación IP + VLAN.
- Registrar cliente, ONU/puerto, NAP y observaciones.
- Buscar, editar, eliminar, importar y exportar.
- Conexión con Supabase para compartir registros entre dispositivos.

## Configuración
La tabla `public.ip_registros` debe existir en Supabase y tener RLS activado con políticas para usuarios autenticados. No publiques contraseñas ni claves secretas de Supabase.
