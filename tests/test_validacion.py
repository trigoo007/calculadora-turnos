#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas unitarias para el módulo de validación.
"""

import os
import sys
import unittest
from datetime import datetime

# Asegurar que podemos importar desde el directorio padre
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos a probar
import validacion
import config

class TestValidacion(unittest.TestCase):
    """Pruebas para el módulo de validación."""
    
    def setUp(self):
        """Configuración de las pruebas."""
        self.procedimientos_prueba = [
            "RX de Tórax",
            "TAC de Cerebro",
            "TAC Tórax-Abdomen-Pelvis",
            "TAC de Cuello, Tórax y Abdomen",
            "TAC TX/ABD/PEL",
            "TAC Craneo-Cuello-Torax",
            "TAC Cerebro-Cuello-Torax",
            "Ecografía Abdominal",
            "TAC de Tórax",
            "RX de Columna Lumbar"
        ]
        
        self.salas_prueba = [
            "SCA01",
            "SJ02",
            "SJ-TAC",
            "HOS01",
            "PROC02",
            "OTRO"
        ]
        
        self.fechas_prueba = [
            "01-ene-2025",
            "01/01/2025",
            "2025-01-01",
            "01-01-2025",
            "fecha inválida"
        ]
    
    def test_validar_procedimiento(self):
        """Prueba la validación de procedimientos."""
        # Procedimiento RX
        resultado = validacion.validar_procedimiento("RX de Tórax")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "RX")
        self.assertEqual(resultado["subtipo"], "NORMAL")
        
        # Procedimiento TAC normal
        resultado = validacion.validar_procedimiento("TAC de Cerebro")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "TAC")
        self.assertEqual(resultado["subtipo"], "NORMAL")
        
        # Procedimiento TAC doble
        resultado = validacion.validar_procedimiento("TAC Tórax-Abdomen")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "TAC")
        self.assertEqual(resultado["subtipo"], "DOBLE")
        
        # Procedimiento TAC triple
        resultado = validacion.validar_procedimiento("TAC Cerebro-Cuello-Torax")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "TAC")
        self.assertEqual(resultado["subtipo"], "TRIPLE")
        
        # Otro tipo de procedimiento
        resultado = validacion.validar_procedimiento("Ecografía Abdominal")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "OTRO")
        self.assertEqual(resultado["subtipo"], "DESCONOCIDO")
        
        # Procedimiento vacío
        resultado = validacion.validar_procedimiento("")
        self.assertFalse(resultado["valido"])
        
        # Procedimiento None
        resultado = validacion.validar_procedimiento(None)
        self.assertFalse(resultado["valido"])
    
    def test_validar_sala(self):
        """Prueba la validación de salas."""
        # Sala SCA
        resultado = validacion.validar_sala("SCA01")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "SCA")
        
        # Sala SJ
        resultado = validacion.validar_sala("SJ02")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "SJ")
        
        # Sala SJ-TAC
        resultado = validacion.validar_sala("SJ-TAC")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "SJ")
        self.assertEqual(resultado["subtipo"], "TAC")
        
        # Sala HOS
        resultado = validacion.validar_sala("HOS01")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "HOS")
        
        # Otra sala
        resultado = validacion.validar_sala("OTRO")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["tipo"], "OTRO")
        
        # Sala vacía
        resultado = validacion.validar_sala("")
        self.assertFalse(resultado["valido"])
        
        # Sala None
        resultado = validacion.validar_sala(None)
        self.assertFalse(resultado["valido"])
    
    def test_validar_fecha(self):
        """Prueba la validación de fechas."""
        # Formato dd-mmm-yyyy
        resultado = validacion.validar_fecha("01-ene-2025")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["fecha_normalizada"], "01-Jan-2025")
        
        # Formato dd/mm/yyyy
        resultado = validacion.validar_fecha("01/01/2025")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["fecha_normalizada"], "01-Jan-2025")
        
        # Formato yyyy-mm-dd
        resultado = validacion.validar_fecha("2025-01-01")
        self.assertTrue(resultado["valido"])
        self.assertEqual(resultado["fecha_normalizada"], "01-Jan-2025")
        
        # Fecha inválida
        resultado = validacion.validar_fecha("fecha inválida")
        self.assertFalse(resultado["valido"])
        
        # Fecha vacía
        resultado = validacion.validar_fecha("")
        self.assertFalse(resultado["valido"])
        
        # Fecha None
        resultado = validacion.validar_fecha(None)
        self.assertFalse(resultado["valido"])
    
    def test_validar_configuracion(self):
        """Prueba la validación de configuración."""
        # Configuración válida
        config_valida = {
            "TARIFAS": {
                "TARIFA_HORA": 55000,
                "TARIFA_RX": 5300,
                "TARIFA_TAC": 42400,
                "TARIFA_TAC_DOBLE": 84800,
                "TARIFA_TAC_TRIPLE": 127200
            },
            "HORARIOS_TURNO": {
                "LUNES_JUEVES": {"inicio": "18:00", "fin": "08:00", "duracion": 14},
                "VIERNES": {"inicio": "18:00", "fin": "09:00", "duracion": 15},
                "SABADO": {"inicio": "09:00", "fin": "09:00", "duracion": 24},
                "DOMINGO": {"inicio": "09:00", "fin": "08:00", "duracion": 23}
            },
            "PHI2": {
                "HOST": "localhost",
                "PUERTO": 11434,
                "MODELO": "phi:latest",
                "TEMPERATURE": 0.1,
                "TOP_P": 0.95
            },
            "OUTPUT": {
                "PREFIJO_ARCHIVO": "Turnos_",
                "FORMATO_FECHA": "%d-%m-%Y",
                "FORMATOS_PERMITIDOS": ["xlsx", "csv", "json", "txt"]
            }
        }
        
        exito, mensaje = validacion.validar_configuracion(config_valida)
        self.assertTrue(exito)
        
        # Configuración sin tarifas
        config_sin_tarifas = config_valida.copy()
        del config_sin_tarifas["TARIFAS"]
        
        exito, mensaje = validacion.validar_configuracion(config_sin_tarifas)
        self.assertFalse(exito)
        
        # Configuración con tarifas incompletas
        config_tarifas_incompletas = config_valida.copy()
        config_tarifas_incompletas["TARIFAS"] = {
            "TARIFA_HORA": 55000,
            "TARIFA_RX": 5300
        }
        
        exito, mensaje = validacion.validar_configuracion(config_tarifas_incompletas)
        self.assertFalse(exito)
        
        # Configuración sin horarios de turno
        config_sin_horarios = config_valida.copy()
        del config_sin_horarios["HORARIOS_TURNO"]
        
        exito, mensaje = validacion.validar_configuracion(config_sin_horarios)
        self.assertFalse(exito)
    
    def test_validar_csv(self):
        """Prueba la validación de archivos CSV."""
        # No podemos probar directamente esta función sin archivos de prueba,
        # así que verificamos el comportamiento con parámetros inválidos
        
        # Archivo que no existe
        exito, mensaje = validacion.validar_csv("/ruta/inexistente.csv")
        self.assertFalse(exito)
        
        # Archivo con extensión incorrecta
        archivo_temp = os.path.join(config.TEMP_DIR, "archivo_temporal.txt")
        with open(archivo_temp, 'w') as f:
            f.write("Este no es un CSV")
        
        exito, mensaje = validacion.validar_csv(archivo_temp)
        self.assertFalse(exito)
        
        # Limpiar
        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)

if __name__ == '__main__':
    unittest.main()