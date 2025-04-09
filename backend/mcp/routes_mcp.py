"""
Módulo MCP para cálculo de rutas terrestres utilizando OSRM

Este módulo proporciona funcionalidades MCP para calcular distancias y rutas
entre coordenadas utilizando Open Source Routing Machine (OSRM).
"""

import os
import json
import time
import requests
from typing import Dict, List, Tuple, Optional, Any, Union
from urllib.parse import urljoin

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.default import OSRM_CONFIG

class OSRMRouteMCP:
    """
    Implementación MCP para cálculo de rutas utilizando OSRM.
    
    Proporciona métodos para:
    - Calcular distancia óptima entre dos puntos
    - Calcular ruta completa con waypoints
    - Calcular matriz de distancias entre múltiples puntos
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el servicio MCP con la configuración de OSRM.
        
        Args:
            config: Configuración opcional que sobreescribe la configuración por defecto
        """
        self.config = config or OSRM_CONFIG
        self.base_url = self.config["base_url"]
        self.profile = self.config["profile"]
        self.timeout = self.config["timeout"]
    
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
            "calculate_distance": self.calculate_distance,
            "calculate_route": self.calculate_route,
            "calculate_distance_matrix": self.calculate_distance_matrix,
            "nearest_road": self.find_nearest_road,
        }
        
        if action not in action_handlers:
            return {
                "error": f"Acción no soportada: {action}",
                "supported_actions": list(action_handlers.keys())
            }
        
        return action_handlers[action](context)
    
    def calculate_distance(self, context: Dict) -> Dict:
        """
        Calcula la distancia óptima por carretera entre dos puntos.
        
        Args:
            context: Diccionario con:
                - origin: coordenadas [lon, lat] del origen
                - destination: coordenadas [lon, lat] del destino
                - profile (opcional): perfil de ruta (default: "car")
        
        Returns:
            Diccionario con:
                - distance: distancia en kilómetros
                - duration: duración estimada en segundos
                - status: estado del cálculo
                - error: mensaje de error (si ocurre)
        """
        try:
            # Validar datos de entrada
            origin = context.get("origin")
            destination = context.get("destination")
            
            if not origin or not destination:
                return {"error": "Se requieren coordenadas de origen y destino"}
            
            # Asegurarse de que las coordenadas estén en formato [lon, lat] para OSRM
            origin_formatted = self._format_coordinates(origin)
            destination_formatted = self._format_coordinates(destination)
            
            # Construir URL para la API de OSRM
            profile = context.get("profile", self.profile)
            url = f"{self.base_url}/route/v1/{profile}/{origin_formatted};{destination_formatted}"
            
            params = {
                "overview": "false",  # No necesitamos la geometría completa
                "alternatives": "false",
                "steps": "false"
            }
            
            # Realizar la solicitud a la API de OSRM
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data["code"] != "Ok":
                return {
                    "status": "error",
                    "error": f"Error en el cálculo de ruta: {data['message']}",
                    "raw_response": data
                }
            
            # Extraer datos relevantes de la respuesta
            route = data["routes"][0]
            distance_km = route["distance"] / 1000  # Convertir metros a kilómetros
            duration_sec = route["duration"]
            
            return {
                "status": "success",
                "distance": round(distance_km, 2),  # Redondear a 2 decimales
                "duration": round(duration_sec),
                "origin": origin,
                "destination": destination
            }
            
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": f"Error de comunicación con OSRM: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error en el cálculo de distancia: {str(e)}"
            }
    
    def calculate_route(self, context: Dict) -> Dict:
        """
        Calcula una ruta completa entre dos puntos, incluyendo geometría.
        
        Args:
            context: Diccionario con:
                - origin: coordenadas [lon, lat] del origen
                - destination: coordenadas [lon, lat] del destino
                - waypoints (opcional): lista de coordenadas intermedias
                - profile (opcional): perfil de ruta (default: "car")
                - steps (opcional): incluir pasos de navegación
        
        Returns:
            Diccionario con datos de la ruta, incluyendo geometría y pasos
        """
        try:
            # Validar datos de entrada
            origin = context.get("origin")
            destination = context.get("destination")
            
            if not origin or not destination:
                return {"error": "Se requieren coordenadas de origen y destino"}
            
            # Formatear coordenadas y waypoints
            waypoints = context.get("waypoints", [])
            coords = [origin] + waypoints + [destination]
            coords_str = ";".join([self._format_coordinates(coord) for coord in coords])
            
            # Construir URL para la API de OSRM
            profile = context.get("profile", self.profile)
            url = f"{self.base_url}/route/v1/{profile}/{coords_str}"
            
            params = {
                "overview": "full",  # Incluir geometría completa
                "alternatives": "false",
                "steps": "true" if context.get("steps", False) else "false",
                "geometries": "geojson"  # Formato geojson para la geometría
            }
            
            # Realizar la solicitud a la API de OSRM
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data["code"] != "Ok":
                return {
                    "status": "error",
                    "error": f"Error en el cálculo de ruta: {data['message']}",
                    "raw_response": data
                }
            
            # Extraer datos relevantes de la respuesta
            route = data["routes"][0]
            
            result = {
                "status": "success",
                "distance": round(route["distance"] / 1000, 2),  # km
                "duration": round(route["duration"] / 60, 2),   # minutos
                "geometry": route["geometry"],
                "waypoints": data["waypoints"]
            }
            
            # Incluir pasos detallados si se solicitaron
            if context.get("steps", False):
                result["steps"] = route["legs"]
            
            return result
            
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": f"Error de comunicación con OSRM: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error en el cálculo de ruta: {str(e)}"
            }
    
    def calculate_distance_matrix(self, context: Dict) -> Dict:
        """
        Calcula una matriz de distancias entre múltiples puntos.
        
        Args:
            context: Diccionario con:
                - sources: lista de coordenadas [lon, lat] de orígenes
                - destinations: lista de coordenadas [lon, lat] de destinos
                - profile (opcional): perfil de ruta (default: "car")
        
        Returns:
            Matriz de distancias y duraciones entre todos los puntos
        """
        try:
            # Validar datos de entrada
            sources = context.get("sources", [])
            destinations = context.get("destinations", [])
            
            if not sources or not destinations:
                return {"error": "Se requieren coordenadas de orígenes y destinos"}
            
            # Formatear coordenadas
            sources_str = ";".join([self._format_coordinates(coord) for coord in sources])
            destinations_str = ";".join([self._format_coordinates(coord) for coord in destinations])
            
            # Construir URL para la API de OSRM (table endpoint)
            profile = context.get("profile", self.profile)
            url = f"{self.base_url}/table/v1/{profile}/{sources_str};{destinations_str}"
            
            params = {
                "sources": ";".join([str(i) for i in range(len(sources))]),
                "destinations": ";".join([str(i + len(sources)) for i in range(len(destinations))])
            }
            
            # Realizar la solicitud a la API de OSRM
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data["code"] != "Ok":
                return {
                    "status": "error",
                    "error": f"Error en el cálculo de matriz: {data.get('message', 'Error desconocido')}",
                    "raw_response": data
                }
            
            # Procesar la matriz de duración a un formato más útil
            matrix = []
            durations = data["durations"]
            
            for i, source in enumerate(sources):
                row = []
                for j, dest in enumerate(destinations):
                    duration = durations[i][j]
                    # Estimamos distancia basada en duración y velocidad promedio (80 km/h)
                    # Este es un cálculo aproximado, OSRM no devuelve distancias en matriz
                    distance_km = (duration / 3600) * 80
                    
                    row.append({
                        "from": source,
                        "to": dest,
                        "distance": round(distance_km, 2),
                        "duration": round(duration / 60, 2)  # minutos
                    })
                matrix.append(row)
            
            return {
                "status": "success",
                "matrix": matrix,
                "sources": sources,
                "destinations": destinations
            }
            
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": f"Error de comunicación con OSRM: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error en el cálculo de matriz: {str(e)}"
            }
    
    def find_nearest_road(self, context: Dict) -> Dict:
        """
        Encuentra el punto más cercano en la red vial para unas coordenadas.
        Útil para "snap" de coordenadas a rutas válidas.
        
        Args:
            context: Diccionario con:
                - coordinates: coordenadas [lon, lat] para ajustar
                - profile (opcional): perfil de ruta (default: "car")
        
        Returns:
            Coordenadas ajustadas a la red vial más cercana
        """
        try:
            # Validar datos de entrada
            coordinates = context.get("coordinates")
            
            if not coordinates:
                return {"error": "Se requieren coordenadas"}
            
            # Formatear coordenadas
            coordinates_str = self._format_coordinates(coordinates)
            
            # Construir URL para la API de OSRM (nearest endpoint)
            profile = context.get("profile", self.profile)
            url = f"{self.base_url}/nearest/v1/{profile}/{coordinates_str}"
            
            params = {
                "number": 1  # Solo queremos el punto más cercano
            }
            
            # Realizar la solicitud a la API de OSRM
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data["code"] != "Ok":
                return {
                    "status": "error",
                    "error": f"Error al encontrar el punto más cercano: {data.get('message', 'Error desconocido')}",
                    "raw_response": data
                }
            
            # Extraer datos relevantes de la respuesta
            waypoint = data["waypoints"][0]
            nearest_point = waypoint["location"]
            distance = waypoint["distance"]
            
            return {
                "status": "success",
                "original": coordinates,
                "nearest": nearest_point,
                "distance": round(distance, 2),  # metros
                "name": waypoint.get("name", "")
            }
            
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": f"Error de comunicación con OSRM: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error al encontrar el punto más cercano: {str(e)}"
            }
    
    def _format_coordinates(self, coordinates: List[float]) -> str:
        """
        Formatea coordenadas para la API de OSRM.
        OSRM espera coordenadas en formato "lon,lat" (GeoJSON).
        
        Args:
            coordinates: Lista [lon, lat] o [lat, lon] según formato.
            
        Returns:
            String con coordenadas en formato "lon,lat"
        """
        # Si las coordenadas están en formato [lat, lon] (común en muchas API)
        # necesitamos invertirlas para OSRM que espera [lon, lat]
        if len(coordinates) == 2:
            # Verificamos si están en formato lat,lon (común)
            if coordinates[0] >= -90 and coordinates[0] <= 90 and \
               coordinates[1] >= -180 and coordinates[1] <= 180:
                # Están en formato lat,lon, invertimos
                return f"{coordinates[1]},{coordinates[0]}"
            else:
                # Asumimos que ya están en formato lon,lat
                return f"{coordinates[0]},{coordinates[1]}"
        else:
            # Formato inválido
            raise ValueError(f"Formato de coordenadas inválido: {coordinates}. Se esperaba [lon, lat] o [lat, lon]")


# Ejemplo de uso como servidor MCP
if __name__ == "__main__":
    import sys
    import argparse
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    osrm_mcp = OSRMRouteMCP()
    
    @app.route('/mcp/osrm', methods=['POST'])
    def handle_mcp_request():
        """Endpoint para recibir solicitudes MCP."""
        try:
            data = request.json
            action = data.get('action')
            context = data.get('context', {})
            
            if not action:
                return jsonify({"error": "Se requiere una acción"}), 400
                
            result = osrm_mcp.handle_request(action, context)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": f"Error: {str(e)}"}), 500
    
    parser = argparse.ArgumentParser(description='Servidor MCP para cálculo de rutas con OSRM')
    parser.add_argument('--host', default='0.0.0.0', help='Host para el servidor Flask')
    parser.add_argument('--port', type=int, default=5001, help='Puerto para el servidor Flask')
    parser.add_argument('--debug', action='store_true', help='Ejecutar en modo debug')
    
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=args.debug)