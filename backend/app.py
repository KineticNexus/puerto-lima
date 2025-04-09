"""
Punto de entrada principal para la aplicación puerto-lima.

Este módulo inicializa la aplicación Flask, registra las rutas API
y establece la configuración necesaria para los distintos servicios.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from typing import Dict, List, Any

# Importar configuración
from config.default import (
    COORDENADAS_TIMBUES, 
    COORDENADAS_LIMA, 
    FLETES_MARITIMOS,
    COSTO_FLETE_TERRESTRE,
    FACTORES_CORRECCION_RUTA
)

# Importar servicios MCP
from mcp.routes_mcp import OSRMRouteMCP
from mcp.viz_mcp import MapboxVisualizationMCP
from mcp.analysis_mcp import SensitivityAnalysisMCP

# Inicializar la aplicación Flask
app = Flask(__name__)
CORS(app)  # Permitir Cross-Origin Resource Sharing

# Inicializar servicios MCP
osrm_mcp = OSRMRouteMCP()
viz_mcp = MapboxVisualizationMCP()
analysis_mcp = SensitivityAnalysisMCP()

# Directorio para archivos exportados
EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Ruta principal
@app.route('/')
def index():
    return jsonify({
        "name": "Puerto-Lima API",
        "version": "1.0.0",
        "description": "API para análisis comparativo de costos de exportación entre puertos Timbúes y Lima (Zárate)."
    })

# Documentación de la API
@app.route('/docs')
def docs():
    return jsonify({
        "api_endpoints": [
            {
                "path": "/calculate_costs",
                "method": "POST",
                "description": "Calcula costos de exportación para un sector o empresa",
                "params": {
                    "coordinates": "[lon, lat] - Coordenadas del origen",
                    "volume": "Volumen anual en toneladas",
                    "destination": "Destino internacional (china, europa, brasil)"
                }
            },
            {
                "path": "/analyze_sectors",
                "method": "POST",
                "description": "Analiza múltiples sectores y genera visualización",
                "params": {
                    "sectors": "Lista de sectores con coordenadas",
                    "destination": "Destino internacional"
                }
            },
            {
                "path": "/analyze_companies",
                "method": "POST",
                "description": "Realiza recomendaciones para empresas",
                "params": {
                    "companies": "Lista de empresas con coordenadas y volúmenes",
                    "destination": "Destino internacional"
                }
            },
            {
                "path": "/sensitivity_analysis",
                "method": "POST",
                "description": "Realiza análisis de sensibilidad",
                "params": {
                    "sectors": "Resultados de sectores",
                    "variables": "Variables a analizar"
                }
            },
            {
                "path": "/generate_report",
                "method": "POST",
                "description": "Genera un reporte completo en PDF",
                "params": {
                    "sectors_results": "Resultados del análisis de sectores",
                    "companies_results": "Resultados del análisis de empresas",
                    "sensitivity_results": "Resultados del análisis de sensibilidad"
                }
            },
            {
                "path": "/mcp/route",
                "method": "POST",
                "description": "Endpoint MCP para cálculo de rutas",
                "params": {
                    "action": "Acción a realizar",
                    "context": "Contexto con datos para la acción"
                }
            },
            {
                "path": "/mcp/visualization",
                "method": "POST",
                "description": "Endpoint MCP para visualización",
                "params": {
                    "action": "Acción a realizar",
                    "context": "Contexto con datos para la acción"
                }
            },
            {
                "path": "/mcp/sensitivity",
                "method": "POST",
                "description": "Endpoint MCP para análisis de sensibilidad",
                "params": {
                    "action": "Acción a realizar",
                    "context": "Contexto con datos para la acción"
                }
            }
        ]
    })

# Calcular costos de exportación
@app.route('/calculate_costs', methods=['POST'])
def calculate_costs():
    try:
        data = request.json
        
        # Validar datos de entrada
        if not data or 'coordinates' not in data:
            return jsonify({"error": "Se requieren coordenadas de origen"}), 400
        
        coordinates = data['coordinates']
        volume = data.get('volume', 1000)  # Volumen en toneladas
        destination = data.get('destination', 'china')
        
        # Validar destino
        if destination not in FLETES_MARITIMOS:
            return jsonify({"error": f"Destino no válido. Opciones: {list(FLETES_MARITIMOS.keys())}"}), 400
        
        # Obtener fletes marítimos para el destino
        flete_maritimo_timbues = FLETES_MARITIMOS[destination]['timbues']
        flete_maritimo_lima = FLETES_MARITIMOS[destination]['lima']
        
        # Calcular distancia terrestre a cada puerto usando OSRM
        distancia_timbues_result = osrm_mcp.handle_request('calculate_distance', {
            'origin': coordinates,
            'destination': COORDENADAS_TIMBUES
        })
        
        distancia_lima_result = osrm_mcp.handle_request('calculate_distance', {
            'origin': coordinates,
            'destination': COORDENADAS_LIMA
        })
        
        if 'error' in distancia_timbues_result or 'error' in distancia_lima_result:
            return jsonify({
                "error": "Error al calcular distancias",
                "details": {
                    "timbues": distancia_timbues_result.get('error', ''),
                    "lima": distancia_lima_result.get('error', '')
                }
            }), 500
        
        # Obtener distancias en km
        distancia_timbues = distancia_timbues_result.get('distance', 0)
        distancia_lima = distancia_lima_result.get('distance', 0)
        
        # Determinar factor de corrección según región
        region = data.get('region', 'default')
        factor_correccion = FACTORES_CORRECCION_RUTA.get(region, FACTORES_CORRECCION_RUTA['default'])
        
        # Aplicar factor de corrección
        distancia_timbues_corregida = distancia_timbues * factor_correccion
        distancia_lima_corregida = distancia_lima * factor_correccion
        
        # Calcular costos de flete terrestre
        costo_terrestre_timbues = distancia_timbues_corregida * COSTO_FLETE_TERRESTRE
        costo_terrestre_lima = distancia_lima_corregida * COSTO_FLETE_TERRESTRE
        
        # Costos totales por tonelada
        costo_total_timbues = costo_terrestre_timbues + flete_maritimo_timbues
        costo_total_lima = costo_terrestre_lima + flete_maritimo_lima
        
        # Diferencial (costoTimbues - costoLima)
        diferencial = costo_total_timbues - costo_total_lima
        
        # Puerto óptimo
        puerto_optimo = "Timbúes" if diferencial < 0 else "Lima"
        
        # Ahorro total anual
        ahorro_anual = abs(diferencial) * volume
        
        return jsonify({
            "coordinates": coordinates,
            "region": region,
            "destination": destination,
            "distancias": {
                "timbues": distancia_timbues_corregida,
                "lima": distancia_lima_corregida
            },
            "costos": {
                "terrestre_timbues": costo_terrestre_timbues,
                "terrestre_lima": costo_terrestre_lima,
                "maritimo_timbues": flete_maritimo_timbues,
                "maritimo_lima": flete_maritimo_lima,
                "total_timbues": costo_total_timbues,
                "total_lima": costo_total_lima
            },
            "diferencial": diferencial,
            "puertoOptimo": puerto_optimo,
            "ahorroAnual": ahorro_anual
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Analizar múltiples sectores
@app.route('/analyze_sectors', methods=['POST'])
def analyze_sectors():
    try:
        data = request.json
        
        # Validar datos de entrada
        if not data or 'sectors' not in data:
            return jsonify({"error": "Se requieren datos de sectores"}), 400
        
        sectors = data['sectors']
        destination = data.get('destination', 'china')
        
        # Resultados para cada sector
        results = []
        
        for sector in sectors:
            if 'coordinates' not in sector:
                continue
                
            # Calcular costos para este sector
            sector_data = {
                'coordinates': sector['coordinates'],
                'region': sector.get('region', 'default'),
                'destination': destination
            }
            
            # Si el sector tiene volumen de producción, incluirlo
            if 'produccionTotal' in sector:
                sector_data['volume'] = sector['produccionTotal']
            
            # Llamar a la función de cálculo
            response = calculate_costs()
            if response.status_code != 200:
                continue
                
            # Extraer resultados
            sector_result = response.get_json()
            
            # Añadir identificador del sector
            sector_result['id'] = sector.get('id', f"sector_{len(results)}")
            
            # Incluir datos de producción si existen
            if 'produccionTotal' in sector:
                sector_result['produccionTotal'] = sector['produccionTotal']
            
            results.append(sector_result)
        
        # Encontrar diferenciales extremos
        differentials = [r['diferencial'] for r in results]
        min_differential = min(differentials) if differentials else 0
        max_differential = max(differentials) if differentials else 0
        
        # Generar visualización
        visualization = viz_mcp.handle_request('create_gradient_map', {
            'sectors': results,
            'min_differential': min_differential,
            'max_differential': max_differential
        })
        
        # Generar HTML
        html_viz = None
        if 'status' in visualization and visualization['status'] == 'success':
            html_result = viz_mcp.handle_request('generate_html_visualization', {
                'mapbox_config': visualization['mapbox_config'],
                'title': f"Análisis Comparativo Timbúes vs. Lima - Destino: {destination.capitalize()}"
            })
            
            if 'status' in html_result and html_result['status'] == 'success':
                html_viz = html_result['url']
        
        return jsonify({
            "status": "success",
            "results": results,
            "stats": {
                "total_sectors": len(results),
                "min_differential": min_differential,
                "max_differential": max_differential,
                "timbues_preference": sum(1 for r in results if r['diferencial'] < 0),
                "lima_preference": sum(1 for r in results if r['diferencial'] > 0)
            },
            "visualization": visualization,
            "html_visualization": html_viz
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Analizar empresas
@app.route('/analyze_companies', methods=['POST'])
def analyze_companies():
    try:
        data = request.json
        
        # Validar datos de entrada
        if not data or 'companies' not in data:
            return jsonify({"error": "Se requieren datos de empresas"}), 400
        
        companies = data['companies']
        destination = data.get('destination', 'china')
        
        # Resultados para cada empresa
        results = []
        
        for company in companies:
            if 'coordenadas' not in company or 'volumenAnual' not in company:
                continue
                
            # Calcular costos para esta empresa
            company_data = {
                'coordinates': company['coordenadas'],
                'volume': company['volumenAnual'],
                'destination': destination
            }
            
            # Llamar a la función de cálculo
            sector_data = {
                'coordinates': company['coordenadas'],
                'volume': company['volumenAnual'],
                'destination': destination,
                'region': company.get('region', 'default')
            }
            
            # Hacer el cálculo
            response = app.test_client().post('/calculate_costs', 
                                          json=sector_data, 
                                          content_type='application/json')
            
            if response.status_code != 200:
                continue
                
            # Extraer resultados
            company_result = response.get_json()
            
            # Añadir datos de la empresa
            company_result['nombre'] = company.get('nombre', f"empresa_{len(results)}")
            company_result['volumenAnual'] = company['volumenAnual']
            
            results.append(company_result)
        
        # Generar visualización
        visualization = viz_mcp.handle_request('create_company_map', {
            'companies': results
        })
        
        # Generar HTML
        html_viz = None
        if 'status' in visualization and visualization['status'] == 'success':
            html_result = viz_mcp.handle_request('generate_html_visualization', {
                'mapbox_config': visualization['mapbox_config'],
                'title': f"Análisis de Empresas - Destino: {destination.capitalize()}"
            })
            
            if 'status' in html_result and html_result['status'] == 'success':
                html_viz = html_result['url']
        
        return jsonify({
            "status": "success",
            "results": results,
            "stats": {
                "total_companies": len(results),
                "timbues_preference": sum(1 for r in results if r['puertoOptimo'] == "Timbúes"),
                "lima_preference": sum(1 for r in results if r['puertoOptimo'] == "Lima"),
                "total_savings": sum(r['ahorroAnual'] for r in results)
            },
            "visualization": visualization,
            "html_visualization": html_viz
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Análisis de sensibilidad
@app.route('/sensitivity_analysis', methods=['POST'])
def sensitivity_analysis():
    try:
        data = request.json
        
        # Validar datos de entrada
        if not data or 'sectors' not in data:
            return jsonify({"error": "Se requieren datos de sectores"}), 400
        
        sectors = data['sectors']
        variables = data.get('variables')
        
        # Realizar análisis de sensibilidad
        sensitivity_result = analysis_mcp.handle_request('analyze_sensitivity', {
            'sectors': sectors,
            'calculate_costs_fn': {
                'type': 'simulation',
                'method': 'internal'
            },
            'variables': variables
        })
        
        return jsonify(sensitivity_result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Generar reporte completo
@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        
        # Validar datos de entrada
        if not data:
            return jsonify({"error": "Se requieren datos para el reporte"}), 400
        
        sectors_results = data.get('sectors_results', [])
        companies_results = data.get('companies_results', [])
        sensitivity_results = data.get('sensitivity_results', {})
        
        # Aquí implementaríamos la generación real del reporte con WeasyPrint
        # Para este ejemplo, simularemos la creación de un reporte
        
        report_filename = f"report_{int(time.time())}.pdf"
        report_path = os.path.join(EXPORTS_DIR, report_filename)
        
        # En una implementación real, aquí se crearía el PDF
        # Para este ejemplo, creamos un archivo vacío
        with open(report_path, 'w') as f:
            f.write("Placeholder for PDF report")
        
        return jsonify({
            "status": "success",
            "report_filename": report_filename,
            "report_url": f"/exports/{report_filename}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Servir archivos exportados
@app.route('/exports/<path:filename>')
def serve_export(filename):
    return send_from_directory(EXPORTS_DIR, filename)

# MCP Routes
@app.route('/mcp/route', methods=['POST'])
def mcp_route():
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

# MCP Visualization
@app.route('/mcp/visualization', methods=['POST'])
def mcp_visualization():
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

# MCP Sensitivity Analysis
@app.route('/mcp/sensitivity', methods=['POST'])
def mcp_sensitivity():
    try:
        data = request.json
        action = data.get('action')
        context = data.get('context', {})
        
        if not action:
            return jsonify({"error": "Se requiere una acción"}), 400
            
        result = analysis_mcp.handle_request(action, context)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    # Configuración para desarrollo local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)