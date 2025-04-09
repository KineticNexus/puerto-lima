"""
Archivo de configuración por defecto para la aplicación puerto-lima.

Este módulo define constantes y variables globales utilizadas en todo el sistema,
incluyendo coordenadas de puertos, costos de fletes y factores de corrección.
"""

# Coordenadas geográficas de los puertos
COORDENADAS_TIMBUES = [-60.7489, -32.6636]  # [longitud, latitud]
COORDENADAS_LIMA = [-59.0344, -34.1073]     # [longitud, latitud]

# Fletes marítimos por destino (USD/ton)
FLETES_MARITIMOS = {
    "china": {
        "timbues": 45.0,
        "lima": 47.5
    },
    "europa": {
        "timbues": 35.0,
        "lima": 36.5
    },
    "brasil": {
        "timbues": 25.0,
        "lima": 24.0
    }
}

# Costo flete terrestre (USD/ton/km)
COSTO_FLETE_TERRESTRE = 0.12

# Factores de corrección por tipo de ruta
FACTORES_CORRECCION_RUTA = {
    "buenos_aires": 1.15,    # Mayor congestión
    "santa_fe": 1.05,        # Rutas normales
    "cordoba": 1.10,         # Algunas rutas secundarias
    "entre_rios": 1.20,      # Más rutas secundarias
    "default": 1.10          # Factor por defecto
}

# Configuración de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "database": "puerto_lima"
}

# Configuración de servicios externos
OSRM_API_URL = "http://router.project-osrm.org"
MAPBOX_ACCESS_TOKEN = "YOUR_MAPBOX_ACCESS_TOKEN"

# Configuración de visualización
VISUALIZATION_CONFIG = {
    "color_positive": "#FF0000",    # Rojo (favorable a Timbúes)
    "color_negative": "#0000FF",    # Azul (favorable a Lima)
    "color_neutral": "#FFFFFF",     # Blanco (neutral)
    "opacity": 0.7,
    "line_width": 2
}

# Valores por defecto para análisis de sensibilidad
SENSITIVITY_DEFAULT_VALUES = {
    "flete_terrestre_min": 0.08,
    "flete_terrestre_max": 0.16,
    "flete_terrestre_step": 0.01,
    "flete_maritimo_min_factor": 0.8,
    "flete_maritimo_max_factor": 1.2,
    "flete_maritimo_step_factor": 0.05
}

# Configuración para generación de reportes
REPORT_CONFIG = {
    "template_dir": "templates/reports",
    "default_template": "default_report.html",
    "company_logo": "static/img/logo.png",
    "page_size": "A4",
    "margin": "1cm"
}