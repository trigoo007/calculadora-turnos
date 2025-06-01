"""
Módulo de cálculo de turnos para la Calculadora de Turnos.

Este módulo contiene la lógica principal para calcular turnos,
horas trabajadas y honorarios basados en los exámenes procesados.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from collections import defaultdict

from config.settings import TIME_ESTIMATES, CENTERS

logger = logging.getLogger(__name__)


class TurnoCalculator:
    """Calculadora principal para turnos médicos."""
    
    def __init__(self):
        """Inicializa la calculadora con las tarifas y configuraciones."""
        # Tarifas por hora y por tipo de examen
        self.TARIFA_HORA = 55000
        self.TARIFA_RX = 5300
        self.TARIFA_TAC = 42300
        self.TARIFA_TAC_DOBLE = 84600    # 2x TARIFA_TAC
        self.TARIFA_TAC_TRIPLE = 126900  # 3x TARIFA_TAC
        
        # Horarios de turnos por día
        self.HORARIOS_TURNO = {
            0: {'inicio': 18, 'fin': 8, 'horas': 14},   # Lunes
            1: {'inicio': 18, 'fin': 8, 'horas': 14},   # Martes
            2: {'inicio': 18, 'fin': 8, 'horas': 14},   # Miércoles
            3: {'inicio': 18, 'fin': 8, 'horas': 14},   # Jueves
            4: {'inicio': 18, 'fin': 9, 'horas': 15},   # Viernes
            5: {'inicio': 9, 'fin': 9, 'horas': 24},    # Sábado
            6: {'inicio': 9, 'fin': 8, 'horas': 23}     # Domingo
        }
        
        # Inicializar resultados
        self.reset_results()
    
    def reset_results(self):
        """Reinicia los resultados del cálculo."""
        self.resultado_economico = {
            'horas_trabajadas': 0,
            'rx_count': 0,
            'tac_count': 0,
            'tac_doble_count': 0,
            'tac_triple_count': 0,
            'rx_total': 0,
            'tac_total': 0,
            'tac_doble_total': 0,
            'tac_triple_total': 0,
            'honorarios_hora': 0,
            'total': 0,
            'detalle_turnos': []
        }
    
    def calcular_turnos(self, df: pd.DataFrame, 
                       fechas_especificas: Optional[List[datetime]] = None) -> Dict[str, any]:
        """
        Calcula los turnos y honorarios basados en los exámenes.
        
        Args:
            df: DataFrame con los exámenes clasificados
            fechas_especificas: Lista opcional de fechas específicas de turnos
            
        Returns:
            Diccionario con los resultados del cálculo
        """
        self.reset_results()
        
        # Validar DataFrame
        if not self._validar_dataframe(df):
            raise ValueError("DataFrame no contiene las columnas necesarias")
        
        # Filtrar exámenes por centro si es necesario
        df_filtrado = self._filtrar_por_centros(df)
        
        # Asignar exámenes a turnos
        df_con_turnos = self._asignar_a_turnos(df_filtrado, fechas_especificas)
        
        # Calcular horas trabajadas
        self._calcular_horas_trabajadas(df_con_turnos, fechas_especificas)
        
        # Contabilizar exámenes
        self._contabilizar_examenes(df_con_turnos)
        
        # Calcular honorarios
        self._calcular_honorarios()
        
        return self.resultado_economico
    
    def _validar_dataframe(self, df: pd.DataFrame) -> bool:
        """Valida que el DataFrame tenga las columnas necesarias."""
        columnas_requeridas = ['fecha', 'procedimiento', 'sala']
        columnas_opcionales = ['tipo', 'is_tac_double', 'is_tac_triple']
        
        # Verificar columnas requeridas
        for col in columnas_requeridas:
            if col not in df.columns:
                logger.error(f"Columna requerida '{col}' no encontrada en DataFrame")
                return False
        
        # Agregar columnas opcionales si no existen
        for col in columnas_opcionales:
            if col not in df.columns:
                df[col] = False if 'is_' in col else 'OTRO'
        
        return True
    
    def _filtrar_por_centros(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra los exámenes por centros válidos (SCA y SJ)."""
        # Crear máscara para centros válidos
        mask_centros = pd.Series(False, index=df.index)
        
        for center_code in ['SCA', 'SJ']:
            mask_centros |= df['sala'].str.startswith(center_code)
        
        # Excluir salas que comienzan con HOS
        mask_excluir = ~df['sala'].str.startswith('HOS')
        
        df_filtrado = df[mask_centros & mask_excluir].copy()
        
        logger.info(f"Filtrados {len(df_filtrado)} exámenes de {len(df)} totales")
        
        return df_filtrado
    
    def _asignar_a_turnos(self, df: pd.DataFrame, 
                         fechas_especificas: Optional[List[datetime]] = None) -> pd.DataFrame:
        """
        Asigna cada examen a un turno específico.
        
        Args:
            df: DataFrame con los exámenes
            fechas_especificas: Lista opcional de fechas de turnos
            
        Returns:
            DataFrame con columna adicional 'turno_asignado'
        """
        df = df.copy()
        df['turno_asignado'] = None
        
        if fechas_especificas:
            # Asignar basándose en fechas específicas
            for fecha_turno in fechas_especificas:
                # Determinar rango de fechas que cubre este turno
                inicio, fin = self._obtener_rango_turno(fecha_turno)
                
                # Asignar exámenes en este rango al turno
                mask = (df['fecha'] >= inicio) & (df['fecha'] < fin)
                df.loc[mask, 'turno_asignado'] = fecha_turno.date()
        else:
            # Asignar automáticamente basándose en las fechas de los exámenes
            for idx, row in df.iterrows():
                fecha_examen = pd.to_datetime(row['fecha'])
                turno = self._determinar_turno_automatico(fecha_examen)
                df.at[idx, 'turno_asignado'] = turno
        
        # Filtrar solo exámenes con turno asignado
        df_con_turnos = df[df['turno_asignado'].notna()].copy()
        
        logger.info(f"Asignados {len(df_con_turnos)} exámenes a turnos")
        
        return df_con_turnos
    
    def _obtener_rango_turno(self, fecha_turno: datetime) -> Tuple[datetime, datetime]:
        """
        Obtiene el rango de fechas que cubre un turno.
        
        Args:
            fecha_turno: Fecha del turno
            
        Returns:
            Tupla (inicio, fin) del rango del turno
        """
        dia_semana = fecha_turno.weekday()
        horario = self.HORARIOS_TURNO[dia_semana]
        
        # Calcular inicio del turno
        inicio = fecha_turno.replace(hour=horario['inicio'], minute=0, second=0)
        
        # Calcular fin del turno
        if horario['fin'] < horario['inicio']:
            # El turno termina al día siguiente
            fin = (fecha_turno + timedelta(days=1)).replace(
                hour=horario['fin'], minute=0, second=0
            )
        else:
            # El turno termina el mismo día
            fin = fecha_turno.replace(hour=horario['fin'], minute=0, second=0)
        
        return inicio, fin
    
    def _determinar_turno_automatico(self, fecha_examen: datetime) -> datetime.date:
        """
        Determina automáticamente a qué turno pertenece un examen.
        
        Args:
            fecha_examen: Fecha y hora del examen
            
        Returns:
            Fecha del turno al que pertenece
        """
        hora_examen = fecha_examen.hour
        dia_semana = fecha_examen.weekday()
        
        # Determinar si el examen pertenece al turno del día anterior
        if hora_examen < 9:  # Antes de las 9 AM
            # Pertenece al turno del día anterior
            return (fecha_examen - timedelta(days=1)).date()
        elif hora_examen >= 18:  # Después de las 6 PM
            # Pertenece al turno del mismo día
            return fecha_examen.date()
        else:
            # Horario diurno - no pertenece a ningún turno nocturno
            return None
    
    def _calcular_horas_trabajadas(self, df: pd.DataFrame, 
                                  fechas_especificas: Optional[List[datetime]] = None):
        """Calcula las horas trabajadas en los turnos."""
        if fechas_especificas:
            # Calcular basándose en fechas específicas
            total_horas = 0
            detalle_turnos = []
            
            for fecha in fechas_especificas:
                dia_semana = fecha.weekday()
                horas = self.HORARIOS_TURNO[dia_semana]['horas']
                total_horas += horas
                
                # Contar exámenes en este turno
                examenes_turno = len(df[df['turno_asignado'] == fecha.date()])
                
                detalle_turnos.append({
                    'fecha': fecha.date(),
                    'dia_semana': fecha.strftime('%A'),
                    'horas': horas,
                    'examenes': examenes_turno
                })
            
            self.resultado_economico['horas_trabajadas'] = total_horas
            self.resultado_economico['detalle_turnos'] = detalle_turnos
        else:
            # Calcular basándose en los turnos únicos encontrados
            turnos_unicos = df['turno_asignado'].unique()
            total_horas = 0
            
            for turno in turnos_unicos:
                if turno is not None:
                    fecha_turno = pd.to_datetime(turno)
                    dia_semana = fecha_turno.weekday()
                    horas = self.HORARIOS_TURNO[dia_semana]['horas']
                    total_horas += horas
            
            self.resultado_economico['horas_trabajadas'] = total_horas
    
    def _contabilizar_examenes(self, df: pd.DataFrame):
        """Contabiliza los exámenes por tipo."""
        # Contar RX
        self.resultado_economico['rx_count'] = len(
            df[df['tipo'] == 'RX']
        )
        
        # Contar TAC simple (no doble ni triple)
        mask_tac_simple = (
            (df['tipo'] == 'TAC') & 
            (~df.get('is_tac_double', False)) & 
            (~df.get('is_tac_triple', False))
        )
        self.resultado_economico['tac_count'] = len(df[mask_tac_simple])
        
        # Contar TAC doble (excluyendo los que son triple)
        mask_tac_doble = (
            df.get('is_tac_double', False) & 
            (~df.get('is_tac_triple', False))
        )
        self.resultado_economico['tac_doble_count'] = len(df[mask_tac_doble])
        
        # Contar TAC triple
        self.resultado_economico['tac_triple_count'] = len(
            df[df.get('is_tac_triple', False)]
        )
        
        logger.info(f"Contabilizados: {self.resultado_economico['rx_count']} RX, "
                   f"{self.resultado_economico['tac_count']} TAC, "
                   f"{self.resultado_economico['tac_doble_count']} TAC doble, "
                   f"{self.resultado_economico['tac_triple_count']} TAC triple")
    
    def _calcular_honorarios(self):
        """Calcula los honorarios totales."""
        # Calcular honorarios por tipo de examen
        self.resultado_economico['rx_total'] = (
            self.resultado_economico['rx_count'] * self.TARIFA_RX
        )
        
        self.resultado_economico['tac_total'] = (
            self.resultado_economico['tac_count'] * self.TARIFA_TAC
        )
        
        self.resultado_economico['tac_doble_total'] = (
            self.resultado_economico['tac_doble_count'] * self.TARIFA_TAC_DOBLE
        )
        
        self.resultado_economico['tac_triple_total'] = (
            self.resultado_economico['tac_triple_count'] * self.TARIFA_TAC_TRIPLE
        )
        
        # Calcular honorarios por horas trabajadas
        self.resultado_economico['honorarios_hora'] = (
            self.resultado_economico['horas_trabajadas'] * self.TARIFA_HORA
        )
        
        # Calcular total general
        self.resultado_economico['total'] = (
            self.resultado_economico['rx_total'] +
            self.resultado_economico['tac_total'] +
            self.resultado_economico['tac_doble_total'] +
            self.resultado_economico['tac_triple_total'] +
            self.resultado_economico['honorarios_hora']
        )
        
        logger.info(f"Total calculado: ${self.resultado_economico['total']:,.0f}")
    
    def generar_resumen_estadistico(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Genera un resumen estadístico de los exámenes.
        
        Args:
            df: DataFrame con los exámenes
            
        Returns:
            Diccionario con estadísticas
        """
        resumen = {
            'total_examenes': len(df),
            'por_tipo': df['tipo'].value_counts().to_dict() if 'tipo' in df.columns else {},
            'por_sala': df['sala'].value_counts().to_dict() if 'sala' in df.columns else {},
            'por_centro': {},
            'examenes_por_dia': {}
        }
        
        # Agrupar por centro
        if 'sala' in df.columns:
            df['centro'] = df['sala'].str[:3]  # Primeros 3 caracteres (SCA, SJ, etc.)
            resumen['por_centro'] = df['centro'].value_counts().to_dict()
        
        # Exámenes por día de la semana
        if 'fecha' in df.columns:
            df['dia_semana'] = pd.to_datetime(df['fecha']).dt.day_name()
            resumen['examenes_por_dia'] = df['dia_semana'].value_counts().to_dict()
        
        return resumen
    
    def estimar_tiempo_total(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Estima el tiempo total requerido para todos los exámenes.
        
        Args:
            df: DataFrame con los exámenes clasificados
            
        Returns:
            Diccionario con tiempos estimados
        """
        tiempo_total = 0
        tiempo_por_tipo = defaultdict(float)
        
        for _, examen in df.iterrows():
            # Obtener tiempo estimado del examen
            if 'estimated_time' in examen:
                tiempo = examen['estimated_time']
            else:
                # Estimar basándose en el tipo
                tipo = examen.get('tipo', 'OTRO')
                tiempo = TIME_ESTIMATES.get(tipo, {}).get('simple', 20)
            
            tiempo_total += tiempo
            tiempo_por_tipo[examen.get('tipo', 'OTRO')] += tiempo
        
        return {
            'tiempo_total_minutos': tiempo_total,
            'tiempo_total_horas': tiempo_total / 60,
            'tiempo_por_tipo': dict(tiempo_por_tipo),
            'promedio_por_examen': tiempo_total / len(df) if len(df) > 0 else 0
        }


# Funciones de utilidad para compatibilidad
def calcular_turnos(df: pd.DataFrame, fechas: Optional[List[datetime]] = None) -> Dict[str, any]:
    """Función de compatibilidad para calcular turnos."""
    calculator = TurnoCalculator()
    return calculator.calcular_turnos(df, fechas)


def calcular_honorarios_totales(resultado_economico: Dict[str, any]) -> float:
    """Función de compatibilidad para obtener el total de honorarios."""
    return resultado_economico.get('total', 0) 