"""
Utilidad para visualización de rutas y costos.

Este módulo contiene funciones para generar visualizaciones, gráficos y mapas
para representar las rutas y costos de exportación.
"""

import io
import base64
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.features import DivIcon
from typing import Dict, List, Tuple, Optional, Union
from config.default import (
    COORDENADAS_TIMBUES,
    COORDENADAS_LIMA,
    VISUALIZACION_COLORES_PRIMARIOS,
    VISUALIZACION_COLORES_SECUNDARIOS
)

# Configurar logging
logger = logging.getLogger(__name__)

class VisualizationGenerator:
    """Clase para generar visualizaciones de rutas y costos."""
    
    def __init__(self, 
                coords_timbues: Tuple[float, float] = COORDENADAS_TIMBUES,
                coords_lima: Tuple[float, float] = COORDENADAS_LIMA,
                colores_primarios: List[str] = VISUALIZACION_COLORES_PRIMARIOS,
                colores_secundarios: List[str] = VISUALIZACION_COLORES_SECUNDARIOS):
        """Inicializar generador de visualizaciones.
        
        Args:
            coords_timbues: Coordenadas (longitud, latitud) de puerto Timbúes.
            coords_lima: Coordenadas (longitud, latitud) de puerto Lima.
            colores_primarios: Lista de colores primarios para gráficos.
            colores_secundarios: Lista de colores secundarios para gráficos.
        """
        self.coords_timbues = coords_timbues
        self.coords_lima = coords_lima
        self.colores_primarios = colores_primarios
        self.colores_secundarios = colores_secundarios
    
    def generar_grafico_comparacion_costos(self, 
                                         resultados_comparacion: Dict) -> Dict:
        """Generar gráfico de barras comparando costos entre puertos.
        
        Args:
            resultados_comparacion: Diccionario con resultados de comparación de costos.
            
        Returns:
            Diccionario con imagen base64 del gráfico y metadatos.
        """
        try:
            if resultados_comparacion["status"] != "success":
                return {
                    "status": "error",
                    "message": "Los resultados de comparación no son válidos",
                    "imagen": None
                }
            
            # Extraer datos relevantes
            timbues = resultados_comparacion["timbues"]
            lima = resultados_comparacion["lima"]
            
            # Crear DataFrame para visualización
            categorias = ["Flete Terrestre", "Flete Marítimo", "Costos Fijos"]
            
            datos = pd.DataFrame({
                "Timbúes": [
                    timbues["desglose"]["flete_terrestre"],
                    timbues["desglose"]["flete_maritimo"],
                    timbues["desglose"]["costos_fijos"]
                ],
                "Lima": [
                    lima["desglose"]["flete_terrestre"],
                    lima["desglose"]["flete_maritimo"],
                    lima["desglose"]["costos_fijos"]
                ]
            }, index=categorias)
            
            # Calcular totales
            total_timbues = timbues["costo_total"]
            total_lima = lima["costo_total"]
            
            # Configurar figura
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Crear gráfico de barras agrupadas
            ancho = 0.35
            indice = np.arange(len(categorias))
            
            # Barras para cada puerto
            barra_timbues = ax.bar(indice - ancho/2, datos["Timbúes"], ancho, 
                                  label=f'Timbúes (Total: ${total_timbues:,.2f})', 
                                  color=self.colores_primarios[0])
            
            barra_lima = ax.bar(indice + ancho/2, datos["Lima"], ancho, 
                              label=f'Lima (Total: ${total_lima:,.2f})', 
                              color=self.colores_primarios[1])
            
            # Añadir etiquetas y leyenda
            ax.set_title('Comparación de Costos por Puerto', fontsize=16)
            ax.set_ylabel('Costo (USD)', fontsize=12)
            ax.set_xticks(indice)
            ax.set_xticklabels(categorias, fontsize=10)
            
            # Añadir valores en las barras
            def agregar_etiquetas(barras):
                for barra in barras:
                    altura = barra.get_height()
                    ax.text(barra.get_x() + barra.get_width()/2., altura + 0.1,
                           f'${altura:,.2f}', ha='center', va='bottom', 
                           fontsize=9, rotation=0)
            
            agregar_etiquetas(barra_timbues)
            agregar_etiquetas(barra_lima)
            
            # Añadir texto con análisis de diferencia
            puerto_optimo = resultados_comparacion["comparacion"]["puerto_optimo"]
            diferencia = resultados_comparacion["comparacion"]["diferencia_absoluta"]
            diferencia_porcentual = resultados_comparacion["comparacion"]["diferencia_porcentual"]
            
            resumen = f"""Puerto óptimo: {puerto_optimo.title()}
Ahorro: ${diferencia:,.2f} ({diferencia_porcentual:.1f}%)"""
            
            # Posicionar el texto de resumen
            plt.figtext(0.15, 0.02, resumen, fontsize=10, 
                      bbox=dict(facecolor='lightgray', alpha=0.5))
            
            # Mostrar leyenda
            ax.legend(loc='upper right')
            
            # Mejorar estética
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Guardar gráfico en memoria como imagen base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            imagen_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return {
                "status": "success",
                "imagen": imagen_base64,
                "formato": "png",
                "puerto_optimo": puerto_optimo,
                "diferencia_absoluta": diferencia,
                "diferencia_porcentual": diferencia_porcentual
            }
            
        except Exception as e:
            logger.error(f"Error al generar gráfico de comparación: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al generar gráfico de comparación: {str(e)}",
                "imagen": None
            }
    
    def generar_grafico_desglose_costos(self, 
                                      resultado_puerto: Dict,
                                      titulo: Optional[str] = None) -> Dict:
        """Generar gráfico circular de desglose de costos para un puerto.
        
        Args:
            resultado_puerto: Diccionario con resultados de cálculo de costos.
            titulo: Título personalizado para el gráfico.
            
        Returns:
            Diccionario con imagen base64 del gráfico y metadatos.
        """
        try:
            if resultado_puerto["status"] != "success":
                return {
                    "status": "error",
                    "message": "Los resultados del puerto no son válidos",
                    "imagen": None
                }
            
            # Extraer datos relevantes
            desglose = resultado_puerto["desglose"]
            puerto = resultado_puerto["puerto"].title()
            
            # Preparar datos para el gráfico
            categorias = ["Flete Terrestre", "Flete Marítimo", "Costos Fijos"]
            valores = [
                desglose["flete_terrestre"],
                desglose["flete_maritimo"],
                desglose["costos_fijos"]
            ]
            
            # Crear figura
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            fig.subplots_adjust(wspace=0.3)
            
            # Gráfico de torta
            wedges, texts, autotexts = ax1.pie(
                valores, 
                autopct='%1.1f%%',
                textprops={'fontsize': 9},
                colors=self.colores_primarios[:3],
                startangle=90,
                shadow=False
            )
            
            # Mejorar el aspecto visual
            plt.setp(autotexts, size=8, weight="bold")
            
            # Añadir leyenda
            ax1.legend(
                wedges, 
                [f"{cat} (${val:,.2f})" for cat, val in zip(categorias, valores)],
                loc="center left",
                bbox_to_anchor=(0.95, 0.5),
                fontsize=9
            )
            
            # Gráfico de barras horizontal
            y_pos = np.arange(len(categorias))
            ax2.barh(y_pos, valores, align='center', color=self.colores_primarios[:3])
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(categorias)
            ax2.invert_yaxis()  # Los valores más altos están abajo
            
            # Añadir valores en las barras
            for i, v in enumerate(valores):
                ax2.text(v + v*0.01, i, f"${v:,.2f}", va='center', fontsize=9)
            
            # Configurar título y etiquetas
            if not titulo:
                titulo = f"Desglose de Costos - Puerto {puerto}"
                
            fig.suptitle(titulo, fontsize=14)
            ax1.set_title("Proporción de Costos", fontsize=11)
            ax2.set_title("Montos por Categoría", fontsize=11)
            ax2.set_xlabel("Costo (USD)", fontsize=10)
            
            # Añadir texto con información adicional
            info_texto = f"""
Puerto: {puerto}
Distancia: {resultado_puerto['distancia_terrestre']:.0f} km
Carga: {resultado_puerto['toneladas']:.1f} toneladas
Costo Total: ${resultado_puerto['costo_total']:,.2f}
Costo Unitario: ${resultado_puerto['costo_unitario']:,.2f}/ton
            """
            
            # Posicionar el texto de información
            plt.figtext(0.01, 0.02, info_texto, fontsize=9, 
                      bbox=dict(facecolor='lightgray', alpha=0.5))
            
            # Eliminar bordes de los gráficos
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            
            # Guardar gráfico en memoria como imagen base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            imagen_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return {
                "status": "success",
                "imagen": imagen_base64,
                "formato": "png",
                "puerto": puerto,
                "costo_total": resultado_puerto['costo_total'],
                "costo_unitario": resultado_puerto['costo_unitario']
            }
            
        except Exception as e:
            logger.error(f"Error al generar gráfico de desglose: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al generar gráfico de desglose: {str(e)}",
                "imagen": None
            }
    
    def generar_mapa_rutas(self,
                         origen: Tuple[float, float],
                         nombre_origen: str,
                         ruta_timbues: Optional[Dict] = None,
                         ruta_lima: Optional[Dict] = None,
                         resultados_comparacion: Optional[Dict] = None) -> Dict:
        """Generar mapa interactivo con rutas a los puertos.
        
        Args:
            origen: Coordenadas (longitud, latitud) de origen.
            nombre_origen: Nombre del punto de origen.
            ruta_timbues: Diccionario con datos de ruta a Timbúes.
            ruta_lima: Diccionario con datos de ruta a Lima.
            resultados_comparacion: Resultados de comparación de costos.
            
        Returns:
            Diccionario con HTML del mapa y metadatos.
        """
        try:
            # Invertir coordenadas para folium (latitud, longitud)
            origen_invertido = (origen[1], origen[0])
            timbues_invertido = (self.coords_timbues[1], self.coords_timbues[0])
            lima_invertido = (self.coords_lima[1], self.coords_lima[0])
            
            # Crear mapa base
            mapa = folium.Map(
                location=[-20, -65],  # Centrado aproximado en Sudamérica
                zoom_start=4,
                tiles='CartoDB positron'
            )
            
            # Añadir título al mapa
            titulo_html = '''
            <div style="position: fixed; 
                        top: 10px; left: 50px; width: 300px; height: 90px; 
                        background-color: white; border-radius: 5px;
                        z-index: 900; font-size: 14px; padding: 10px">
                <h4 style="margin-top: 0;">Rutas de Exportación</h4>
                <p>Comparación de rutas desde el origen hacia puertos alternativos</p>
            </div>
            '''
            mapa.get_root().html.add_child(folium.Element(titulo_html))
            
            # Marcador para el origen
            folium.Marker(
                location=origen_invertido,
                popup=folium.Popup(f"<b>Origen:</b> {nombre_origen}", max_width=200),
                tooltip=nombre_origen,
                icon=folium.Icon(color="green", icon="play", prefix="fa")
            ).add_to(mapa)
            
            # Marcadores para los puertos
            folium.Marker(
                location=timbues_invertido,
                popup=folium.Popup("<b>Puerto:</b> Timbúes", max_width=200),
                tooltip="Puerto Timbúes",
                icon=folium.Icon(color="blue", icon="anchor", prefix="fa")
            ).add_to(mapa)
            
            folium.Marker(
                location=lima_invertido,
                popup=folium.Popup("<b>Puerto:</b> Lima", max_width=200),
                tooltip="Puerto Lima",
                icon=folium.Icon(color="red", icon="anchor", prefix="fa")
            ).add_to(mapa)
            
            # Añadir líneas de rutas si están disponibles
            if ruta_timbues and ruta_timbues["status"] == "success" and ruta_timbues["geometry"]:
                # Convertir geometría de polyline a coordenadas [lat, lng]
                ruta_coords = ruta_timbues["geometry"]
                
                # Dibujar ruta a Timbúes
                folium.PolyLine(
                    locations=ruta_coords,
                    color=self.colores_primarios[0],
                    weight=4,
                    opacity=0.8,
                    tooltip=f"Ruta a Timbúes: {ruta_timbues['distance']} km"
                ).add_to(mapa)
                
                # Añadir etiqueta de distancia
                midpoint = ruta_coords[len(ruta_coords)//2]
                folium.Marker(
                    location=midpoint,
                    icon=DivIcon(
                        icon_size=(150, 36),
                        icon_anchor=(75, 18),
                        html=f'<div style="background-color: rgba(255, 255, 255, 0.8); padding: 2px 5px; border-radius: 3px; font-size: 11px;"><b>Timbúes:</b> {ruta_timbues["distance"]} km</div>'
                    )
                ).add_to(mapa)
            
            if ruta_lima and ruta_lima["status"] == "success" and ruta_lima["geometry"]:
                # Convertir geometría de polyline a coordenadas [lat, lng]
                ruta_coords = ruta_lima["geometry"]
                
                # Dibujar ruta a Lima
                folium.PolyLine(
                    locations=ruta_coords,
                    color=self.colores_primarios[1],
                    weight=4,
                    opacity=0.8,
                    tooltip=f"Ruta a Lima: {ruta_lima['distance']} km"
                ).add_to(mapa)
                
                # Añadir etiqueta de distancia
                midpoint = ruta_coords[len(ruta_coords)//2]
                folium.Marker(
                    location=midpoint,
                    icon=DivIcon(
                        icon_size=(150, 36),
                        icon_anchor=(75, 18),
                        html=f'<div style="background-color: rgba(255, 255, 255, 0.8); padding: 2px 5px; border-radius: 3px; font-size: 11px;"><b>Lima:</b> {ruta_lima["distance"]} km</div>'
                    )
                ).add_to(mapa)
            
            # Añadir leyenda con resultados de comparación si están disponibles
            if resultados_comparacion and resultados_comparacion["status"] == "success":
                puerto_optimo = resultados_comparacion["comparacion"]["puerto_optimo"].title()
                ahorro = resultados_comparacion["comparacion"]["diferencia_absoluta"]
                porcentaje = resultados_comparacion["comparacion"]["diferencia_porcentual"]
                
                costo_timbues = resultados_comparacion["timbues"]["costo_total"]
                costo_lima = resultados_comparacion["lima"]["costo_total"]
                
                legend_html = f'''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 250px;
                            background-color: white; border-radius: 5px;
                            z-index: 900; font-size: 12px; padding: 10px">
                    <h5 style="margin-top: 0;">Comparación de Costos</h5>
                    <p><b>Timbúes:</b> ${costo_timbues:,.2f}</p>
                    <p><b>Lima:</b> ${costo_lima:,.2f}</p>
                    <p><b>Puerto óptimo:</b> {puerto_optimo}</p>
                    <p><b>Ahorro:</b> ${ahorro:,.2f} ({porcentaje:.1f}%)</p>
                </div>
                '''
                mapa.get_root().html.add_child(folium.Element(legend_html))
            
            # Centrar mapa para incluir todos los puntos
            mapa.fit_bounds([origen_invertido, timbues_invertido, lima_invertido])
            
            # Convertir mapa a HTML
            html_mapa = mapa._repr_html_()
            
            return {
                "status": "success",
                "mapa_html": html_mapa,
                "origen": nombre_origen,
                "incluye_ruta_timbues": ruta_timbues is not None and ruta_timbues["status"] == "success",
                "incluye_ruta_lima": ruta_lima is not None and ruta_lima["status"] == "success"
            }
            
        except Exception as e:
            logger.error(f"Error al generar mapa de rutas: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al generar mapa de rutas: {str(e)}",
                "mapa_html": None
            }
    
    def generar_grafico_sensibilidad(self,
                                   valores_parametro: List[float],
                                   costos_timbues: List[float],
                                   costos_lima: List[float],
                                   nombre_parametro: str,
                                   unidad_parametro: str) -> Dict:
        """Generar gráfico de análisis de sensibilidad.
        
        Args:
            valores_parametro: Lista de valores del parámetro analizado.
            costos_timbues: Lista de costos correspondientes para Timbúes.
            costos_lima: Lista de costos correspondientes para Lima.
            nombre_parametro: Nombre del parámetro (ej. 'Distancia', 'Toneladas').
            unidad_parametro: Unidad del parámetro (ej. 'km', 'ton').
            
        Returns:
            Diccionario con imagen base64 del gráfico y metadatos.
        """
        try:
            if len(valores_parametro) != len(costos_timbues) or len(valores_parametro) != len(costos_lima):
                return {
                    "status": "error",
                    "message": "Las listas de valores y costos deben tener la misma longitud",
                    "imagen": None
                }
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Trazar líneas para cada puerto
            ax.plot(valores_parametro, costos_timbues, 'o-', 
                  color=self.colores_primarios[0], 
                  linewidth=2, 
                  markersize=6,
                  label="Puerto Timbúes")
            
            ax.plot(valores_parametro, costos_lima, 's-', 
                  color=self.colores_primarios[1], 
                  linewidth=2, 
                  markersize=6,
                  label="Puerto Lima")
            
            # Calcular punto de cruce (si existe)
            punto_cruce_x = None
            punto_cruce_y = None
            
            for i in range(len(valores_parametro) - 1):
                if (costos_timbues[i] > costos_lima[i] and costos_timbues[i+1] < costos_lima[i+1]) or \
                   (costos_timbues[i] < costos_lima[i] and costos_timbues[i+1] > costos_lima[i+1]):
                    # Estimación lineal del punto de cruce
                    x1, y1_t, y1_l = valores_parametro[i], costos_timbues[i], costos_lima[i]
                    x2, y2_t, y2_l = valores_parametro[i+1], costos_timbues[i+1], costos_lima[i+1]
                    
                    m_t = (y2_t - y1_t) / (x2 - x1)
                    m_l = (y2_l - y1_l) / (x2 - x1)
                    
                    b_t = y1_t - m_t * x1
                    b_l = y1_l - m_l * x1
                    
                    # Resolver para x: m_t * x + b_t = m_l * x + b_l
                    punto_cruce_x = (b_l - b_t) / (m_t - m_l)
                    punto_cruce_y = m_t * punto_cruce_x + b_t
                    
                    # Marcar el punto de cruce
                    ax.plot(punto_cruce_x, punto_cruce_y, 'X', 
                          color='green', markersize=10, 
                          label=f"Punto de equilibrio: {punto_cruce_x:.1f} {unidad_parametro}")
                    
                    # Línea vertical en el punto de cruce
                    ax.axvline(x=punto_cruce_x, color='green', linestyle='--', alpha=0.5)
                    break
            
            # Regiones de colores para indicar puerto más conveniente
            if punto_cruce_x:
                min_x = min(valores_parametro)
                max_x = max(valores_parametro)
                max_y = max(max(costos_timbues), max(costos_lima)) * 1.1
                
                # Determinar qué puerto es mejor en cada región
                if costos_timbues[0] < costos_lima[0]:
                    # Timbúes es mejor para valores bajos del parámetro
                    ax.fill_between([min_x, punto_cruce_x], 0, max_y, 
                                  color=self.colores_primarios[0], alpha=0.1)
                    ax.fill_between([punto_cruce_x, max_x], 0, max_y, 
                                  color=self.colores_primarios[1], alpha=0.1)
                else:
                    # Lima es mejor para valores bajos del parámetro
                    ax.fill_between([min_x, punto_cruce_x], 0, max_y, 
                                  color=self.colores_primarios[1], alpha=0.1)
                    ax.fill_between([punto_cruce_x, max_x], 0, max_y, 
                                  color=self.colores_primarios[0], alpha=0.1)
            
            # Configurar etiquetas y título
            ax.set_title(f'Análisis de Sensibilidad - {nombre_parametro}', fontsize=14)
            ax.set_xlabel(f'{nombre_parametro} ({unidad_parametro})', fontsize=12)
            ax.set_ylabel('Costo Total (USD)', fontsize=12)
            
            # Mejorar estética
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Colocar leyenda
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10)
            
            # Añadir anotación de punto de cruce
            if punto_cruce_x:
                ax.annotate(
                    f'Punto de equilibrio:\n{punto_cruce_x:.1f} {unidad_parametro}, ${punto_cruce_y:.2f}',
                    xy=(punto_cruce_x, punto_cruce_y),
                    xytext=(punto_cruce_x + (max_x - min_x)*0.1, punto_cruce_y + (max_y*0.1)),
                    arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
                )
            
            # Guardar gráfico en memoria como imagen base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            imagen_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return {
                "status": "success",
                "imagen": imagen_base64,
                "formato": "png",
                "parametro": nombre_parametro,
                "unidad": unidad_parametro,
                "punto_equilibrio": punto_cruce_x,
                "costo_equilibrio": punto_cruce_y
            }
            
        except Exception as e:
            logger.error(f"Error al generar gráfico de sensibilidad: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al generar gráfico de sensibilidad: {str(e)}",
                "imagen": None
            }