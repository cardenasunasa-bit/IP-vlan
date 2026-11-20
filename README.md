# Gestor de IP + VLAN para ISP

Aplicación web estática lista para publicar con GitHub Pages.

## Funciones
- Registrar IPv4 y VLAN (1 a 4094).
- Permite reutilizar una IP en VLAN diferentes.
- Bloquea duplicados de la combinación IP + VLAN.
- Campos adicionales: cliente, ONU/puerto, NAP y observaciones.
- Buscar, editar y eliminar.
- Guardado automático en el almacenamiento local del navegador.
- Exportar a Excel (.xlsx), importar Excel y descargar copia JSON.
- Diseño adaptable a Android y computador.

## Publicar en GitHub Pages
1. Crea un repositorio en GitHub, por ejemplo `gestor-ip-vlan`.
2. Sube `index.html` y este `README.md` a la raíz del repositorio.
3. En GitHub entra a **Settings → Pages**.
4. En **Build and deployment**, selecciona **Deploy from a branch**.
5. Selecciona la rama `main` y la carpeta `/ (root)`, luego pulsa **Save**.
6. Espera a que GitHub Pages genere el enlace. Abre ese enlace desde tu Android.

## Importante sobre la memoria
Los registros quedan guardados en el navegador y dispositivo donde se ingresan. GitHub Pages publica la aplicación, pero no sincroniza datos entre celulares ni crea una base de datos en la nube. Para evitar perder información, descarga periódicamente el Excel o el respaldo JSON. Puedes importar esos archivos en otro dispositivo.

## Excel
La exportación/importación `.xlsx` usa la librería SheetJS desde CDN; se requiere conexión a internet al cargar la página para disponer de esa función.
