"""
Endpoints de API para cálculo de rutas y costos.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Tuple, Optional, Union
import base64

from utils.route_calculator import RouteCalculator
from utils.cost_calculator import CostCalculator
from utils.visualization import VisualizationGenerator
from utils.report_generator import ReportGenerator
from config.default import (
    COORDENADAS_TIMBUES,
    COORDENADAS_LIMA
)

router = APIRouter()

# Modelos Pydantic para la API
class RouteRequest(BaseModel):
    """Modelo para solicitud de cálculo de ruta."""
    origen_lat: float
    origen_lon: float
    origen_nombre: str
    toneladas: float
    es_contenedor: bool = False
    contenedores: int = 0

class RouteResponse(BaseModel):
    """Modelo para respuesta de cálculo de ruta."""
    status: str
    rutas: Optional[Dict] = None
    costos: Optional[Dict] = None
    comparacion: Optional[Dict] = None
    graficos: Optional[Dict] = None
    mensaje: Optional[str] = None

# Instanciar las clases de utilidades
route_calculator = RouteCalculator()
cost_calculator = CostCalculator()
visualization_generator = VisualizationGenerator()
report_generator = ReportGenerator()

@router.post("/calcular", response_model=RouteResponse)
async def calcular_rutas_costos(request: RouteRequest):
    """
    Calcular rutas y costos para exportación.
    
    Args:
        request: Datos de origen y carga para el cálculo.
        
    Returns:
        Resultados del cálculo incluyendo rutas, costos y visualizaciones.
    """
    try:
        # Coordenadas de origen (longitud, latitud)
        origen = (request.origen_lon, request.origen_lat)
        
        # Calcular rutas a los puertos
        ruta_timbues = route_calculator.get_route(origen, COORDENADAS_TIMBUES)
        ruta_lima = route_calculator.get_route(origen, COORDENADAS_LIMA)
        
        # Verificar si las rutas se calcularon correctamente
        if ruta_timbues["status"] != "success" or ruta_lima["status"] != "success":
            return RouteResponse(
                status="error",
                mensaje="Error al calcular una o ambas rutas"
            )
        
        # Calcular costos para cada puerto
        resultado_timbues = cost_calculator.calcular_costo_total_exportacion(
            'timbues',
            ruta_timbues["distance"],
            request.toneladas,
            request.es_contenedor,
            request.contenedores
        )
        
        resultado_lima = cost_calculator.calcular_costo_total_exportacion(
            'lima',
            ruta_lima["distance"],
            request.toneladas,
            request.es_contenedor,
            request.contenedores
        )
        
        # Comparar costos entre puertos
        resultados_comparacion = cost_calculator.comparar_costos_puertos(
            ruta_timbues["distance"],
            ruta_lima["distance"],
            request.toneladas,
            request.es_contenedor,
            request.contenedores
        )
        
        # Generar visualizaciones
        grafico_comparacion = visualization_generator.generar_grafico_comparacion_costos(
            resultados_comparacion
        )
        
        grafico_desglose_timbues = visualization_generator.generar_grafico_desglose_costos(
            resultado_timbues
        )
        
        grafico_desglose_lima = visualization_generator.generar_grafico_desglose_costos(
            resultado_lima
        )
        
        mapa_rutas = visualization_generator.generar_mapa_rutas(
            origen,
            request.origen_nombre,
            ruta_timbues,
            ruta_lima,
            resultados_comparacion
        )
        
        # Crear respuesta
        return RouteResponse(
            status="success",
            rutas={
                "timbues": ruta_timbues,
                "lima": ruta_lima
            },
            costos={
                "timbues": resultado_timbues,
                "lima": resultado_lima,
                "comparacion": resultados_comparacion["comparacion"]
            },
            graficos={
                "comparacion": grafico_comparacion.get("imagen"),
                "desglose_timbues": grafico_desglose_timbues.get("imagen"),
                "desglose_lima": grafico_desglose_lima.get("imagen"),
                "mapa": mapa_rutas.get("mapa_html")
            }
        )
        
    except Exception as e:
        return RouteResponse(
            status="error",
            mensaje=f"Error en el cálculo: {str(e)}"
        )

@router.post("/reporte")
async def generar_reporte_pdf(request: RouteRequest):
    """
    Generar un reporte PDF completo de análisis.
    
    Args:
        request: Datos de origen y carga para el cálculo.
        
    Returns:
        Archivo PDF con el reporte completo.
    """
    try:
        # Coordenadas de origen (longitud, latitud)
        origen = (request.origen_lon, request.origen_lat)
        
        # Calcular rutas a los puertos
        ruta_timbues = route_calculator.get_route(origen, COORDENADAS_TIMBUES)
        ruta_lima = route_calculator.get_route(origen, COORDENADAS_LIMA)
        
        # Calcular costos para cada puerto
        resultado_timbues = cost_calculator.calcular_costo_total_exportacion(
            'timbues',
            ruta_timbues["distance"],
            request.toneladas,
            request.es_contenedor,
            request.contenedores
        )
        
        resultado_lima = cost_calculator.calcular_costo_total_exportacion(
            'lima',
            ruta_lima["distance"],
            request.toneladas,
            request.es_contenedor,
            request.contenedores
        )
        
        # Comparar costos entre puertos
        resultados_comparacion = cost_calculator.comparar_costos_puertos(
            ruta_timbues["distance"],
            ruta_lima["distance"],
            request.toneladas,
            request.es_contenedor,
            request.contenedores
        )
        
        # Generar visualizaciones
        grafico_comparacion = visualization_generator.generar_grafico_comparacion_costos(
            resultados_comparacion
        )
        
        grafico_desglose_timbues = visualization_generator.generar_grafico_desglose_costos(
            resultado_timbues
        )
        
        grafico_desglose_lima = visualization_generator.generar_grafico_desglose_costos(
            resultado_lima
        )
        
        mapa_rutas = visualization_generator.generar_mapa_rutas(
            origen,
            request.origen_nombre,
            ruta_timbues,
            ruta_lima,
            resultados_comparacion
        )
        
        # Imágenes para el reporte
        imagenes = {
            "comparacion": grafico_comparacion.get("imagen"),
            "desglose_timbues": grafico_desglose_timbues.get("imagen"),
            "desglose_lima": grafico_desglose_lima.get("imagen"),
            "mapa_html": mapa_rutas.get("mapa_html")
        }
        
        # Generar el reporte
        reporte = report_generator.generar_reporte_comparacion(
            request.origen_nombre,
            resultado_timbues,
            resultado_lima,
            resultados_comparacion,
            ruta_timbues,
            ruta_lima,
            imagenes
        )
        
        if reporte["status"] != "success":
            raise HTTPException(status_code=500, detail=reporte.get("message", "Error al generar el reporte"))
        
        # Codificar el PDF en base64 para la respuesta
        pdf_base64 = base64.b64encode(reporte["pdf"]).decode('utf-8')
        
        return {
            "status": "success",
            "pdf_base64": pdf_base64,
            "filename": f"reporte_{request.origen_nombre.replace(' ', '_')}.pdf"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el reporte: {str(e)}")