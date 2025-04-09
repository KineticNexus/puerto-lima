"""
Archivo principal de la aplicación.

Este archivo configura la aplicación FastAPI y define las rutas principales.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from api.endpoints.route import router as route_router

# Crear la aplicación FastAPI
app = FastAPI(
    title="Puerto Lima API",
    description="API para el sistema de comparación de alternativas de exportación",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, esto debería ser más restrictivo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers de la API
app.include_router(route_router, prefix="/api/route", tags=["rutas"])

# Manejo de errores personalizados
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Manejar errores de validación de solicitudes."""
    return JSONResponse(
        status_code=422,
        content={"status": "error", "detail": str(exc)},
    )

# Endpoint de prueba
@app.get("/")
async def root():
    """Endpoint de prueba para verificar que la API está funcionando."""
    return {
        "status": "success",
        "message": "API de Puerto Lima funcionando correctamente",
        "version": "1.0.0"
    }

# Montar archivos estáticos si existe la carpeta
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Punto de entrada para ejecutar con uvicorn directamente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)