"""
Configuración por defecto del modelo de análisis de exportación puerto-lima
Contiene todas las constantes y parámetros utilizados en el análisis.
"""

# Constantes y parámetros iniciales
TAMAÑO_SECTOR = 100000  # hectáreas por sector
COSTO_FLETE_TERRESTRE = 0.043  # USD/ton/km

# Coordenadas de los puertos
COORDENADAS_TIMBUES = (-33.18, -60.78)  # Latitud, Longitud (formato GeoJSON)
COORDENADAS_LIMA = (-34.15, -59.03)  # Latitud, Longitud (formato GeoJSON)

# Fletes marítimos por destino internacional (USD/ton)
FLETES_MARITIMOS = {
    "china": {
        "timbues": 40,    # USD/ton desde Timbúes a China
        "lima": 45        # USD/ton desde Lima a China
    },
    "europa": {
        "timbues": 35,    # USD/ton desde Timbúes a Europa
        "lima": 38        # USD/ton desde Lima a Europa
    },
    "brasil": {
        "timbues": 20,    # USD/ton desde Timbúes a Brasil
        "lima": 22        # USD/ton desde Lima a Brasil
    }
}

# Cultivos analizados
CULTIVOS = ["soja", "maiz", "trigo", "sorgo"]

# Rendimientos por región (ton/hectárea)
RENDIMIENTOS_POR_REGION = {
    "zona_nucleo": {
        "soja": 3.5,
        "maiz": 9.0,
        "trigo": 3.8,
        "sorgo": 5.0
    },
    "nea": {
        "soja": 2.8,
        "maiz": 6.0,
        "trigo": 2.5,
        "sorgo": 3.5
    },
    "noa": {
        "soja": 2.5,
        "maiz": 5.5,
        "trigo": 2.3,
        "sorgo": 3.2
    },
    "cuyo": {
        "soja": 2.2,
        "maiz": 6.2,
        "trigo": 3.0,
        "sorgo": 3.8
    }
}

# Proporción típica de uso de tierra por cultivo en rotación
PROPORCION_USO_TIERRA = {
    "zona_nucleo": {
        "soja": 0.50,   # 50% del área dedicada a soja
        "maiz": 0.30,   # 30% a maíz
        "trigo": 0.15,  # 15% a trigo
        "sorgo": 0.05   # 5% a sorgo
    },
    "nea": {
        "soja": 0.45,
        "maiz": 0.25,
        "trigo": 0.10,
        "sorgo": 0.20
    },
    "noa": {
        "soja": 0.40,
        "maiz": 0.30,
        "trigo": 0.10,
        "sorgo": 0.20
    },
    "cuyo": {
        "soja": 0.30,
        "maiz": 0.35,
        "trigo": 0.25,
        "sorgo": 0.10
    }
}

# Factores de corrección de ruta por tipo de región
FACTORES_CORRECCION_RUTA = {
    "zona_nucleo": 1.2,  # Mejor infraestructura vial
    "nea": 1.4,          # Infraestructura vial menos desarrollada
    "noa": 1.5,          # Rutas con más curvas y montañas
    "cuyo": 1.45,        # Rutas con condiciones mixtas
    "default": 1.3       # Valor por defecto
}

# Costos adicionales por puerto (USD/ton)
COSTOS_ADICIONALES = {
    "timbues": {
        "carga": 2.5,
        "peajes": 1.0,
        "tiempo_espera": 1.2  # Costo equivalente por tiempo de espera
    },
    "lima": {
        "carga": 3.0,
        "peajes": 0.8,
        "tiempo_espera": 0.9
    }
}

# Configuración de visualización
COLORES = {
    "TIMBUES_MAX": "#006400",    # Verde oscuro (máxima ventaja para Timbúes)
    "TIMBUES_MED": "#32CD32",    # Verde medio
    "TIMBUES_MIN": "#98FB98",    # Verde claro (ventaja leve para Timbúes)
    "NEUTRAL": "#F5F5F5",        # Casi blanco (zonas neutrales)
    "LIMA_MIN": "#ADD8E6",       # Azul claro (ventaja leve para Lima)
    "LIMA_MED": "#4169E1",       # Azul medio
    "LIMA_MAX": "#00008B",       # Azul oscuro (máxima ventaja para Lima)
    "EMPRESAS_TIMBUES": "#FF4500", # Naranja para empresas que prefieren Timbúes
    "EMPRESAS_LIMA": "#800080"     # Púrpura para empresas que prefieren Lima
}

# Umbrales para clasificación
UMBRAL_SIGNIFICATIVO = 1.0  # USD/ton (diferencia mínima para considerar preferencia por un puerto)
UMBRAL_ALTO_IMPACTO = 5.0   # USD/ton (diferencia para identificar zonas de alto impacto)
UMBRAL_DOMINANCIA = 70      # Porcentaje mínimo para considerar preferencia dominante en una región

# Configuración de conexiones externas
# OSRM para cálculo de rutas
OSRM_CONFIG = {
    "base_url": "http://osrm:5000",  # URL del servicio OSRM dentro de Docker
    "profile": "car",                # Perfil de cálculo (car es el estándar, pero puede usarse truck)
    "timeout": 30                    # Timeout para solicitudes en segundos
}

# GeoServer para servicios GIS
GEOSERVER_CONFIG = {
    "base_url": "http://geoserver:8080/geoserver",
    "workspace": "puerto-lima",
    "username": "admin",
    "password": "geoserver"
}

# Mapbox para visualización
MAPBOX_CONFIG = {
    "access_token": "YOUR_MAPBOX_ACCESS_TOKEN",  # Reemplazar con token real en producción
    "style": "mapbox://styles/mapbox/light-v10",
    "center": [-61.5, -33.5],  # Centro aproximado de la región de interés
    "zoom": 5
}

# Supabase para datos empresariales
SUPABASE_CONFIG = {
    "url": "YOUR_SUPABASE_URL",      # Reemplazar con URL real
    "key": "YOUR_SUPABASE_API_KEY",  # Reemplazar con key real
    "table_empresas": "empresas"
}

# Configuración para generación de reportes
REPORT_CONFIG = {
    "template_path": "backend/templates/reports",
    "output_path": "data/exports",
    "default_format": "pdf",
    "page_size": "A4"
}

# Configuración de análisis de sensibilidad
SENSITIVITY_CONFIG = {
    "variables": {
        "flete_terrestre": [0.035, 0.043, 0.050],  # Escenarios bajo/actual/alto
        "flete_maritimo_factor": [0.9, 1.0, 1.1]   # Factor multiplicador para fletes marítimos
    },
    "threshold": 1.0  # Umbral para contar cambios de puerto óptimo
}