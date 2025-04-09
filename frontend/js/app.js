/**
 * Aplicación Puerto Lima
 * Lógica JavaScript para la interfaz web
 */

// Configuración global
const API_URL = 'http://localhost:8000/api';
const TIMBUES_COORDS = [-32.667918, -60.729970]; // [lat, lng]
const LIMA_COORDS = [-12.052100, -77.114300]; // [lat, lng]

// Variables globales
let map;
let originMarker;
let resultsData;

// DOM Elements
const routeForm = document.getElementById('routeForm');
const selectLocation = document.getElementById('selectLocation');
const isContainerSwitch = document.getElementById('isContainer');
const containerCountGroup = document.getElementById('containerCountGroup');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultsSection = document.getElementById('resultados');
const downloadReportBtn = document.getElementById('downloadReportBtn');

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initEventListeners();
});

/**
 * Inicializar el mapa de Leaflet
 */
function initMap() {
    // Crear mapa centrado en Sudamérica
    map = L.map('map').setView([-20, -65], 4);
    
    // Añadir capa base de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Añadir marcadores para los puertos
    const timbuesMarker = L.marker(TIMBUES_COORDS)
        .addTo(map)
        .bindPopup('<b>Puerto Timbúes</b><br>Argentina')
        .bindTooltip('Puerto Timbúes');
    
    const limaMarker = L.marker(LIMA_COORDS)
        .addTo(map)
        .bindPopup('<b>Puerto Lima</b><br>Perú')
        .bindTooltip('Puerto Lima');
    
    // Permitir hacer clic en el mapa para seleccionar ubicación de origen
    map.on('click', function(e) {
        setOriginCoordinates(e.latlng.lat, e.latlng.lng);
        updateOriginMarker(e.latlng.lat, e.latlng.lng);
    });
}

/**
 * Inicializar todos los event listeners
 */
function initEventListeners() {
    // Formulario de cálculo
    routeForm.addEventListener('submit', handleRouteFormSubmit);
    
    // Selector de ubicaciones predefinidas
    selectLocation.addEventListener('change', handleLocationSelect);
    
    // Mostrar/ocultar campo de número de contenedores
    isContainerSwitch.addEventListener('change', () => {
        containerCountGroup.style.display = isContainerSwitch.checked ? 'block' : 'none';
    });
    
    // Botón para descargar reporte
    downloadReportBtn.addEventListener('click', handleReportDownload);
    
    // Validación adicional para formulario
    document.getElementById('tonnage').addEventListener('input', function() {
        if (this.value < 0) this.value = 0;
    });
    
    document.getElementById('containerCount').addEventListener('input', function() {
        if (this.value < 0) this.value = 0;
    });
}

/**
 * Manejar envío del formulario de cálculo
 */
async function handleRouteFormSubmit(e) {
    e.preventDefault();
    
    try {
        // Validación básica
        const originName = document.getElementById('originName').value;
        const originLat = parseFloat(document.getElementById('originLat').value);
        const originLon = parseFloat(document.getElementById('originLon').value);
        const tonnage = parseFloat(document.getElementById('tonnage').value);
        
        if (!originName || isNaN(originLat) || isNaN(originLon) || isNaN(tonnage) || tonnage <= 0) {
            alert('Por favor complete todos los campos requeridos correctamente.');
            return;
        }
        
        // Preparar datos para la API
        const isContainer = isContainerSwitch.checked;
        const containerCount = isContainer ? parseInt(document.getElementById('containerCount').value) : 0;
        
        if (isContainer && (!containerCount || containerCount <= 0)) {
            alert('Por favor ingrese un número válido de contenedores.');
            return;
        }
        
        // Mostrar overlay de carga
        loadingOverlay.style.display = 'flex';
        
        // Llamar a la API
        const response = await calculateRoutes(originName, originLat, originLon, tonnage, isContainer, containerCount);
        
        // Guardar datos para uso posterior
        resultsData = response;
        
        // Procesar y mostrar resultados
        displayResults(response);
        
        // Actualizar el mapa con la información de rutas
        updateMapWithRoutes(response);
        
        // Ocultar overlay de carga
        loadingOverlay.style.display = 'none';
        
        // Mostrar sección de resultados
        resultsSection.style.display = 'block';
        
        // Scroll a resultados
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error en el cálculo:', error);
        alert('Hubo un error al procesar su solicitud. Por favor intente nuevamente.');
        loadingOverlay.style.display = 'none';
    }
}

/**
 * Manejar selección de ubicación predefinida
 */
