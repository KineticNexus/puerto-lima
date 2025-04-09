"""
Utilidad para cálculo de costos de exportación.

Este módulo contiene funciones para calcular los costos asociados a la exportación
de productos utilizando diferentes puertos y rutas.
"""

import logging
from typing import Dict, List, Tuple, Optional, Union
from config.default import (
    COSTOS_FIJOS_TIMBUES,
    COSTOS_FIJOS_LIMA,
    TARIFA_FLETE_MARITIMO_TIMBUES,
    TARIFA_FLETE_MARITIMO_LIMA,
    TARIFA_FLETE_TERRESTRE_BASE,
    FACTOR_CORRECCION_TIMBUES,
    FACTOR_CORRECCION_LIMA
)

# Configurar logging
logger = logging.getLogger(__name__)

class CostCalculator:
    """Clase para calcular costos de exportación vía diferentes puertos."""
    
    def __init__(self, 
                costos_fijos_timbues: Dict[str, float] = COSTOS_FIJOS_TIMBUES,
                costos_fijos_lima: Dict[str, float] = COSTOS_FIJOS_LIMA,
                tarifa_flete_maritimo_timbues: float = TARIFA_FLETE_MARITIMO_TIMBUES,
                tarifa_flete_maritimo_lima: float = TARIFA_FLETE_MARITIMO_LIMA,
                tarifa_flete_terrestre_base: float = TARIFA_FLETE_TERRESTRE_BASE,
                factor_correccion_timbues: float = FACTOR_CORRECCION_TIMBUES,
                factor_correccion_lima: float = FACTOR_CORRECCION_LIMA):
        """Inicializar calculador de costos.
        
        Args:
            costos_fijos_timbues: Diccionario con costos fijos en puerto Timbúes.
            costos_fijos_lima: Diccionario con costos fijos en puerto Lima.
            tarifa_flete_maritimo_timbues: Tarifa de flete marítimo desde Timbúes (USD/ton).
            tarifa_flete_maritimo_lima: Tarifa de flete marítimo desde Lima (USD/ton).
            tarifa_flete_terrestre_base: Tarifa base para flete terrestre (USD/ton·km).
            factor_correccion_timbues: Factor de corrección para rutas a Timbúes.
            factor_correccion_lima: Factor de corrección para rutas a Lima.
        """
        self.costos_fijos_timbues = costos_fijos_timbues
        self.costos_fijos_lima = costos_fijos_lima
        self.tarifa_flete_maritimo_timbues = tarifa_flete_maritimo_timbues
        self.tarifa_flete_maritimo_lima = tarifa_flete_maritimo_lima
        self.tarifa_flete_terrestre_base = tarifa_flete_terrestre_base
        self.factor_correccion_timbues = factor_correccion_timbues
        self.factor_correccion_lima = factor_correccion_lima
    
    def calcular_costo_total_exportacion(self, 
                                        puerto: str,
                                        distancia_terrestre: float,
                                        toneladas: float,
                                        es_contenedor: bool = False,
                                        contenedores: int = 0) -> Dict:
        """Calcular costo total de exportación vía un puerto específico.
        
        Args:
            puerto: Puerto de exportación ('timbues' o 'lima').
            distancia_terrestre: Distancia terrestre en km.
            toneladas: Cantidad de producto en toneladas.
            es_contenedor: Si es True, se calcula por contenedor en lugar de granel.
            contenedores: Número de contenedores (solo si es_contenedor=True).
            
        Returns:
            Diccionario con desglose de costos y costo total.
        """
        if puerto.lower() not in ['timbues', 'lima']:
            return {
                "status": "error",
                "message": "Puerto no válido. Opciones: 'timbues' o 'lima'",
                "costo_total": None
            }
        
        try:
            # Seleccionar parámetros según puerto
            if puerto.lower() == 'timbues':
                costos_fijos = self.costos_fijos_timbues
                tarifa_flete_maritimo = self.tarifa_flete_maritimo_timbues
                factor_correccion = self.factor_correccion_timbues
            else:  # 'lima'
                costos_fijos = self.costos_fijos_lima
                tarifa_flete_maritimo = self.tarifa_flete_maritimo_lima
                factor_correccion = self.factor_correccion_lima
            
            # Calcular costo de flete terrestre
            distancia_ajustada = distancia_terrestre * factor_correccion
            costo_flete_terrestre = distancia_ajustada * self.tarifa_flete_terrestre_base * toneladas
            
            # Calcular costo de flete marítimo
            costo_flete_maritimo = tarifa_flete_maritimo * toneladas
            
            # Calcular costos fijos totales
            if es_contenedor:
                # Para carga en contenedores
                costo_fijo_total = sum([
                    costos_fijos.get(concepto, 0) * contenedores 
                    for concepto in costos_fijos
                ])
            else:
                # Para carga a granel
                costo_fijo_total = sum([
                    costos_fijos.get(concepto, 0) 
                    for concepto in costos_fijos
                ])
            
            # Calcular costo total
            costo_total = costo_flete_terrestre + costo_flete_maritimo + costo_fijo_total
            
            # Construir respuesta con desglose
            return {
                "status": "success",
                "puerto": puerto,
                "toneladas": toneladas,
                "distancia_terrestre": distancia_terrestre,
                "distancia_ajustada": distancia_ajustada,
                "desglose": {
                    "flete_terrestre": round(costo_flete_terrestre, 2),
                    "flete_maritimo": round(costo_flete_maritimo, 2),
                    "costos_fijos": round(costo_fijo_total, 2),
                },
                "costo_total": round(costo_total, 2),
                "costo_unitario": round(costo_total / toneladas, 2)
            }
            
        except Exception as e:
            logger.error(f"Error en cálculo de costos: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en cálculo de costos: {str(e)}",
                "costo_total": None
            }
    
    def comparar_costos_puertos(self,
                              distancia_timbues: float,
                              distancia_lima: float,
                              toneladas: float,
                              es_contenedor: bool = False,
                              contenedores: int = 0) -> Dict:
        """Comparar costos de exportación entre puertos Timbúes y Lima.
        
        Args:
            distancia_timbues: Distancia terrestre a Timbúes en km.
            distancia_lima: Distancia terrestre a Lima en km.
            toneladas: Cantidad de producto en toneladas.
            es_contenedor: Si es True, se calcula por contenedor en lugar de granel.
            contenedores: Número de contenedores (solo si es_contenedor=True).
            
        Returns:
            Diccionario con resultados de ambos puertos y comparación.
        """
        try:
            # Calcular costos para cada puerto
            resultado_timbues = self.calcular_costo_total_exportacion(
                'timbues', distancia_timbues, toneladas, es_contenedor, contenedores
            )
            
            resultado_lima = self.calcular_costo_total_exportacion(
                'lima', distancia_lima, toneladas, es_contenedor, contenedores
            )
            
            # Verificar si ambos cálculos fueron exitosos
            if resultado_timbues["status"] != "success" or resultado_lima["status"] != "success":
                return {
                    "status": "error",
                    "message": "Error en el cálculo de costos para uno o ambos puertos",
                    "timbues": resultado_timbues,
                    "lima": resultado_lima
                }
            
            # Determinar cuál puerto es más conveniente
            diferencia = resultado_lima["costo_total"] - resultado_timbues["costo_total"]
            porcentaje_diferencia = (abs(diferencia) / min(
                resultado_timbues["costo_total"], 
                resultado_lima["costo_total"]
            )) * 100
            
            puerto_optimo = "timbues" if diferencia > 0 else "lima"
            
            return {
                "status": "success",
                "timbues": resultado_timbues,
                "lima": resultado_lima,
                "comparacion": {
                    "diferencia_absoluta": round(abs(diferencia), 2),
                    "diferencia_porcentual": round(porcentaje_diferencia, 2),
                    "puerto_optimo": puerto_optimo,
                    "ahorro": round(abs(diferencia), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error en comparación de costos: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en comparación de costos: {str(e)}",
                "timbues": None,
                "lima": None
            }
    
    def calcular_punto_equilibrio(self,
                                distancia_lima: float,
                                toneladas: float,
                                es_contenedor: bool = False,
                                contenedores: int = 0,
                                precision: float = 0.1) -> Dict:
        """Calcular punto de equilibrio entre ambos puertos.
        
        Encuentra la distancia a Timbúes donde el costo es igual al de Lima.
        
        Args:
            distancia_lima: Distancia terrestre a Lima en km.
            toneladas: Cantidad de producto en toneladas.
            es_contenedor: Si es True, se calcula por contenedor.
            contenedores: Número de contenedores (solo si es_contenedor=True).
            precision: Precisión deseada en km.
            
        Returns:
            Diccionario con punto de equilibrio y detalles.
        """
        try:
            # Método de bisección para encontrar el punto de equilibrio
            min_dist = 0.0
            max_dist = 2000.0  # Distancia máxima razonable en Argentina
            
            # Verificar si Lima es más barato incluso a distancia cero a Timbúes
            comparacion_min = self.comparar_costos_puertos(
                min_dist, distancia_lima, toneladas, es_contenedor, contenedores
            )
            
            if comparacion_min["status"] != "success":
                return {
                    "status": "error",
                    "message": "Error en el cálculo inicial de comparación",
                    "punto_equilibrio": None
                }
            
            if comparacion_min["comparacion"]["puerto_optimo"] == "lima":
                return {
                    "status": "success",
                    "mensaje": "El puerto de Lima es siempre más conveniente para este caso",
                    "punto_equilibrio": None,
                    "comparacion_referencia": comparacion_min
                }
            
            # Verificar si Timbúes es más barato incluso a distancia máxima
            comparacion_max = self.comparar_costos_puertos(
                max_dist, distancia_lima, toneladas, es_contenedor, contenedores
            )
            
            if comparacion_max["comparacion"]["puerto_optimo"] == "timbues":
                return {
                    "status": "success",
                    "mensaje": "El puerto de Timbúes es siempre más conveniente para este caso",
                    "punto_equilibrio": None,
                    "comparacion_referencia": comparacion_max
                }
            
            # Buscar el punto de equilibrio mediante bisección
            while (max_dist - min_dist) > precision:
                mid_dist = (min_dist + max_dist) / 2
                
                comparacion = self.comparar_costos_puertos(
                    mid_dist, distancia_lima, toneladas, es_contenedor, contenedores
                )
                
                if comparacion["status"] != "success":
                    return {
                        "status": "error",
                        "message": "Error en el cálculo de comparación durante la bisección",
                        "punto_equilibrio": None
                    }
                
                # Ajustar los límites según el resultado
                if comparacion["comparacion"]["puerto_optimo"] == "timbues":
                    min_dist = mid_dist
                else:
                    max_dist = mid_dist
            
            # Calcular el punto final con precisión aceptable
            punto_equilibrio = (min_dist + max_dist) / 2
            
            # Calcular costos en el punto de equilibrio
            comparacion_equilibrio = self.comparar_costos_puertos(
                punto_equilibrio, distancia_lima, toneladas, es_contenedor, contenedores
            )
            
            return {
                "status": "success",
                "punto_equilibrio": round(punto_equilibrio, 2),
                "distancia_lima": distancia_lima,
                "toneladas": toneladas,
                "es_contenedor": es_contenedor,
                "contenedores": contenedores if es_contenedor else None,
                "comparacion_equilibrio": comparacion_equilibrio
            }
            
        except Exception as e:
            logger.error(f"Error en cálculo de punto de equilibrio: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en cálculo de punto de equilibrio: {str(e)}",
                "punto_equilibrio": None
            }