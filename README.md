# Sistema de gestión de visitantes y proveedores

Aplicación de escritorio en Python con Tkinter y SQLite, acompañada de un formulario web para que visitantes y proveedores registren personalmente sus datos desde un enlace.

## Funcionalidades

- Inicio de sesión para el personal administrador.
- Generación de enlaces individuales de registro.
- Formulario web adaptable a celular y computadora.
- Ramas diferenciadas para visitantes y proveedores.
- Rama condicional de trabajos de alto riesgo para proveedores.
- Agenda de solicitudes, consulta de respuestas y actualización de estado.
- Indicadores y gráficas con Matplotlib.
- Exportación CSV compatible con Excel.
- Ventanas de escritorio con tamaño adaptable y desplazamiento vertical.
- Base de datos SQLite local (`visitantes.db`).

## Estructura

```text
gestion_visitantes/
├── main.py
├── web_form.py
├── requirements.txt
├── README.md
└── visitantes.db       # se crea al ejecutar
```

## Requisitos

- Python 3.10 o posterior.
- Windows, macOS o Linux con Tkinter disponible.
- Conexión a internet solo para instalar dependencias; el sistema local no requiere servicios externos.

## Instalación en VS Code

Abre esta carpeta en Visual Studio Code. En Terminal > Nuevo terminal, ejecuta:

```bash
python -m pip install -r requirements.txt
python main.py
```

En Windows también puedes utilizar `py` en lugar de `python`.

## Acceso inicial

- Usuario: `admin`
- Contraseña: `admin123`

Cambia la contraseña y configura controles de acceso adecuados antes de utilizar el sistema con información real.

## Cómo generar el formulario

1. Inicia sesión en la aplicación de escritorio.
2. Selecciona **Generar enlace de registro**.
3. Copia el enlace y compártelo con la persona visitante o proveedora.
4. La persona completa el formulario en su propio navegador.
5. La respuesta aparece en **Agenda de registros**, **Tabla general** y **Resultados**.

Al generar el enlace, la aplicación inicia un servidor web local en el puerto 5000. El enlace con la dirección IP local sirve para la propia computadora y, normalmente, para dispositivos conectados a la misma red. Para que personas externas a esa red puedan responder desde cualquier lugar, hay que desplegar `web_form.py` en un servidor accesible por internet, configurar HTTPS y un dominio público, y adaptar la dirección base que se muestra al generar el enlace. No publiques el puerto directamente en internet sin HTTPS y controles de seguridad.

## Datos y privacidad

El formulario de referencia contempla datos de contacto, fechas de visita, aceptación de reglas y, en la rama de trabajos de alto riesgo, número de seguridad social e información de salud. Estos últimos son datos personales sensibles. Antes de utilizar el sistema con personas reales, configura un aviso de privacidad válido, define finalidad y periodo de conservación, limita el acceso, protege respaldos y revisa las obligaciones legales aplicables. No utilices los datos de demostración para producción.

## Alcance y notas

- La exportación se realiza en CSV con codificación compatible con Excel; no genera un archivo `.xlsx` nativo.
- El servidor local es para pruebas o redes internas. El acceso público requiere despliegue seguro.
- El sistema conserva las respuestas completas en SQLite. Protege el archivo `visitantes.db` y no lo compartas sin autorización.
- El contenido del formulario se reconstruyó a partir de los documentos de referencia, sustituyendo nombres propios y eliminando logotipos e imágenes instructivas. Se conservaron las instrucciones y compromisos como texto; no se incorporaron infografías.