function handleLocationSelect() {
    const selectedValue = selectLocation.value;
    
    if (selectedValue) {
        const [lat, lon, name] = selectedValue.split(',');
        document.getElementById('originName').value = name;
        
        setOriginCoordinates(parseFloat(lat), parseFloat(lon));
        updateOriginMarker(parseFloat(lat), parseFloat(lon));
    }
}

/**
 * Actualizar campos de coordenadas con valores nuevos
 */
function setOriginCoordinates(lat, lon) {
    document.getElementById('originLat').value = lat.toFixed(6);
    document.getElementById('originLon').value = lon.toFixed(6);
}

/**
 * Actualizar el marcador de origen en el mapa
 */
function updateOriginMarker(lat, lon) {
    // Remover marcador anterior si existe
    if (originMarker) {
        map.removeLayer(originMarker);
    }
    
    // Crear nuevo marcador
    originMarker = L.marker([lat, lon], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(map);
    
    // Añadir popup y tooltip
    const name = document.getElementById('originName').value || 'Origen seleccionado';
    originMarker.bindPopup(`<b>Origen:</b> ${name}<br>Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`);
    originMarker.bindTooltip(name);
    
    // Centrar el mapa en la nueva ubicación
    map.setView([lat, lon], 5);
}

/**
 * Llamar a la API para calcular rutas y costos
 */
async function calculateRoutes(originName, originLat, originLon, tonnage, isContainer, containerCount) {
    try {
        const response = await fetch(`${API_URL}/route/calcular`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origen_nombre: originName,
                origen_lat: originLat,
                origen_lon: originLon,
                toneladas: tonnage,
                es_contenedor: isContainer,
                contenedores: containerCount
            })
        });
        
        if (!response.ok) {
            throw new Error(`Error en la respuesta: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error al conectar con la API:', error);
        throw error;
    }
}

/**
 * Mostrar resultados en la interfaz
 */
function displayResults(data) {
    if (data.status !== 'success') {
        alert('Error al procesar los resultados: ' + (data.mensaje || 'Error desconocido'));
        return;
    }
    
    // Obtener datos de costos y comparaciones
    const { costos, graficos } = data;
    const { timbues, lima, comparacion } = costos;
    
    // Actualizar resumen
    document.getElementById('optimalPort').textContent = comparacion.puerto_optimo.charAt(0).toUpperCase() + comparacion.puerto_optimo.slice(1);
    document.getElementById('savingsAmount').textContent = `$${formatNumber(comparacion.diferencia_absoluta)}`;
    document.getElementById('savingsPercentage').textContent = `${formatNumber(comparacion.diferencia_porcentual)}%`;
    document.getElementById('resultOrigin').textContent = document.getElementById('originName').value;
    document.getElementById('resultTonnage').textContent = formatNumber(parseFloat(document.getElementById('tonnage').value));
    
    // Actualizar tabla de costos
    document.getElementById('costLandTimbues').textContent = `$${formatNumber(timbues.desglose.flete_terrestre)}`;
    document.getElementById('costLandLima').textContent = `$${formatNumber(lima.desglose.flete_terrestre)}`;
    document.getElementById('costSeaTimbues').textContent = `$${formatNumber(timbues.desglose.flete_maritimo)}`;
    document.getElementById('costSeaLima').textContent = `$${formatNumber(lima.desglose.flete_maritimo)}`;
    document.getElementById('costFixedTimbues').textContent = `$${formatNumber(timbues.desglose.costos_fijos)}`;
    document.getElementById('costFixedLima').textContent = `$${formatNumber(lima.desglose.costos_fijos)}`;
    document.getElementById('costTotalTimbues').textContent = `$${formatNumber(timbues.costo_total)}`;
    document.getElementById('costTotalLima').textContent = `$${formatNumber(lima.costo_total)}`;
    document.getElementById('costUnitTimbues').textContent = `$${formatNumber(timbues.costo_unitario)}`;
    document.getElementById('costUnitLima').textContent = `$${formatNumber(lima.costo_unitario)}`;
    
    // Mostrar gráficos
    if (graficos.comparacion) {
        document.getElementById('costComparison').innerHTML = `
            <img src="data:image/png;base64,${graficos.comparacion}" alt="Comparación de costos">
        `;
    }
    
    if (graficos.desglose_timbues) {
        document.getElementById('timbuesCostBreakdown').innerHTML = `
            <img src="data:image/png;base64,${graficos.desglose_timbues}" alt="Desglose costos Timbúes">
        `;
    }
    
    if (graficos.desglose_lima) {
        document.getElementById('limaCostBreakdown').innerHTML = `
            <img src="data:image/png;base64,${graficos.desglose_lima}" alt="Desglose costos Lima">
        `;
    }
}

/**
 * Actualizar el mapa con las rutas calculadas
 */
function updateMapWithRoutes(data) {
    if (data.status !== 'success' || !data.rutas) {
        return;
    }
    
    // Limpiar rutas anteriores
    map.eachLayer(layer => {
        if (layer instanceof L.Polyline) {
            map.removeLayer(layer);
        }
    });
    
    // Obtener datos de las rutas
    const { timbues, lima } = data.rutas;
    const originLat = parseFloat(document.getElementById('originLat').value);
    const originLon = parseFloat(document.getElementById('originLon').value);
    
    // Si hay un mapa HTML completo, usarlo en lugar de dibujar rutas manualmente
    if (data.graficos && data.graficos.mapa) {
        // Crear un iframe y mostrar el mapa
        const mapIframe = document.createElement('iframe');
        mapIframe.style.width = '100%';
        mapIframe.style.height = '400px';
        mapIframe.style.border = 'none';
        mapIframe.srcdoc = data.graficos.mapa;
        
        // Reemplazar el mapa actual con el iframe
        const mapContainer = document.getElementById('map');
        mapContainer.innerHTML = '';
        mapContainer.appendChild(mapIframe);
        
        return;
    }
    
    // Dibujar ruta a Timbúes
    if (timbues && timbues.geometry) {
        drawRoute(timbues.geometry, '#1e88e5', `Ruta a Timbúes: ${timbues.distance.toFixed(1)} km`);
    } else {
        // Si no hay geometría, dibujar línea recta
        drawStraightLine([originLat, originLon], TIMBUES_COORDS, '#1e88e5', `Ruta a Timbúes (aproximada)`);
    }
    
    // Dibujar ruta a Lima
    if (lima && lima.geometry) {
        drawRoute(lima.geometry, '#e53935', `Ruta a Lima: ${lima.distance.toFixed(1)} km`);
    } else {
        // Si no hay geometría, dibujar línea recta
        drawStraightLine([originLat, originLon], LIMA_COORDS, '#e53935', `Ruta a Lima (aproximada)`);
    }
    
    // Ajustar vista para mostrar todas las rutas
    const bounds = L.latLngBounds([
        [originLat, originLon],
        TIMBUES_COORDS,
        LIMA_COORDS
    ]);
    map.fitBounds(bounds, { padding: [50, 50] });
}

/**
 * Dibujar ruta en el mapa a partir de geometría
 */
function drawRoute(geometry, color, tooltip) {
    L.polyline(geometry, {
        color: color,
        weight: 4,
        opacity: 0.7
    })
    .addTo(map)
    .bindTooltip(tooltip);
}

/**
 * Dibujar línea recta entre dos puntos
 */
function drawStraightLine(start, end, color, tooltip) {
    L.polyline([start, end], {
        color: color,
        weight: 3,
        opacity: 0.5,
        dashArray: '5, 10'
    })
    .addTo(map)
    .bindTooltip(tooltip);
}

/**
 * Generar y descargar reporte PDF
 */
async function handleReportDownload(e) {
    e.preventDefault();
    
    if (!resultsData || resultsData.status !== 'success') {
        alert('No hay resultados disponibles para generar el reporte.');
        return;
    }
    
    try {
        // Mostrar overlay de carga
        loadingOverlay.style.display = 'flex';
        
        // Recopilar datos para el reporte
        const originName = document.getElementById('originName').value;
        const originLat = parseFloat(document.getElementById('originLat').value);
        const originLon = parseFloat(document.getElementById('originLon').value);
        const tonnage = parseFloat(document.getElementById('tonnage').value);
        const isContainer = isContainerSwitch.checked;
        const containerCount = isContainer ? parseInt(document.getElementById('containerCount').value) : 0;
        
        // Llamar a la API para generar el reporte
        const response = await fetch(`${API_URL}/route/reporte`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origen_nombre: originName,
                origen_lat: originLat,
                origen_lon: originLon,
                toneladas: tonnage,
                es_contenedor: isContainer,
                contenedores: containerCount
            })
        });
        
        if (!response.ok) {
            throw new Error(`Error en la respuesta: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status !== 'success' || !data.pdf_base64) {
            throw new Error('No se pudo generar el reporte PDF.');
        }
        
        // Descargar el PDF
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${data.pdf_base64}`;
        link.download = data.filename || `reporte_${originName.replace(/\s+/g, '_')}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Ocultar overlay de carga
        loadingOverlay.style.display = 'none';
        
    } catch (error) {
        console.error('Error al generar reporte:', error);
        alert('Hubo un error al generar el reporte. Por favor intente nuevamente.');
        loadingOverlay.style.display = 'none';
    }
}

/**
 * Formatear número con separadores de miles y decimales
 */
function formatNumber(number) {
    return number.toLocaleString('es-AR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}