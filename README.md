# Puerto-Lima

Análisis comparativo de costos de exportación entre puertos Timbúes y Lima (Zárate).

## Descripción

Esta aplicación permite realizar un análisis detallado de costos logísticos para determinar la ruta de exportación más eficiente entre los puertos de Timbúes y Lima (Zárate) en Argentina. El sistema divide el territorio en sectores, calcula costos de transporte terrestre y marítimo, y genera visualizaciones de gradiente para identificar la línea divisoria de conveniencia entre ambos puertos.

## Características

- División del territorio argentino en sectores para análisis granular
- Cálculo preciso de distancias por rutas terrestres reales
- Análisis de costos de flete terrestre y marítimo
- Visualización de gradiente de preferencia entre puertos
- Análisis de sensibilidad para evaluar robustez de las recomendaciones
- Recomendaciones específicas para empresas exportadoras
- Generación de reportes detallados en PDF

## Estructura del Proyecto

```
puerto-lima/
├── backend/               # Servidor backend con API REST y MCP
│   ├── app.py             # Punto de entrada de la aplicación Flask
│   ├── config/            # Configuraciones por ambiente
│   ├── db/                # Modelos y conexión a base de datos
│   ├── gis/               # Funcionalidades GIS
│   │   ├── routes.py      # Cálculo de rutas (OSRM)
│   │   └── sectors.py     # División territorial (PostGIS)
│   ├── models/            # Modelos de datos
│   ├── services/          # Lógica de negocio
│   └── mcp/               # Integraciones MCP
│       ├── routes_mcp.py  # MCP para cálculo de rutas
│       ├── gis_mcp.py     # MCP para operaciones GIS
│       ├── data_mcp.py    # MCP para datos empresariales
│       ├── viz_mcp.py     # MCP para visualización
│       ├── analysis_mcp.py# MCP para análisis de sensibilidad
│       └── report_mcp.py  # MCP para generación de reportes
├── frontend/              # Aplicación React para interfaz de usuario
│   ├── public/            # Archivos estáticos
│   ├── src/               # Código fuente React
│   │   ├── components/    # Componentes reutilizables
│   │   ├── pages/         # Páginas principales
│   │   ├── hooks/         # Hooks personalizados
│   │   ├── services/      # Servicios API y MCP
│   │   └── utils/         # Utilidades generales
│   └── package.json       # Dependencias
├── data/                  # Datos para la aplicación
│   ├── initial/           # Datos iniciales (script de carga)
│   └── exports/           # Reportes exportados
├── docker/                # Configuración Docker
│   ├── docker-compose.yml # Orquestación de servicios
│   ├── backend.Dockerfile # Dockerfile para backend
│   ├── frontend.Dockerfile# Dockerfile para frontend
│   ├── osrm.Dockerfile    # Dockerfile para servidor OSRM
│   ├── postgis.Dockerfile # Dockerfile para PostgreSQL/PostGIS
│   └── geoserver.Dockerfile # Dockerfile para GeoServer
└── docs/                  # Documentación
    ├── api.md             # Documentación de la API
    ├── mcp.md             # Documentación de las integraciones MCP
    └── user_manual.md     # Manual de usuario
```

## Tecnologías

- **Backend**: Python con Flask, SQLAlchemy
- **Frontend**: React, Material-UI, Mapbox GL JS
- **Base de datos**: PostgreSQL con extensión PostGIS
- **GIS**: GeoServer, OSRM (Open Source Routing Machine)
- **Reportes**: WeasyPrint
- **Despliegue**: Docker, Docker Compose
- **Integraciones MCP**:
  - Cálculo de rutas (OSRM)
  - Operaciones GIS (PostGIS/GeoServer)
  - Manejo de datos (Supabase/PostgreSQL)
  - Visualización (Mapbox)
  - Análisis de sensibilidad (Python/NumPy)
  - Generación de reportes (WeasyPrint)

## Configuración y Ejecución

### Requisitos
- Docker y Docker Compose
- Node.js 16+ (desarrollo frontend)
- Python 3.9+ (desarrollo backend)

### Instalación y Ejecución

1. Clonar el repositorio:
```bash
git clone https://github.com/KineticNexus/puerto-lima.git
cd puerto-lima
```

2. Ejecutar con Docker Compose:
```bash
docker-compose -f docker/docker-compose.yml up
```

3. Acceder a la aplicación:
- Frontend: http://localhost:3000
- API Backend: http://localhost:5000
- Documentación API: http://localhost:5000/docs

## Configuración de Variables

Las variables del modelo se pueden configurar a través de la interfaz gráfica o modificando los archivos de configuración:

- `backend/config/default.py`: Variables por defecto
- `backend/config/production.py`: Sobrescrituras para producción

Variables principales configurables:
- Costos de flete terrestre (USD/ton/km)
- Fletes marítimos por destino
- Factores de corrección de ruta
- Costos adicionales por puerto
- Rendimientos por región
- Proporción de uso de tierra

## Licencia

MIT