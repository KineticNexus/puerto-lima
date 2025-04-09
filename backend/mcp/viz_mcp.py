"""
Módulo MCP para visualización de resultados usando Mapbox

Este módulo proporciona funcionalidades MCP para generar visualizaciones
interactivas de los resultados del análisis comparativo de exportación,
mostrando el gradiente de preferencia entre puertos y datos de empresas.
"""

import os
import json
import uuid
import math
from typing import Dict, List, Tuple, Optional, Any, Union

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.default import MAPBOX_CONFIG, COLORES

class MapboxVisualizationMCP:
    """
    Implementación MCP para visualización de resultados usando Mapbox.
    
    Proporciona métodos para:
    - Generar mapas de gradiente
    - Visualizar ubicaciones de empresas
    - Mostrar líneas divisorias
    - Crear leyendas y paneles informativos
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el servicio MCP con la configuración de Mapbox.
        
        Args:
            config: Configuración opcional que sobreescribe la configuración por defecto
        """
        self.config = config or MAPBOX_CONFIG
        self.access_token = self.config["access_token"]
        self.default_style = self.config["style"]
        self.default_center = self.config["center"]
        self.default_zoom = self.config["zoom"]
        self.colors = COLORES
        
        # Directorio para guardar los HTML generados (si se usa en modo local)
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      "../data/exports/visualizations")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def handle_request(self, action: str, context: Dict) -> Dict:
        """
        Punto de entrada principal para manejar solicitudes MCP.
        
        Args:
            action: Acción a realizar
            context: Contexto con datos para la acción
            
        Returns:
            Resultado de la acción solicitada
        """
        action_handlers = {
            "create_gradient_map": self.create_gradient_map,
            "create_company_map": self.create_company_map,
            "create_complete_analysis_map": self.create_complete_analysis_map,
            "generate_html_visualization": self.generate_html_visualization,
        }
        
        if action not in action_handlers:
            return {
                "error": f"Acción no soportada: {action}",
                "supported_actions": list(action_handlers.keys())
            }
        
        return action_handlers[action](context)
    
    def create_gradient_map(self, context: Dict) -> Dict:
        """
        Crea un mapa que muestra el gradiente de preferencia entre puertos.
        
        Args:
            context: Diccionario con:
                - sectors: lista de sectores con sus coordenadas y diferenciales
                - min_differential: valor diferencial mínimo (ventaja máxima para Timbúes)
                - max_differential: valor diferencial máximo (ventaja máxima para Lima)
                - center (opcional): centro del mapa [lon, lat]
                - zoom (opcional): nivel de zoom
                
        Returns:
            Configuración para un mapa Mapbox con gradiente
        """
        try:
            # Validar datos de entrada
            sectors = context.get("sectors", [])
            
            if not sectors:
                return {"error": "Se requieren datos de sectores"}
            
            # Obtener valores extremos para el gradiente
            min_diff = context.get("min_differential")
            max_diff = context.get("max_differential")
            
            if min_diff is None or max_diff is None:
                # Calcular valores extremos si no se proporcionaron
                differentials = [sector.get("differential", 0) for sector in sectors]
                min_diff = min(differentials)
                max_diff = max(differentials)
            
            # Normalizar para que el valor absoluto máximo sea 1
            max_abs_diff = max(abs(min_diff), abs(max_diff))
            normalize_factor = 1.0 / max_abs_diff if max_abs_diff > 0 else 1.0
            
            # Preparar GeoJSON para los sectores
            features = []
            
            for sector in sectors:
                # Asegurar que todas las propiedades necesarias existan
                if "coordinates" not in sector or "differential" not in sector:
                    continue
                
                # Normalizar diferencial para escala de colores (-1 a 1)
                differential = sector["differential"]
                normalized_diff = differential * normalize_factor
                
                # Determinar color basado en diferencial normalizado
                color = self._get_gradient_color(normalized_diff)
                
                # Crear feature GeoJSON
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": sector.get("id", str(uuid.uuid4())[:8]),
                        "differential": differential,
                        "normalized_diff": normalized_diff,
                        "color": color,
                        "region": sector.get("region", ""),
                        "production": sector.get("produccionTotal", 0),
                        "description": f"Diferencial: {differential:.2f} USD/ton"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": self._create_sector_polygon(sector["coordinates"])
                    }
                }
                
                features.append(feature)
            
            # Crear estructura GeoJSON
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # Crear configuración para Mapbox
            mapbox_config = {
                "container": "map",
                "style": self.default_style,
                "center": context.get("center", self.default_center),
                "zoom": context.get("zoom", self.default_zoom),
                "accessToken": self.access_token,
                "data": {
                    "type": "geojson",
                    "data": geojson
                },
                "layers": [
                    {
                        "id": "sectors-fill",
                        "type": "fill",
                        "source": "data",
                        "paint": {
                            "fill-color": ["get", "color"],
                            "fill-opacity": 0.7
                        }
                    },
                    {
                        "id": "sectors-outline",
                        "type": "line",
                        "source": "data",
                        "paint": {
                            "line-color": "#000000",
                            "line-width": 1,
                            "line-opacity": 0.5
                        }
                    }
                ],
                "legend": {
                    "title": "Diferencial de costo (USD/ton)",
                    "min_value": min_diff,
                    "max_value": max_diff,
                    "min_color": self.colors["TIMBUES_MAX"],
                    "neutral_color": self.colors["NEUTRAL"],
                    "max_color": self.colors["LIMA_MAX"],
                    "min_label": "Ventaja Timbúes",
                    "neutral_label": "Neutral",
                    "max_label": "Ventaja Lima"
                }
            }
            
            return {
                "status": "success",
                "mapbox_config": mapbox_config,
                "stats": {
                    "sectors_count": len(features),
                    "min_differential": min_diff,
                    "max_differential": max_diff
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error al crear mapa de gradiente: {str(e)}"
            }
    
    def create_company_map(self, context: Dict) -> Dict:
        """
        Crea un mapa que muestra las empresas y sus recomendaciones.
        
        Args:
            context: Diccionario con:
                - companies: lista de empresas con coordenadas y recomendaciones
                - center (opcional): centro del mapa [lon, lat]
                - zoom (opcional): nivel de zoom
                
        Returns:
            Configuración para un mapa Mapbox con las empresas
        """
        try:
            # Validar datos de entrada
            companies = context.get("companies", [])
            
            if not companies:
                return {"error": "Se requieren datos de empresas"}
            
            # Preparar GeoJSON para las empresas
            features = []
            
            for company in companies:
                # Asegurar que todas las propiedades necesarias existan
                if "coordenadas" not in company:
                    continue
                
                # Determinar color y tamaño basado en volumen y puerto óptimo
                puerto_optimo = company.get("puertoOptimo", "")
                volume = company.get("volumenAnual", 0)
                ahorro = company.get("ahorroAnual", 0)
                
                # Seleccionar color según puerto óptimo
                if puerto_optimo.lower() == "timbúes" or puerto_optimo.lower() == "timbues":
                    color = self.colors["EMPRESAS_TIMBUES"]
                else:
                    color = self.colors["EMPRESAS_LIMA"]
                
                # Calcular tamaño según volumen (entre 5 y 15 px)
                size = 5 + min(10, math.sqrt(volume) / 100)
                
                # Calcular grosor del borde según ahorro (entre 1 y 5 px)
                border_width = 1 + min(4, math.log10(max(1, ahorro)) / 2)
                
                # Crear feature GeoJSON
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": company.get("nombre", str(uuid.uuid4())[:8]),
                        "name": company.get("nombre", "Empresa"),
                        "volume": volume,
                        "savings": ahorro,
                        "port": puerto_optimo,
                        "color": color,
                        "size": size,
                        "border_width": border_width,
                        "description": f"{company.get('nombre', 'Empresa')}<br>" +
                                       f"Puerto óptimo: {puerto_optimo}<br>" +
                                       f"Volumen: {volume:,} ton/año<br>" +
                                       f"Ahorro potencial: ${ahorro:,.2f} USD/año"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": self._format_coordinates(company["coordenadas"])
                    }
                }
                
                features.append(feature)
            
            # Crear estructura GeoJSON
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # Crear configuración para Mapbox
            mapbox_config = {
                "container": "map",
                "style": self.default_style,
                "center": context.get("center", self.default_center),
                "zoom": context.get("zoom", self.default_zoom),
                "accessToken": self.access_token,
                "data": {
                    "type": "geojson",
                    "data": geojson
                },
                "layers": [
                    {
                        "id": "companies-circle",
                        "type": "circle",
                        "source": "data",
                        "paint": {
                            "circle-color": ["get", "color"],
                            "circle-radius": ["get", "size"],
                            "circle-stroke-width": ["get", "border_width"],
                            "circle-stroke-color": "#ffffff"
                        }
                    },
                    {
                        "id": "companies-label",
                        "type": "symbol",
                        "source": "data",
                        "layout": {
                            "text-field": ["get", "name"],
                            "text-font": ["Open Sans Bold"],
                            "text-size": 12,
                            "text-offset": [0, 1.5],
                            "text-anchor": "top"
                        },
                        "paint": {
                            "text-color": "#000000",
                            "text-halo-color": "#ffffff",
                            "text-halo-width": 1
                        }
                    }
                ],
                "legend": {
                    "items": [
                        {
                            "color": self.colors["EMPRESAS_TIMBUES"],
                            "label": "Empresa: óptimo Timbúes"
                        },
                        {
                            "color": self.colors["EMPRESAS_LIMA"],
                            "label": "Empresa: óptimo Lima"
                        }
                    ]
                }
            }
            
            return {
                "status": "success",
                "mapbox_config": mapbox_config,
                "stats": {
                    "companies_count": len(features),
                    "timbues_count": sum(1 for f in features if f["properties"]["port"].lower() in ["timbúes", "timbues"]),
                    "lima_count": sum(1 for f in features if f["properties"]["port"].lower() == "lima"),
                    "total_savings": sum(f["properties"]["savings"] for f in features)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error al crear mapa de empresas: {str(e)}"
            }
    
    def create_complete_analysis_map(self, context: Dict) -> Dict:
        """
        Crea un mapa completo que combina el gradiente de sectores y las empresas.
        
        Args:
            context: Diccionario con:
                - sectors: lista de sectores con sus coordenadas y diferenciales
                - companies: lista de empresas con coordenadas y recomendaciones
                - ports: coordenadas de los puertos [{"name": "Timbúes", "coordinates": [lon, lat]}, ...]
                - min_differential: valor diferencial mínimo
                - max_differential: valor diferencial máximo
                - center (opcional): centro del mapa [lon, lat]
                - zoom (opcional): nivel de zoom
                - sensitivity_info (opcional): información del análisis de sensibilidad
                
        Returns:
            Configuración completa para un mapa Mapbox con todos los elementos
        """
        try:
            # Crear configuraciones de mapas separados
            gradient_context = {
                "sectors": context.get("sectors", []),
                "min_differential": context.get("min_differential"),
                "max_differential": context.get("max_differential"),
            }
            
            company_context = {
                "companies": context.get("companies", []),
            }
            
            gradient_result = self.create_gradient_map(gradient_context)
            company_result = self.create_company_map(company_context)
            
            if "error" in gradient_result or "error" in company_result:
                errors = []
                if "error" in gradient_result:
                    errors.append(f"Error en mapa de gradiente: {gradient_result['error']}")
                if "error" in company_result:
                    errors.append(f"Error en mapa de empresas: {company_result['error']}")
                return {"status": "error", "errors": errors}
            
            # Combinar ambos mapas
            gradient_config = gradient_result["mapbox_config"]
            company_config = company_result["mapbox_config"]
            
            # Tomar configuración base del mapa de gradiente
            combined_config = gradient_config.copy()
            
            # Añadir fuente de datos de empresas
            combined_config["data"]["companies"] = company_config["data"]["data"]
            
            # Añadir capas de empresas
            for layer in company_config["layers"]:
                layer["source"] = "companies"  # Cambiar la fuente
                combined_config["layers"].append(layer)
            
            # Añadir puertos al mapa
            ports = context.get("ports", [])
            if ports:
                port_features = []
                
                for port in ports:
                    if "name" not in port or "coordinates" not in port:
                        continue
                    
                    port_feature = {
                        "type": "Feature",
                        "properties": {
                            "name": port["name"],
                            "description": f"Puerto: {port['name']}",
                            "icon": "harbor"
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": self._format_coordinates(port["coordinates"])
                        }
                    }
                    
                    port_features.append(port_feature)
                
                # Añadir fuente de datos de puertos
                combined_config["data"]["ports"] = {
                    "type": "geojson",
                    "data": {
                        "type": "FeatureCollection",
                        "features": port_features
                    }
                }
                
                # Añadir capas de puertos
                combined_config["layers"].append({
                    "id": "ports-icon",
                    "type": "symbol",
                    "source": "ports",
                    "layout": {
                        "icon-image": "harbor-15",
                        "icon-size": 1.5,
                        "text-field": ["get", "name"],
                        "text-font": ["Open Sans Semibold"],
                        "text-offset": [0, 1.2],
                        "text-anchor": "top"
                    },
                    "paint": {
                        "text-color": "#000000",
                        "text-halo-color": "#ffffff",
                        "text-halo-width": 2
                    }
                })
            
            # Combinar leyendas
            combined_config["legend"]["items"] = company_config["legend"]["items"]
            
            # Añadir panel de estadísticas
            stats = {
                **gradient_result["stats"],
                **company_result["stats"]
            }
            
            # Añadir información de sensibilidad si está disponible
            if "sensitivity_info" in context:
                sensitivity = context["sensitivity_info"]
                combined_config["sensitivity_panel"] = {
                    "title": "Análisis de Sensibilidad",
                    "content": sensitivity.get("comentarioGeneral", ""),
                    "parameters": {
                        "most_sensitive": sensitivity.get("parametrosMasSensibles", []),
                        "least_sensitive": sensitivity.get("parametrosMenosSensibles", [])
                    }
                }
            
            return {
                "status": "success",
                "mapbox_config": combined_config,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error al crear mapa de análisis completo: {str(e)}"
            }
    
    def generate_html_visualization(self, context: Dict) -> Dict:
        """
        Genera un archivo HTML con la visualización Mapbox para uso local.
        
        Args:
            context: Diccionario con:
                - mapbox_config: configuración del mapa
                - title (opcional): título de la visualización
                - filename (opcional): nombre del archivo a generar
                
        Returns:
            Ruta al archivo HTML generado
        """
        try:
            # Validar datos de entrada
            mapbox_config = context.get("mapbox_config")
            
            if not mapbox_config:
                return {"error": "Se requiere configuración de Mapbox"}
            
            title = context.get("title", "Análisis Comparativo Timbúes vs. Lima (Zárate)")
            filename = context.get("filename", f"visualization_{uuid.uuid4()}.html")
            
            # Crear contenido HTML
            html_content = self._generate_html_template(title, mapbox_config)
            
            # Guardar archivo
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            return {
                "status": "success",
                "file_path": file_path,
                "url": f"file://{file_path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error al generar visualización HTML: {str(e)}"
            }
    
    def _get_gradient_color(self, normalized_value: float) -> str:
        """
        Determina el color basado en un valor normalizado entre -1 y 1.
        
        Args:
            normalized_value: Valor normalizado (-1: máx ventaja Timbúes, 0: neutral, 1: máx ventaja Lima)
            
        Returns:
            Código de color en formato hexadecimal
        """
        if normalized_value < 0:
            # Ventaja para Timbúes (verde)
            intensity = abs(normalized_value)
            if intensity > 0.66:
                return self.colors["TIMBUES_MAX"]
            elif intensity > 0.33:
                return self.colors["TIMBUES_MED"]
            else:
                return self.colors["TIMBUES_MIN"]
        elif normalized_value > 0:
            # Ventaja para Lima (azul)
            intensity = normalized_value
            if intensity > 0.66:
                return self.colors["LIMA_MAX"]
            elif intensity > 0.33:
                return self.colors["LIMA_MED"]
            else:
                return self.colors["LIMA_MIN"]
        else:
            # Neutral
            return self.colors["NEUTRAL"]
    
    def _create_sector_polygon(self, center: List[float], size: float = 0.1) -> List[List[float]]:
        """
        Crea un polígono simplificado para un sector agrícola.
        
        Args:
            center: Coordenadas del centro [lon, lat]
            size: Tamaño del polígono en grados
            
        Returns:
            Lista de coordenadas que forman el polígono
        """
        # Si center es [lat, lon], convertimos a [lon, lat]
        center = self._format_coordinates(center)
        if isinstance(center, str):
            center = [float(x) for x in center.split(',')]
        
        lon, lat = center
        half_size = size / 2
        
        # Crear un polígono cuadrado simple
        return [[
            [lon - half_size, lat - half_size],
            [lon + half_size, lat - half_size],
            [lon + half_size, lat + half_size],
            [lon - half_size, lat + half_size],
            [lon - half_size, lat - half_size]
        ]]
    
    def _format_coordinates(self, coordinates: Union[List[float], Tuple[float, float]]) -> Union[List[float], str]:
        """
        Formatea coordenadas para asegurar que estén en orden [lon, lat].
        
        Args:
            coordinates: Lista o tupla de coordenadas
            
        Returns:
            Coordenadas en formato [lon, lat] o "lon,lat"
        """
        # Si las coordenadas están en formato [lat, lon] (común en muchas API)
        # necesitamos invertirlas para GeoJSON que espera [lon, lat]
        if len(coordinates) == 2:
            # Verificamos si están en formato lat,lon (común)
            if isinstance(coordinates[0], (int, float)) and isinstance(coordinates[1], (int, float)):
                if coordinates[0] >= -90 and coordinates[0] <= 90 and \
                coordinates[1] >= -180 and coordinates[1] <= 180:
                    # Están en formato lat,lon, invertimos
                    return [coordinates[1], coordinates[0]]
                else:
                    # Asumimos que ya están en formato lon,lat
                    return coordinates
        
        # Si llegamos aquí, devolvemos tal cual
        return coordinates
    
    def _generate_html_template(self, title: str, mapbox_config: Dict) -> str:
        """
        Genera un template HTML con la visualización Mapbox.
        
        Args:
            title: Título de la página
            mapbox_config: Configuración para Mapbox
            
        Returns:
            Contenido HTML completo
        """
        # Convertir configuración a JSON
        mapbox_json = json.dumps(mapbox_config, indent=2)
        
        # Template HTML básico
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
            <link href="https://api.mapbox.com/mapbox-gl-js/v2.12.0/mapbox-gl.css" rel="stylesheet">
            <script src="https://api.mapbox.com/mapbox-gl-js/v2.12.0/mapbox-gl.js"></script>
            <style>
                body {{ margin: 0; padding: 0; }}
                #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
                
                .map-overlay {{
                    position: absolute;
                    bottom: 15px;
                    right: 15px;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 5px;
                    padding: 10px;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.2);
                    font-family: Arial, sans-serif;
                    max-width: 320px;
                    overflow-y: auto;
                    max-height: 80%;
                }}
                
                .legend-title {{
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-size: 14px;
                    text-align: center;
                }}
                
                .gradient-bar {{
                    height: 15px;
                    width: 100%;
                    background: linear-gradient(to right, {mapbox_config['legend']['min_color']}, {mapbox_config['legend']['neutral_color']}, {mapbox_config['legend']['max_color']});
                    margin-bottom: 5px;
                }}
                
                .gradient-labels {{
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    margin-bottom: 15px;
                }}
                
                .legend-item {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 5px;
                    font-size: 12px;
                }}
                
                .legend-color {{
                    width: 15px;
                    height: 15px;
                    margin-right: 5px;
                }}
                
                .sensitivity-panel {{
                    margin-top: 15px;
                    padding-top: 10px;
                    border-top: 1px solid #ccc;
                }}
                
                .sensitivity-title {{
                    font-weight: bold;
                    margin-bottom: 5px;
                    font-size: 14px;
                }}
                
                .stats-panel {{
                    position: absolute;
                    top: 15px;
                    left: 15px;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 5px;
                    padding: 10px;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.2);
                    font-family: Arial, sans-serif;
                    max-width: 250px;
                    font-size: 12px;
                }}
                
                .stats-title {{
                    font-weight: bold;
                    margin-bottom: 5px;
                    font-size: 14px;
                }}
                
                .stats-item {{
                    margin-bottom: 3px;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <div class="map-overlay" id="legend">
                <div class="legend-title">{mapbox_config['legend']['title']}</div>
                
                <div class="gradient-bar"></div>
                <div class="gradient-labels">
                    <span>{mapbox_config['legend']['min_label']} ({mapbox_config['legend']['min_value']:.2f})</span>
                    <span>{mapbox_config['legend']['neutral_label']}</span>
                    <span>{mapbox_config['legend']['max_label']} ({mapbox_config['legend']['max_value']:.2f})</span>
                </div>
                
                <!-- Elementos de leyenda adicionales se agregarán aquí con JavaScript -->
                <div id="legend-items"></div>
                
                <!-- Panel de sensibilidad (si existe) -->
                <div id="sensitivity-panel" class="sensitivity-panel" style="display: none;">
                    <div class="sensitivity-title">Análisis de Sensibilidad</div>
                    <div id="sensitivity-content"></div>
                </div>
            </div>
            
            <div class="stats-panel" id="stats">
                <div class="stats-title">Estadísticas</div>
                <div id="stats-content"></div>
            </div>
            
            <script>
                // Configuración de Mapbox
                const config = {mapbox_json};
                
                // Inicializar mapa
                mapboxgl.accessToken = config.accessToken;
                const map = new mapboxgl.Map({{
                    container: 'map',
                    style: config.style,
                    center: config.center,
                    zoom: config.zoom
                }});
                
                map.on('load', function() {{
                    // Añadir fuentes de datos
                    map.addSource('sectors', {{
                        type: 'geojson',
                        data: config.data.data
                    }});
                    
                    // Añadir capas
                    config.layers.forEach(layer => {{
                        map.addLayer(layer);
                    }});
                    
                    // Añadir leyenda
                    if (config.legend.items) {{
                        const legendItems = document.getElementById('legend-items');
                        config.legend.items.forEach(item => {{
                            const div = document.createElement('div');
                            div.className = 'legend-item';
                            div.innerHTML = `
                                <div class="legend-color" style="background-color: ${{item.color}}"></div>
                                <div>${{item.label}}</div>
                            `;
                            legendItems.appendChild(div);
                        }});
                    }}
                    
                    // Añadir panel de sensibilidad
                    if (config.sensitivity_panel) {{
                        document.getElementById('sensitivity-panel').style.display = 'block';
                        document.getElementById('sensitivity-content').innerHTML = config.sensitivity_panel.content;
                    }}
                    
                    // Añadir estadísticas (ejemplo)
                    const statsContent = document.getElementById('stats-content');
                    statsContent.innerHTML = `
                        <div class="stats-item">Sectores analizados: ${{config.stats ? config.stats.sectors_count : 'N/A'}}</div>
                        <div class="stats-item">Empresas analizadas: ${{config.stats ? config.stats.companies_count : 'N/A'}}</div>
                        <div class="stats-item">Preferencia Timbúes: ${{config.stats ? config.stats.timbues_count : 'N/A'}} empresas</div>
                        <div class="stats-item">Preferencia Lima: ${{config.stats ? config.stats.lima_count : 'N/A'}} empresas</div>
                        <div class="stats-item">Ahorro potencial total: ${{config.stats ? '$' + (config.stats.total_savings / 1000000).toFixed(2) + 'M' : 'N/A'}}</div>
                    `;
                    
                    // Agregar navegación
                    map.addControl(new mapboxgl.NavigationControl());
                    
                    // Agregar popups para mostrar info al hacer hover
                    const popup = new mapboxgl.Popup({{
                        closeButton: false,
                        closeOnClick: false
                    }});
                    
                    map.on('mouseenter', 'sectors-fill', function(e) {{
                        map.getCanvas().style.cursor = 'pointer';
                        
                        const coordinates = e.lngLat;
                        const description = e.features[0].properties.description;
                        
                        popup.setLngLat(coordinates)
                            .setHTML(description)
                            .addTo(map);
                    }});
                    
                    map.on('mouseleave', 'sectors-fill', function() {{
                        map.getCanvas().style.cursor = '';
                        popup.remove();
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        return html


# Ejemplo de uso como servidor MCP
if __name__ == "__main__":
    import sys
    import argparse
    from flask import Flask, request, jsonify, send_file
    
    app = Flask(__name__)
    viz_mcp = MapboxVisualizationMCP()
    
    @app.route('/mcp/visualization', methods=['POST'])
    def handle_mcp_request():
        """Endpoint para recibir solicitudes MCP."""
        try:
            data = request.json
            action = data.get('action')
            context = data.get('context', {})
            
            if not action:
                return jsonify({"error": "Se requiere una acción"}), 400
                
            result = viz_mcp.handle_request(action, context)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": f"Error: {str(e)}"}), 500
    
    @app.route('/visualizations/<path:filename>', methods=['GET'])
    def serve_visualization(filename):
        """Sirve las visualizaciones HTML generadas."""
        file_path = os.path.join(viz_mcp.output_dir, filename)
        return send_file(file_path)
    
    parser = argparse.ArgumentParser(description='Servidor MCP para visualización con Mapbox')
    parser.add_argument('--host', default='0.0.0.0', help='Host para el servidor Flask')
    parser.add_argument('--port', type=int, default=5002, help='Puerto para el servidor Flask')
    parser.add_argument('--debug', action='store_true', help='Ejecutar en modo debug')
    
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=args.debug)