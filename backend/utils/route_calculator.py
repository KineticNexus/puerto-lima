"""
Utilidad para cálculo de rutas utilizando OSRM.

Este módulo contiene funciones para calcular distancias y rutas entre puntos 
geográficos utilizando el servicio OSRM (Open Source Routing Machine).
"""

import requests
import logging
import polyline
import json
from typing import Dict, List, Tuple, Optional, Union
from config.default import OSRM_API_URL

# Configurar logging
logger = logging.getLogger(__name__)

class RouteCalculator:
    """Clase para calcular rutas y distancias usando OSRM."""
    
    def __init__(self, api_url: str = OSRM_API_URL):
        """Inicializar calculador de rutas con URL de API OSRM.
        
        Args:
            api_url: URL base de la API OSRM. Por defecto usa la configuración global.
        """
        self.api_url = api_url
    
    def get_distance(self, 
                    origin: Tuple[float, float], 
                    destination: Tuple[float, float],
                    factor_correccion: float = 1.0) -> Dict:
        """Obtener distancia y tiempo entre dos puntos.
        
        Args:
            origin: Tupla de coordenadas (longitud, latitud) de origen.
            destination: Tupla de coordenadas (longitud, latitud) de destino.
            factor_correccion: Factor de corrección para la distancia.
            
        Returns:
            Diccionario con distancia (km), tiempo (min) y estado de la consulta.
        """
        try:
            # Formatear coordenadas para la API
            coords = f"{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
            url = f"{self.api_url}/route/v1/driving/{coords}"
            
            response = requests.get(url, params={"overview": "false"})
            data = response.json()
            
            if data["code"] != "Ok":
                logger.error(f"Error en cálculo de ruta: {data['message'] if 'message' in data else 'Error desconocido'}")
                return {
                    "status": "error",
                    "message": data.get("message", "Error desconocido en OSRM"),
                    "distance": None,
                    "duration": None
                }
            
            # Obtener la primera ruta (OSRM puede devolver alternativas)
            route = data["routes"][0]
            
            # Aplicar factor de corrección a la distancia
            distance_km = (route["distance"] / 1000) * factor_correccion
            duration_min = route["duration"] / 60
            
            return {
                "status": "success",
                "distance": round(distance_km, 2),  # Distancia en km
                "duration": round(duration_min, 2),  # Tiempo en minutos
                "raw_distance": route["distance"],  # Distancia original en metros
                "raw_duration": route["duration"]   # Tiempo original en segundos
            }
            
        except requests.RequestException as e:
            logger.error(f"Error de conexión a OSRM: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión a OSRM: {str(e)}",
                "distance": None,
                "duration": None
            }
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error al procesar respuesta de OSRM: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al procesar respuesta de OSRM: {str(e)}",
                "distance": None,
                "duration": None
            }
    
    def get_route(self, 
                 origin: Tuple[float, float], 
                 destination: Tuple[float, float]) -> Dict:
        """Obtener ruta completa entre dos puntos con geometría.
        
        Args:
            origin: Tupla de coordenadas (longitud, latitud) de origen.
            destination: Tupla de coordenadas (longitud, latitud) de destino.
            
        Returns:
            Diccionario con distancia, tiempo, geometría y estado de la consulta.
        """
        try:
            # Formatear coordenadas para la API
            coords = f"{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
            url = f"{self.api_url}/route/v1/driving/{coords}"
            
            response = requests.get(url, params={"overview": "full", "geometries": "polyline"})
            data = response.json()
            
            if data["code"] != "Ok":
                logger.error(f"Error en cálculo de ruta: {data['message'] if 'message' in data else 'Error desconocido'}")
                return {
                    "status": "error",
                    "message": data.get("message", "Error desconocido en OSRM"),
                    "distance": None,
                    "duration": None,
                    "geometry": None
                }
            
            # Obtener la primera ruta
            route = data["routes"][0]
            
            # Decodificar la geometría polyline
            route_geometry = polyline.decode(route["geometry"])
            
            return {
                "status": "success",
                "distance": round(route["distance"] / 1000, 2),  # Distancia en km
                "duration": round(route["duration"] / 60, 2),  # Tiempo en minutos
                "geometry": route_geometry,  # Lista de coordenadas [lat, lon]
                "raw_distance": route["distance"],  # Distancia original en metros
                "raw_duration": route["duration"]   # Tiempo original en segundos
            }
            
        except requests.RequestException as e:
            logger.error(f"Error de conexión a OSRM: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión a OSRM: {str(e)}",
                "distance": None,
                "duration": None,
                "geometry": None
            }
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error al procesar respuesta de OSRM: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al procesar respuesta de OSRM: {str(e)}",
                "distance": None,
                "duration": None,
                "geometry": None
            }
        
    def get_matrix(self, 
                  points: List[Tuple[float, float]], 
                  factor_correccion: float = 1.0) -> Dict:
        """Obtener matriz de distancias entre múltiples puntos.
        
        Args:
            points: Lista de tuplas de coordenadas (longitud, latitud).
            factor_correccion: Factor de corrección para las distancias.
            
        Returns:
            Diccionario con matrices de distancias y tiempos.
        """
        if len(points) < 2:
            return {
                "status": "error",
                "message": "Se requieren al menos 2 puntos para calcular una matriz",
                "distances": None,
                "durations": None
            }
            
        try:
            # Formatear coordenadas para la API
            coords = ";".join([f"{lon},{lat}" for lon, lat in points])
            url = f"{self.api_url}/table/v1/driving/{coords}"
            
            response = requests.get(url, params={"annotations": "distance,duration"})
            data = response.json()
            
            if data["code"] != "Ok":
                logger.error(f"Error en cálculo de matriz: {data['message'] if 'message' in data else 'Error desconocido'}")
                return {
                    "status": "error",
                    "message": data.get("message", "Error desconocido en OSRM"),
                    "distances": None,
                    "durations": None
                }
            
            # Aplicar factor de corrección a las distancias
            distances = [[d / 1000 * factor_correccion for d in row] for row in data["distances"]]
            durations = [[d / 60 for d in row] for row in data["durations"]]
            
            return {
                "status": "success",
                "distances": distances,  # Matriz de distancias en km
                "durations": durations,  # Matriz de tiempos en minutos
                "raw_distances": data["distances"],  # Matriz original en metros
                "raw_durations": data["durations"]   # Matriz original en segundos
            }
            
        except requests.RequestException as e:
            logger.error(f"Error de conexión a OSRM: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión a OSRM: {str(e)}",
                "distances": None,
                "durations": None
            }
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error al procesar respuesta de OSRM: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al procesar respuesta de OSRM: {str(e)}",
                "distances": None,
                "durations": None
            }