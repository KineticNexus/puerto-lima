"""
Utilidad para generación de reportes de análisis.

Este módulo contiene funciones para generar reportes detallados de análisis
de costos y rutas de exportación.
"""

import io
import json
import logging
import datetime
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from weasyprint import HTML, CSS
from jinja2 import Template

# Configurar logging
logger = logging.getLogger(__name__)

class ReportGenerator:
    """Clase para generar reportes de análisis de exportación."""
    
    def __init__(self):
        """Inicializar generador de reportes."""
        self.today = datetime.datetime.now().strftime("%d/%m/%Y")
        self.report_template = self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Obtener plantilla HTML por defecto para reportes.
        
        Returns:
            String con plantilla HTML para el reporte.
        """
        return """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ titulo }}</title>
            <style>
                body {
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }
                .header h1 {
                    color: #2c3e50;
                    margin-bottom: 10px;
                }
                .header .date {
                    color: #7f8c8d;
                    font-size: 14px;
                }
                .content {
                    margin-bottom: 30px;
                }
                h2 {
                    color: #2980b9;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }
                h3 {
                    color: #3498db;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                table, th, td {
                    border: 1px solid #ddd;
                }
                th {
                    background-color: #f2f2f2;
                    padding: 10px;
                    text-align: left;
                }
                td {
                    padding: 8px;
                }
                .info-box {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 15px 0;
                }
                .result-box {
                    background-color: #e8f4f8;
                    border: 1px solid #d1e7f0;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 15px 0;
                }
                .result-box.highlight {
                    background-color: #d4edda;
                    border-color: #c3e6cb;
                }
                .img-container {
                    text-align: center;
                    margin: 20px 0;
                }
                .img-container img {
                    max-width: 100%;
                    height: auto;
                }
                .footer {
                    text-align: center;
                    font-size: 12px;
                    color: #7f8c8d;
                    margin-top: 30px;
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                }
                .page-break {
                    page-break-after: always;
                }
                @media print {
                    body {
                        padding: 0;
                    }
                    h2, h3 {
                        page-break-after: avoid;
                    }
                    .img-container {
                        page-break-inside: avoid;
                    }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ titulo }}</h1>
                <div class="date">Fecha: {{ fecha }}</div>
            </div>
            
            <div class="content">
                <h2>Resumen Ejecutivo</h2>
                <div class="info-box">
                    {{ resumen_ejecutivo }}
                </div>
                
                <h2>Parámetros del Análisis</h2>
                <table>
                    <tr>
                        <th>Parámetro</th>
                        <th>Valor</th>
                    </tr>
                    {% for param in parametros %}
                    <tr>
                        <td>{{ param.nombre }}</td>
                        <td>{{ param.valor }}</td>
                    </tr>
                    {% endfor %}
                </table>
                
                <h2>Análisis de Rutas</h2>
                <div class="info-box">
                    <p>{{ analisis_rutas.descripcion }}</p>
                    
                    <h3>Distancias</h3>
                    <table>
                        <tr>
                            <th>Ruta</th>
                            <th>Distancia (km)</th>
                            <th>Tiempo Estimado</th>
                        </tr>
                        {% for ruta in analisis_rutas.distancias %}
                        <tr>
                            <td>{{ ruta.nombre }}</td>
                            <td>{{ ruta.distancia }}</td>
                            <td>{{ ruta.tiempo }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    
                    {% if analisis_rutas.mapa %}
                    <div class="img-container">
                        <h3>Mapa de Rutas</h3>
                        {{ analisis_rutas.mapa|safe }}
                    </div>
                    {% endif %}
                </div>
                
                <div class="page-break"></div>
                
                <h2>Análisis de Costos</h2>
                <div class="info-box">
                    <p>{{ analisis_costos.descripcion }}</p>
                    
                    <h3>Detalle de Costos por Puerto</h3>
                    <table>
                        <tr>
                            <th>Concepto</th>
                            <th>Timbúes (USD)</th>
                            <th>Lima (USD)</th>
                        </tr>
                        {% for item in analisis_costos.detalles %}
                        <tr>
                            <td>{{ item.concepto }}</td>
                            <td>{{ item.timbues }}</td>
                            <td>{{ item.lima }}</td>
                        </tr>
                        {% endfor %}
                        <tr>
                            <th>Total</th>
                            <th>{{ analisis_costos.total_timbues }}</th>
                            <th>{{ analisis_costos.total_lima }}</th>
                        </tr>
                    </table>
                    
                    {% if analisis_costos.imagen_comparacion %}
                    <div class="img-container">
                        <h3>Comparación Gráfica de Costos</h3>
                        <img src="data:image/png;base64,{{ analisis_costos.imagen_comparacion }}" alt="Comparación de costos">
                    </div>
                    {% endif %}
                    
                    {% if analisis_costos.imagen_desglose_timbues %}
                    <div class="img-container">
                        <h3>Desglose de Costos - Timbúes</h3>
                        <img src="data:image/png;base64,{{ analisis_costos.imagen_desglose_timbues }}" alt="Desglose de costos Timbúes">
                    </div>
                    {% endif %}
                    
                    {% if analisis_costos.imagen_desglose_lima %}
                    <div class="img-container">
                        <h3>Desglose de Costos - Lima</h3>
                        <img src="data:image/png;base64,{{ analisis_costos.imagen_desglose_lima }}" alt="Desglose de costos Lima">
                    </div>
                    {% endif %}
                </div>
                
                <div class="page-break"></div>
                
                <h2>Conclusiones</h2>
                <div class="result-box {% if conclusiones.puerto_optimo %}highlight{% endif %}">
                    <h3>Puerto Óptimo: {{ conclusiones.puerto_optimo }}</h3>
                    <p>{{ conclusiones.justificacion }}</p>
                    
                    <h3>Resumen Comparativo</h3>
                    <table>
                        <tr>
                            <th>Métrica</th>
                            <th>Valor</th>
                        </tr>
                        {% for metrica in conclusiones.metricas %}
                        <tr>
                            <td>{{ metrica.nombre }}</td>
                            <td>{{ metrica.valor }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    
                    {% if conclusiones.recomendaciones %}
                    <h3>Recomendaciones</h3>
                    <ul>
                        {% for rec in conclusiones.recomendaciones %}
                        <li>{{ rec }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                
                {% if analisis_sensibilidad %}
                <h2>Análisis de Sensibilidad</h2>
                <div class="info-box">
                    <p>{{ analisis_sensibilidad.descripcion }}</p>
                    
                    {% for analisis in analisis_sensibilidad.analisis %}
                    <h3>{{ analisis.titulo }}</h3>
                    <p>{{ analisis.descripcion }}</p>
                    
                    {% if analisis.imagen %}
                    <div class="img-container">
                        <img src="data:image/png;base64,{{ analisis.imagen }}" alt="{{ analisis.titulo }}">
                    </div>
                    {% endif %}
                    
                    <div class="result-box">
                        <p>{{ analisis.conclusion }}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            
            <div class="footer">
                <p>Reporte generado automáticamente por el sistema de análisis de rutas de exportación.</p>
                <p>{{ fecha }} | Proyecto Puerto Lima</p>
            </div>
        </body>
        </html>
        """

    def generar_reporte_comparacion(self,
                                  origen: str,
                                  resultado_timbues: Dict,
                                  resultado_lima: Dict,
                                  resultados_comparacion: Dict,
                                  ruta_timbues: Optional[Dict] = None,
                                  ruta_lima: Optional[Dict] = None,
                                  imagenes: Optional[Dict] = None,
                                  analisis_sensibilidad: Optional[List[Dict]] = None) -> Dict:
        """Generar reporte completo de comparación entre puertos.
        
        Args:
            origen: Nombre del origen de la carga.
            resultado_timbues: Diccionario con resultados para puerto Timbúes.
            resultado_lima: Diccionario con resultados para puerto Lima.
            resultados_comparacion: Diccionario con resultados de comparación.
            ruta_timbues: Diccionario con datos de ruta a Timbúes.
            ruta_lima: Diccionario con datos de ruta a Lima.
            imagenes: Diccionario con imágenes base64 para el reporte.
            analisis_sensibilidad: Lista de diccionarios con análisis de sensibilidad.
            
        Returns:
            Diccionario con reporte PDF en base64 y metadatos.
        """
        try:
            if (resultado_timbues["status"] != "success" or 
                resultado_lima["status"] != "success" or
                resultados_comparacion["status"] != "success"):
                return {
                    "status": "error",
                    "message": "Los resultados proporcionados no son válidos",
                    "pdf": None
                }
            
            # Extraer datos para el reporte
            toneladas = resultado_timbues["toneladas"]
            distancia_timbues = resultado_timbues["distancia_terrestre"]
            distancia_lima = resultado_lima["distancia_terrestre"]
            
            puerto_optimo = resultados_comparacion["comparacion"]["puerto_optimo"].title()
            diferencia_absoluta = resultados_comparacion["comparacion"]["diferencia_absoluta"]
            diferencia_porcentual = resultados_comparacion["comparacion"]["diferencia_porcentual"]
            
            # Preparar parámetros del análisis
            parametros = [
                {"nombre": "Origen", "valor": origen},
                {"nombre": "Carga (toneladas)", "valor": f"{toneladas:,.2f}"},
                {"nombre": "Distancia a Timbúes (km)", "valor": f"{distancia_timbues:,.1f}"},
                {"nombre": "Distancia a Lima (km)", "valor": f"{distancia_lima:,.1f}"}
            ]
            
            # Preparar datos de rutas
            distancias_rutas = []
            if ruta_timbues and ruta_timbues["status"] == "success":
                distancias_rutas.append({
                    "nombre": f"Origen → Timbúes",
                    "distancia": f"{ruta_timbues['distance']:,.1f}",
                    "tiempo": f"{ruta_timbues['duration']:,.1f} min"
                })
                
            if ruta_lima and ruta_lima["status"] == "success":
                distancias_rutas.append({
                    "nombre": f"Origen → Lima",
                    "distancia": f"{ruta_lima['distance']:,.1f}",
                    "tiempo": f"{ruta_lima['duration']:,.1f} min"
                })
                
            if not distancias_rutas:
                distancias_rutas = [
                    {
                        "nombre": f"Origen → Timbúes",
                        "distancia": f"{distancia_timbues:,.1f}",
                        "tiempo": "No disponible"
                    },
                    {
                        "nombre": f"Origen → Lima",
                        "distancia": f"{distancia_lima:,.1f}",
                        "tiempo": "No disponible"
                    }
                ]
                
            # Preparar detalles de costos
            detalles_costos = [
                {
                    "concepto": "Flete Terrestre",
                    "timbues": f"${resultado_timbues['desglose']['flete_terrestre']:,.2f}",
                    "lima": f"${resultado_lima['desglose']['flete_terrestre']:,.2f}"
                },
                {
                    "concepto": "Flete Marítimo",
                    "timbues": f"${resultado_timbues['desglose']['flete_maritimo']:,.2f}",
                    "lima": f"${resultado_lima['desglose']['flete_maritimo']:,.2f}"
                },
                {
                    "concepto": "Costos Fijos",
                    "timbues": f"${resultado_timbues['desglose']['costos_fijos']:,.2f}",
                    "lima": f"${resultado_lima['desglose']['costos_fijos']:,.2f}"
                }
            ]
            
            # Preparar métricas de conclusiones
            metricas_conclusiones = [
                {
                    "nombre": "Costo Total Puerto Timbúes",
                    "valor": f"${resultado_timbues['costo_total']:,.2f}"
                },
                {
                    "nombre": "Costo Total Puerto Lima",
                    "valor": f"${resultado_lima['costo_total']:,.2f}"
                },
                {
                    "nombre": "Ahorro Absoluto",
                    "valor": f"${diferencia_absoluta:,.2f}"
                },
                {
                    "nombre": "Ahorro Porcentual",
                    "valor": f"{diferencia_porcentual:.1f}%"
                },
                {
                    "nombre": "Costo Unitario Puerto Óptimo",
                    "valor": f"${resultados_comparacion[puerto_optimo.lower()]['costo_unitario']:,.2f}/ton"
                }
            ]
            
            # Preparar recomendaciones
            recomendaciones = [
                f"Utilizar el puerto de {puerto_optimo} para esta operación de exportación.",
                f"El ahorro estimado es de ${diferencia_absoluta:,.2f} en comparación con la alternativa."
            ]
            
            # Verificar si la diferencia es significativa
            if diferencia_porcentual < 5:
                recomendaciones.append("La diferencia de costos es menor al 5%. "
                                     "Considerar otros factores logísticos o comerciales para la decisión final.")
            
            # Preparar resumen ejecutivo
            resumen_ejecutivo = f"""
            Este informe presenta un análisis comparativo de costos y rutas de exportación 
            desde {origen} utilizando dos puertos alternativos: Timbúes (Argentina) y Lima (Perú).
            
            El análisis se basa en una carga de {toneladas:,.2f} toneladas, con distancias terrestres 
            de {distancia_timbues:,.1f} km a Timbúes y {distancia_lima:,.1f} km a Lima.
            
            La conclusión principal es que el puerto de {puerto_optimo} representa la opción más 
            económica, con un ahorro estimado de ${diferencia_absoluta:,.2f} ({diferencia_porcentual:.1f}%) 
            en comparación con la alternativa.
            """
            
            # Preparar análisis de sensibilidad si existe
            datos_sensibilidad = None
            if analisis_sensibilidad:
                datos_sensibilidad = {
                    "descripcion": "Análisis del comportamiento de costos al variar parámetros clave.",
                    "analisis": analisis_sensibilidad
                }
            
            # Preparar datos para la plantilla
            template_data = {
                "titulo": f"Análisis de Exportación: {origen}",
                "fecha": self.today,
                "resumen_ejecutivo": resumen_ejecutivo,
                "parametros": parametros,
                "analisis_rutas": {
                    "descripcion": "Análisis de las distancias y tiempos estimados para cada ruta alternativa.",
                    "distancias": distancias_rutas,
                    "mapa": imagenes.get("mapa_html") if imagenes and "mapa_html" in imagenes else None
                },
                "analisis_costos": {
                    "descripcion": "Desglose y comparación de costos para cada alternativa de exportación.",
                    "detalles": detalles_costos,
                    "total_timbues": f"${resultado_timbues['costo_total']:,.2f}",
                    "total_lima": f"${resultado_lima['costo_total']:,.2f}",
                    "imagen_comparacion": imagenes.get("comparacion") if imagenes and "comparacion" in imagenes else None,
                    "imagen_desglose_timbues": imagenes.get("desglose_timbues") if imagenes and "desglose_timbues" in imagenes else None,
                    "imagen_desglose_lima": imagenes.get("desglose_lima") if imagenes and "desglose_lima" in imagenes else None
                },
                "conclusiones": {
                    "puerto_optimo": puerto_optimo,
                    "justificacion": f"El puerto de {puerto_optimo} ofrece un costo total de exportación menor, " + 
                                    f"con un ahorro de ${diferencia_absoluta:,.2f} ({diferencia_porcentual:.1f}%) " +
                                    f"en comparación con la alternativa.",
                    "metricas": metricas_conclusiones,
                    "recomendaciones": recomendaciones
                },
                "analisis_sensibilidad": datos_sensibilidad
            }
            
            # Renderizar plantilla
            template = Template(self.report_template)
            html_content = template.render(**template_data)
            
            # Convertir a PDF
            pdf_file = io.BytesIO()
            HTML(string=html_content).write_pdf(pdf_file)
            pdf_file.seek(0)
            
            return {
                "status": "success",
                "pdf": pdf_file.getvalue(),
                "html": html_content,
                "puerto_optimo": puerto_optimo,
                "ahorro": diferencia_absoluta,
                "ahorro_porcentual": diferencia_porcentual
            }
            
        except Exception as e:
            logger.error(f"Error al generar reporte de comparación: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al generar reporte de comparación: {str(e)}",
                "pdf": None
            }