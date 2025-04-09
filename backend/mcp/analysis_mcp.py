"""
Módulo MCP para análisis de sensibilidad del modelo económico

Este módulo proporciona funcionalidades MCP para realizar análisis de sensibilidad
sobre los parámetros del modelo comparativo entre puertos, permitiendo evaluar
la robustez de las recomendaciones frente a cambios en variables clave.
"""

import os
import json
import copy
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.default import SENSITIVITY_CONFIG, UMBRAL_SIGNIFICATIVO

class SensitivityAnalysisMCP:
    """
    Implementación MCP para análisis de sensibilidad del modelo.
    
    Proporciona métodos para:
    - Realizar análisis de sensibilidad sobre parámetros clave
    - Evaluar la robustez de recomendaciones
    - Identificar parámetros críticos
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el servicio MCP con la configuración de análisis.
        
        Args:
            config: Configuración opcional que sobreescribe la configuración por defecto
        """
        self.config = config or SENSITIVITY_CONFIG
        self.variables = self.config.get("variables", {})
        self.threshold = self.config.get("threshold", UMBRAL_SIGNIFICATIVO)
    
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
            "analyze_sensitivity": self.analyze_sensitivity,
            "evaluate_robustness": self.evaluate_robustness,
            "identify_critical_parameters": self.identify_critical_parameters,
        }
        
        if action not in action_handlers:
            return {
                "error": f"Acción no soportada: {action}",
                "supported_actions": list(action_handlers.keys())
            }
        
        return action_handlers[action](context)
    
    def analyze_sensitivity(self, context: Dict) -> Dict:
        """
        Realiza un análisis de sensibilidad completo con diferentes valores
        para los parámetros clave, recalculando los resultados.
        
        Args:
            context: Diccionario con:
                - sectors: resultados originales del análisis por sectores
                - calculate_costs_fn: función para recalcular costos (o definición de API a invocar)
                - variables: parámetros a variar (opcional, sobreescribe config)
                
        Returns:
            Resultados del análisis de sensibilidad
        """
        try:
            # Validar datos de entrada
            sectors = context.get("sectors", [])
            
            if not sectors:
                return {"error": "Se requieren datos de sectores para el análisis"}
            
            # Obtener función o definición de API para recálculo
            calculate_costs_fn = context.get("calculate_costs_fn")
            if not calculate_costs_fn:
                return {"error": "Se requiere una función o API para recalcular costos"}
            
            # Obtener variables para el análisis (de contexto o configuración)
            variables = context.get("variables", self.variables)
            
            # Preparar estructura para resultados
            sensitivity_results = {}
            
            # Para cada variable a analizar
            for var_name, var_values in variables.items():
                var_changes = {
                    "valores_analizados": var_values,
                    "cambios_por_valor": {},
                    "sectores_afectados": [],
                    "porcentaje_cambios": 0
                }
                
                # Para cada valor de la variable
                for value in var_values:
                    # Clonar la configuración original para este escenario
                    scenario_config = {
                        "variable": var_name,
                        "value": value
                    }
                    
                    # Recalcular resultados para este escenario
                    new_results = self._recalculate_with_scenario(sectors, calculate_costs_fn, scenario_config)
                    
                    # Analizar cambios en recomendaciones
                    changes = self._analyze_changes(sectors, new_results)
                    
                    # Guardar resultados para este valor
                    var_changes["cambios_por_valor"][str(value)] = {
                        "sectores_cambiados": changes["changed_sectors"],
                        "numero_cambios": changes["change_count"],
                        "porcentaje_cambio": changes["change_percentage"]
                    }
                
                # Calcular porcentaje máximo de cambios para esta variable
                max_changes = max([c["porcentaje_cambio"] for c in var_changes["cambios_por_valor"].values()])
                var_changes["porcentaje_cambios"] = max_changes
                
                # Identificar sectores más afectados por esta variable
                affected_sectors = set()
                for changes in var_changes["cambios_por_valor"].values():
                    affected_sectors.update([s["id"] for s in changes["sectores_cambiados"]])
                
                var_changes["sectores_afectados"] = list(affected_sectors)
                
                # Guardar resultados para esta variable
                sensitivity_results[var_name] = var_changes
            
            # Generar análisis y comentarios
            analysis = self._generate_sensitivity_analysis(sensitivity_results, sectors)
            
            return {
                "status": "success",
                "sensitivity_results": sensitivity_results,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error en el análisis de sensibilidad: {str(e)}"
            }
    
    def evaluate_robustness(self, context: Dict) -> Dict:
        """
        Evalúa la robustez de las recomendaciones actuales frente a
        variaciones en los parámetros.
        
        Args:
            context: Diccionario con:
                - companies: recomendaciones para empresas
                - calculate_costs_fn: función para recalcular costos
                - variables: parámetros a variar (opcional)
                
        Returns:
            Evaluación de robustez para cada empresa
        """
        try:
            # Validar datos de entrada
            companies = context.get("companies", [])
            
            if not companies:
                return {"error": "Se requieren datos de empresas para la evaluación"}
            
            # Obtener función o definición de API para recálculo
            calculate_costs_fn = context.get("calculate_costs_fn")
            if not calculate_costs_fn:
                return {"error": "Se requiere una función o API para recalcular costos"}
            
            # Obtener variables para el análisis (de contexto o configuración)
            variables = context.get("variables", self.variables)
            
            # Preparar estructura para resultados
            robustness_results = {}
            
            # Para cada empresa
            for company in companies:
                company_id = company.get("nombre", "")
                if not company_id:
                    continue
                
                # Inicializar resultados para esta empresa
                company_robustness = {
                    "puerto_original": company.get("puertoOptimo", ""),
                    "ahorro_original": company.get("ahorroAnual", 0),
                    "escenarios_analizados": 0,
                    "cambios_de_recomendacion": 0,
                    "robustez_porcentual": 0,
                    "nivel_robustez": "",
                    "escenarios_adversos": []
                }
                
                # Generar todos los escenarios combinando valores de variables
                scenarios = self._generate_scenarios(variables)
                company_robustness["escenarios_analizados"] = len(scenarios)
                
                # Calcular para cada escenario
                for scenario in scenarios:
                    # Recalcular para este escenario
                    new_recommendation = self._recalculate_company_with_scenario(company, calculate_costs_fn, scenario)
                    
                    # Si cambia la recomendación, registrar
                    if new_recommendation["puertoOptimo"] != company_robustness["puerto_original"]:
                        company_robustness["cambios_de_recomendacion"] += 1
                        company_robustness["escenarios_adversos"].append({
                            "escenario": scenario,
                            "nuevo_puerto": new_recommendation["puertoOptimo"],
                            "nuevo_ahorro": new_recommendation["ahorroAnual"]
                        })
                
                # Calcular robustez porcentual (% de escenarios donde no cambia la recomendación)
                if company_robustness["escenarios_analizados"] > 0:
                    unchanged = company_robustness["escenarios_analizados"] - company_robustness["cambios_de_recomendacion"]
                    company_robustness["robustez_porcentual"] = (unchanged / company_robustness["escenarios_analizados"]) * 100
                
                # Determinar nivel de robustez
                if company_robustness["robustez_porcentual"] >= 90:
                    company_robustness["nivel_robustez"] = "Alta"
                elif company_robustness["robustez_porcentual"] >= 70:
                    company_robustness["nivel_robustez"] = "Media"
                else:
                    company_robustness["nivel_robustez"] = "Baja"
                
                # Guardar resultados para esta empresa
                robustness_results[company_id] = company_robustness
            
            # Generar resumen general
            summary = self._generate_robustness_summary(robustness_results)
            
            return {
                "status": "success",
                "robustness_results": robustness_results,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error en la evaluación de robustez: {str(e)}"
            }
    
    def identify_critical_parameters(self, context: Dict) -> Dict:
        """
        Identifica los parámetros más críticos que influyen en las recomendaciones.
        
        Args:
            context: Diccionario con:
                - sensitivity_results: resultados del análisis de sensibilidad
                
        Returns:
            Clasificación de parámetros por nivel de criticidad
        """
        try:
            # Validar datos de entrada
            sensitivity_results = context.get("sensitivity_results")
            
            if not sensitivity_results:
                return {"error": "Se requieren resultados de sensibilidad para identificar parámetros críticos"}
            
            # Ordenar parámetros por porcentaje de cambios
            parameters = []
            for param_name, param_data in sensitivity_results.items():
                parameters.append({
                    "parametro": param_name,
                    "porcentaje_cambios": param_data["porcentaje_cambios"],
                    "sectores_afectados": len(param_data["sectores_afectados"])
                })
            
            # Ordenar por porcentaje de cambios (descendente)
            parameters.sort(key=lambda x: x["porcentaje_cambios"], reverse=True)
            
            # Clasificar parámetros
            critical_parameters = []
            important_parameters = []
            stable_parameters = []
            
            for param in parameters:
                if param["porcentaje_cambios"] >= 30:
                    critical_parameters.append(param)
                elif param["porcentaje_cambios"] >= 10:
                    important_parameters.append(param)
                else:
                    stable_parameters.append(param)
            
            # Generar comentario general
            general_comment = ""
            if critical_parameters:
                general_comment = "El modelo muestra alta sensibilidad a cambios en algunos parámetros, " + \
                                  "lo que sugiere que pequeñas variaciones en costos podrían alterar " + \
                                  "significativamente las recomendaciones para ciertos sectores."
            else:
                general_comment = "El modelo muestra estabilidad frente a variaciones en los parámetros, " + \
                                  "lo que sugiere que las recomendaciones son robustas y confiables " + \
                                  "incluso ante cambios moderados en los costos."
            
            # Si los parámetros críticos influyen en menos del 10% de los sectores
            if critical_parameters and max([p["sectores_afectados"] for p in critical_parameters]) < 10:
                general_comment += " Sin embargo, estos cambios afectan a un porcentaje limitado de sectores."
            
            return {
                "status": "success",
                "parametros_criticos": critical_parameters,
                "parametros_importantes": important_parameters,
                "parametros_estables": stable_parameters,
                "comentario_general": general_comment
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error al identificar parámetros críticos: {str(e)}"
            }
    
    def _recalculate_with_scenario(self, sectors: List[Dict], calculate_costs_fn: Union[callable, Dict], scenario: Dict) -> List[Dict]:
        """
        Recalcula los resultados con un escenario específico.
        
        Args:
            sectors: Resultados originales
            calculate_costs_fn: Función o definición de API para recálculo
            scenario: Definición del escenario
            
        Returns:
            Resultados recalculados
        """
        # Clonar sectores para no modificar los originales
        new_sectors = copy.deepcopy(sectors)
        
        # Si calculate_costs_fn es una función, llamarla directamente
        if callable(calculate_costs_fn):
            return calculate_costs_fn(new_sectors, scenario)
        
        # Si es una definición de API, simulamos el recálculo
        # En un entorno real, aquí se haría una llamada a la API
        # Para este ejemplo, simularemos el resultado
        
        # Aplicar el escenario a cada sector
        variable = scenario["variable"]
        value = scenario["value"]
        
        for sector in new_sectors:
            # Simulamos el cambio en costos según la variable
            if variable == "flete_terrestre":
                # Ajustar ambos costos en proporción al cambio
                factor = value / 0.043  # Relativo al valor por defecto
                sector["costoTimbues"] = self._adjust_cost_component(sector["costoTimbues"], "terrestre", factor)
                sector["costoLima"] = self._adjust_cost_component(sector["costoLima"], "terrestre", factor)
            
            elif variable == "flete_maritimo_factor":
                # Ajustar componente marítimo
                sector["costoTimbues"] = self._adjust_cost_component(sector["costoTimbues"], "maritimo", value)
                sector["costoLima"] = self._adjust_cost_component(sector["costoLima"], "maritimo", value)
            
            # Recalcular diferencial
            sector["diferencial"] = sector["costoTimbues"] - sector["costoLima"]
        
        return new_sectors
    
    def _adjust_cost_component(self, total_cost: float, component: str, factor: float) -> float:
        """
        Ajusta un componente del costo total.
        
        Args:
            total_cost: Costo total actual
            component: Componente a ajustar ("terrestre" o "maritimo")
            factor: Factor de ajuste
            
        Returns:
            Nuevo costo total
        """
        # Estimación simplificada - en una implementación real se tendría más detalle
        if component == "terrestre":
            # Asumimos que el 60% del costo es terrestre
            terrestrial_part = total_cost * 0.6
            maritime_part = total_cost * 0.4
            return (terrestrial_part * factor) + maritime_part
        elif component == "maritimo":
            # Asumimos que el 40% del costo es marítimo
            terrestrial_part = total_cost * 0.6
            maritime_part = total_cost * 0.4
            return terrestrial_part + (maritime_part * factor)
        else:
            return total_cost
    
    def _analyze_changes(self, original_sectors: List[Dict], new_sectors: List[Dict]) -> Dict:
        """
        Analiza los cambios en las recomendaciones entre dos conjuntos de resultados.
        
        Args:
            original_sectors: Resultados originales
            new_sectors: Resultados recalculados
            
        Returns:
            Estadísticas de cambios
        """
        changed_sectors = []
        change_count = 0
        
        # Crear diccionario para acceso rápido a nuevos resultados
        new_dict = {s.get("id"): s for s in new_sectors if "id" in s}
        
        # Analizar cada sector original
        for original in original_sectors:
            sector_id = original.get("id")
            if not sector_id or sector_id not in new_dict:
                continue
            
            new_sector = new_dict[sector_id]
            
            # Determinar preferencia original
            original_preference = self._determine_preference(original["diferencial"])
            
            # Determinar nueva preferencia
            new_preference = self._determine_preference(new_sector["diferencial"])
            
            # Si hay cambio en la preferencia
            if original_preference != new_preference:
                change_count += 1
                changed_sectors.append({
                    "id": sector_id,
                    "region": original.get("region", ""),
                    "preferencia_original": original_preference,
                    "preferencia_nueva": new_preference,
                    "diferencial_original": original["diferencial"],
                    "diferencial_nuevo": new_sector["diferencial"]
                })
        
        # Calcular porcentaje de cambio
        change_percentage = (change_count / len(original_sectors)) * 100 if original_sectors else 0
        
        return {
            "changed_sectors": changed_sectors,
            "change_count": change_count,
            "change_percentage": change_percentage
        }
    
    def _determine_preference(self, differential: float) -> str:
        """
        Determina la preferencia de puerto basada en el diferencial.
        
        Args:
            differential: Diferencial de costo (costoTimbues - costoLima)
            
        Returns:
            Preferencia de puerto ("Timbúes", "Lima" o "Indiferente")
        """
        if differential < -self.threshold:
            return "Timbúes"
        elif differential > self.threshold:
            return "Lima"
        else:
            return "Indiferente"
    
    def _generate_scenarios(self, variables: Dict) -> List[Dict]:
        """
        Genera todas las combinaciones posibles de escenarios.
        
        Args:
            variables: Diccionario de variables y sus valores posibles
            
        Returns:
            Lista de escenarios
        """
        # Si no hay variables, devolver lista vacía
        if not variables:
            return []
        
        # Inicializar con el primer escenario vacío
        scenarios = [{}]
        
        # Por cada variable
        for var_name, var_values in variables.items():
            # Escenarios temporales con la nueva variable
            new_scenarios = []
            
            # Para cada escenario actual
            for scenario in scenarios:
                # Para cada valor de la variable
                for value in var_values:
                    # Crear un nuevo escenario con este valor
                    new_scenario = scenario.copy()
                    new_scenario[var_name] = value
                    new_scenarios.append(new_scenario)
            
            # Actualizar la lista de escenarios
            scenarios = new_scenarios
        
        return scenarios
    
    def _recalculate_company_with_scenario(self, company: Dict, calculate_costs_fn: Union[callable, Dict], scenario: Dict) -> Dict:
        """
        Recalcula la recomendación para una empresa con un escenario específico.
        
        Args:
            company: Datos de la empresa
            calculate_costs_fn: Función o definición de API para recálculo
            scenario: Definición del escenario
            
        Returns:
            Nueva recomendación
        """
        # Clonar empresa para no modificar la original
        new_company = copy.deepcopy(company)
        
        # Si calculate_costs_fn es una función, llamarla directamente
        if callable(calculate_costs_fn):
            return calculate_costs_fn(new_company, scenario)
        
        # Simulamos el recálculo
        variable = list(scenario.keys())[0] if scenario else ""
        value = scenario.get(variable) if variable else 0
        
        # Ajustamos los costos según el escenario
        if variable == "flete_terrestre":
            factor = value / 0.043  # Relativo al valor por defecto
            new_company["costoTimbues"] = self._adjust_cost_component(new_company.get("costoTimbues", 0), "terrestre", factor)
            new_company["costoLima"] = self._adjust_cost_component(new_company.get("costoLima", 0), "terrestre", factor)
        
        elif variable == "flete_maritimo_factor":
            new_company["costoTimbues"] = self._adjust_cost_component(new_company.get("costoTimbues", 0), "maritimo", value)
            new_company["costoLima"] = self._adjust_cost_component(new_company.get("costoLima", 0), "maritimo", value)
        
        # Recalcular diferencial
        diferencial = new_company["costoTimbues"] - new_company["costoLima"]
        new_company["diferencial"] = diferencial
        
        # Determinar puerto óptimo
        if diferencial < 0:
            new_company["puertoOptimo"] = "Timbúes"
        else:
            new_company["puertoOptimo"] = "Lima"
        
        # Calcular ahorro anual
        volumen = new_company.get("volumenAnual", 0)
        new_company["ahorroAnual"] = abs(diferencial) * volumen
        
        return new_company
    
    def _generate_sensitivity_analysis(self, sensitivity_results: Dict, sectors: List[Dict]) -> Dict:
        """
        Genera un análisis detallado de los resultados de sensibilidad.
        
        Args:
            sensitivity_results: Resultados del análisis de sensibilidad
            sectors: Sectores originales
            
        Returns:
            Análisis detallado
        """
        # Identificar parámetros más y menos sensibles
        parameters = []
        for param_name, param_data in sensitivity_results.items():
            parameters.append({
                "parametro": param_name,
                "cambios": param_data["porcentaje_cambios"]
            })
        
        # Ordenar por porcentaje de cambios (descendente)
        parameters.sort(key=lambda x: x["cambios"], reverse=True)
        
        # Seleccionar los 2 más sensibles y los 2 menos sensibles
        params_mas_sensibles = parameters[:2] if len(parameters) >= 2 else parameters
        params_menos_sensibles = parameters[-2:] if len(parameters) >= 2 else []
        
        # Generar comentario general
        comentario_general = ""
        if parameters and parameters[0]["cambios"] > 30:
            comentario_general = "El modelo muestra alta sensibilidad a cambios en algunos parámetros, " + \
                               "lo que sugiere que pequeñas variaciones en costos podrían alterar " + \
                               "significativamente las recomendaciones para ciertos sectores."
        else:
            comentario_general = "El modelo muestra estabilidad frente a variaciones en los parámetros, " + \
                               "lo que sugiere que las recomendaciones son robustas y confiables " + \
                               "incluso ante cambios moderados en los costos."
        
        return {
            "parametrosMasSensibles": params_mas_sensibles,
            "parametrosMenosSensibles": params_menos_sensibles,
            "comentarioGeneral": comentario_general
        }
    
    def _generate_robustness_summary(self, robustness_results: Dict) -> Dict:
        """
        Genera un resumen de la evaluación de robustez.
        
        Args:
            robustness_results: Resultados de robustez por empresa
            
        Returns:
            Resumen general
        """
        total_companies = len(robustness_results)
        if total_companies == 0:
            return {
                "total_empresas": 0,
                "nivel_robustez": {
                    "alta": 0,
                    "media": 0,
                    "baja": 0
                },
                "porcentaje_robustez": {
                    "alta": 0,
                    "media": 0,
                    "baja": 0
                },
                "comentario": "No hay datos suficientes para evaluar la robustez."
            }
        
        # Contar empresas por nivel de robustez
        high_robustness = 0
        medium_robustness = 0
        low_robustness = 0
        
        for company_data in robustness_results.values():
            if company_data["nivel_robustez"] == "Alta":
                high_robustness += 1
            elif company_data["nivel_robustez"] == "Media":
                medium_robustness += 1
            else:
                low_robustness += 1
        
        # Calcular porcentajes
        pct_high = (high_robustness / total_companies) * 100
        pct_medium = (medium_robustness / total_companies) * 100
        pct_low = (low_robustness / total_companies) * 100
        
        # Generar comentario
        comment = ""
        if pct_high >= 70:
            comment = "La mayoría de las recomendaciones muestran alta robustez, lo que indica que " + \
                     "las decisiones serían estables frente a variaciones en los parámetros analizados."
        elif pct_high + pct_medium >= 70:
            comment = "La mayoría de las recomendaciones muestran robustez media-alta, lo que sugiere que " + \
                     "las decisiones serían moderadamente estables frente a variaciones en los parámetros analizados. " + \
                     "Se recomienda mayor análisis para empresas con robustez baja."
        else:
            comment = "Un porcentaje importante de recomendaciones muestra baja robustez, lo que sugiere que " + \
                     "las decisiones podrían cambiar significativamente frente a variaciones en los parámetros analizados. " + \
                     "Se recomienda un análisis detallado caso por caso antes de tomar decisiones."
        
        return {
            "total_empresas": total_companies,
            "nivel_robustez": {
                "alta": high_robustness,
                "media": medium_robustness,
                "baja": low_robustness
            },
            "porcentaje_robustez": {
                "alta": pct_high,
                "media": pct_medium,
                "baja": pct_low
            },
            "comentario": comment
        }


# Ejemplo de uso como servidor MCP
if __name__ == "__main__":
    import sys
    import argparse
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    analysis_mcp = SensitivityAnalysisMCP()
    
    @app.route('/mcp/sensitivity', methods=['POST'])
    def handle_mcp_request():
        """Endpoint para recibir solicitudes MCP."""
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
    
    parser = argparse.ArgumentParser(description='Servidor MCP para análisis de sensibilidad')
    parser.add_argument('--host', default='0.0.0.0', help='Host para el servidor Flask')
    parser.add_argument('--port', type=int, default=5003, help='Puerto para el servidor Flask')
    parser.add_argument('--debug', action='store_true', help='Ejecutar en modo debug')
    
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=args.debug)