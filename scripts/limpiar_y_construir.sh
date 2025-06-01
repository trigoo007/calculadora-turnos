#!/bin/bash
# Script para limpiar directorios y construir la aplicación

echo "Limpiando directorios de build y dist..."
rm -rf dist/
rm -rf build/
rm -f CalculadoraTurnos.spec

# Ejecutar el script de construcción
echo "Ejecutando script de construcción..."
bash crear_aplicacion_escritorio_sin_icono.sh