# Puerto Lima - Comparador de Rutas de Exportación

Este proyecto implementa un sistema de comparación de alternativas de exportación entre los puertos de Timbúes (Argentina) y Lima (Perú). La aplicación permite calcular y visualizar los costos de exportación para diferentes orígenes y cargas, ayudando a tomar decisiones logísticas óptimas.

## Características

- Cálculo de rutas óptimas utilizando OSRM (Open Source Routing Machine)
- Comparación detallada de costos entre puertos alternativos
- Visualización de rutas en mapas interactivos
- Gráficos comparativos de costos
- Generación de reportes PDF
- Interfaz web responsiva

## Estructura del Proyecto

```
puerto-lima/
├── backend/                  # API y lógica de negocio
│   ├── api/                  # Endpoints de la API
│   │   └── endpoints/        # Definición de endpoints
│   ├── config/               # Configuración
│   └── utils/                # Utilidades
│       ├── route_calculator.py   # Cálculo de rutas
│       ├── cost_calculator.py    # Cálculo de costos
│       ├── visualization.py      # Generación de visualizaciones
│       └── report_generator.py   # Generación de reportes
├── frontend/                 # Interfaz web
│   ├── css/                  # Estilos
│   ├── js/                   # Lógica JavaScript
│   └── index.html            # Página principal
└── README.md                 # Este archivo
```

## Requisitos

### Backend
- Python 3.8+
- FastAPI
- Uvicorn
- Pandas
- Matplotlib
- Folium
- WeasyPrint
- Polyline
- Requests

### Frontend
- Navegador web moderno
- Conexión a Internet (para cargar mapas y CDNs)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/KineticNexus/puerto-lima.git
   cd puerto-lima
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ejecutar el backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

4. Abrir el frontend:
   - Opción 1: Abrir `frontend/index.html` directamente en su navegador
   - Opción 2: Usar un servidor web simple
     ```bash
     # Desde la carpeta raíz
     cd frontend
     python -m http.server 8080
     ```
     Luego acceder a http://localhost:8080

## Uso

1. Acceder a la aplicación web
2. Ingresar el nombre del origen y las coordenadas (o seleccionar una ubicación predefinida)
3. Especificar la cantidad de carga en toneladas
4. Hacer clic en "Calcular"
5. Revisar los resultados en los gráficos y tablas
6. Opcionalmente, descargar un reporte PDF completo

## API Endpoints

- `GET /api/` - Verificar que la API está funcionando
- `POST /api/route/calcular` - Calcular rutas y costos
- `POST /api/route/reporte` - Generar reporte PDF

## Configuración

Los parámetros principales de la aplicación se pueden configurar en el archivo `backend/config/default.py`:

- Coordenadas de los puertos
- Tarifas de fletes marítimos y terrestres
- Costos fijos portuarios
- Factores de corrección para rutas
- Configuración de visualización

## Licencia

[MIT](LICENSE)

## Contacto

Para consultas o soporte, contáctenos a través de GitHub o email.