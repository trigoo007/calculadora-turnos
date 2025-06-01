"""
Módulo de procesamiento de datos para la Calculadora de Turnos.

Este módulo maneja la lectura, limpieza y transformación de datos
desde archivos Excel/CSV hacia formatos utilizables por la aplicación.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import logging
from datetime import datetime
import re
import json

from config.settings import (
    PROCESSING_CONFIG, 
    VALIDATION_RULES,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR
)

logger = logging.getLogger(__name__)


class DataProcessor:
    """Clase principal para el procesamiento de datos de turnos."""
    
    def __init__(self):
        self.encoding = PROCESSING_CONFIG["encoding"]
        self.date_format = PROCESSING_CONFIG["date_format"]
        self.datetime_format = PROCESSING_CONFIG["datetime_format"]
        self.batch_size = PROCESSING_CONFIG["batch_size"]
        
    def read_excel(self, file_path: Union[str, Path], sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lee un archivo Excel y retorna un DataFrame.
        
        Args:
            file_path: Ruta al archivo Excel
            sheet_name: Nombre de la hoja a leer (None para la primera)
            
        Returns:
            DataFrame con los datos del Excel
        """
        try:
            file_path = Path(file_path)
            logger.info(f"Leyendo archivo Excel: {file_path}")
            
            # Si no se especifica hoja, leer la primera
            if sheet_name is None:
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            
            logger.info(f"Archivo leído exitosamente. Filas: {len(df)}, Columnas: {len(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"Error al leer archivo Excel: {e}")
            raise
    
    def read_csv(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Lee un archivo CSV y retorna un DataFrame.
        
        Args:
            file_path: Ruta al archivo CSV
            **kwargs: Argumentos adicionales para pd.read_csv
            
        Returns:
            DataFrame con los datos del CSV
        """
        try:
            file_path = Path(file_path)
            logger.info(f"Leyendo archivo CSV: {file_path}")
            
            # Configuración por defecto
            default_kwargs = {
                'encoding': self.encoding,
                'sep': ',',
                'parse_dates': True
            }
            default_kwargs.update(kwargs)
            
            df = pd.read_csv(file_path, **default_kwargs)
            logger.info(f"Archivo leído exitosamente. Filas: {len(df)}, Columnas: {len(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"Error al leer archivo CSV: {e}")
            raise
    
    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detecta automáticamente las columnas relevantes en el DataFrame.
        
        Args:
            df: DataFrame a analizar
            
        Returns:
            Diccionario con el mapeo de columnas detectadas
        """
        column_mapping = {}
        
        # Log de columnas disponibles
        logger.info(f"Columnas disponibles en el archivo: {list(df.columns)}")
        
        # MAPEO DIRECTO - Basado en los logs que muestran las columnas reales
        # Buscar primero por coincidencia exacta con los nombres que sabemos que existen
        for col in df.columns:
            col_lower = col.lower()
            
            # PROCEDIMIENTO - Buscar específicamente "Nombre del procedimiento"
            if col == 'Nombre del procedimiento':
                column_mapping['procedimiento'] = col
                logger.info(f"✓ Columna de procedimiento encontrada: '{col}'")
            
            # FECHA - Buscar "Fecha del procedimiento programado"
            elif col == 'Fecha del procedimiento programado':
                column_mapping['fecha'] = col
                logger.info(f"✓ Columna de fecha encontrada: '{col}'")
            
            # HORA
            elif col == 'Hora del procedimiento programado':
                column_mapping['hora'] = col
                logger.info(f"✓ Columna de hora encontrada: '{col}'")
            
            # PACIENTE - Apellidos del paciente
            elif col == 'Apellidos del paciente':
                column_mapping['paciente'] = col
                logger.info(f"✓ Columna de paciente encontrada: '{col}'")
            
            # SALA
            elif col == 'Sala de adquisición':
                column_mapping['sala'] = col
                logger.info(f"✓ Columna de sala encontrada: '{col}'")
        
        # Si no se encontró alguna columna crítica, buscar con patrones más flexibles
        if 'procedimiento' not in column_mapping:
            logger.warning("No se encontró 'Nombre del procedimiento', buscando alternativas...")
            for col in df.columns:
                if 'procedimiento' in col.lower() and 'nombre' in col.lower():
                    column_mapping['procedimiento'] = col
                    logger.info(f"Columna de procedimiento encontrada (búsqueda flexible): '{col}'")
                    break
        
        # Log final
        logger.info(f"Columnas detectadas finalmente: {column_mapping}")
        
        # Verificación crítica
        if 'procedimiento' not in column_mapping:
            logger.error("¡ERROR CRÍTICO! No se detectó la columna de procedimientos")
            logger.error("Por favor verifique que el archivo tenga una columna 'Nombre del procedimiento'")
        
        return column_mapping
    
    def clean_data(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Limpia y normaliza los datos del DataFrame.
        
        Args:
            df: DataFrame a limpiar
            column_mapping: Mapeo de columnas
            
        Returns:
            DataFrame limpio
        """
        df_clean = df.copy()
        
        # Renombrar columnas según el mapeo
        rename_dict = {v: k for k, v in column_mapping.items()}
        df_clean = df_clean.rename(columns=rename_dict)
        
        # Eliminar filas completamente vacías
        df_clean = df_clean.dropna(how='all')
        
        # Limpiar espacios en blanco solo en columnas de tipo string/object
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                try:
                    # Convertir a string primero para evitar errores
                    df_clean[col] = df_clean[col].astype(str)
                    # Limpiar espacios
                    df_clean[col] = df_clean[col].str.strip()
                    # Reemplazar 'nan' strings con NaN real
                    df_clean[col] = df_clean[col].replace('nan', np.nan)
                except Exception as e:
                    logger.warning(f"No se pudo limpiar la columna {col}: {e}")
        
        # Convertir fechas
        if 'fecha' in df_clean.columns:
            try:
                # Intentar varios formatos de fecha comunes
                df_clean['fecha'] = pd.to_datetime(df_clean['fecha'], errors='coerce', dayfirst=True)
            except Exception as e:
                logger.warning(f"Error al convertir fechas: {e}")
        
        # Normalizar nombres de procedimientos
        if 'procedimiento' in df_clean.columns:
            try:
                df_clean['procedimiento'] = df_clean['procedimiento'].astype(str).str.upper()
                df_clean['procedimiento'] = df_clean['procedimiento'].str.replace(r'\s+', ' ', regex=True)
            except Exception as e:
                logger.warning(f"Error al normalizar procedimientos: {e}")
        
        # Normalizar salas
        if 'sala' in df_clean.columns:
            try:
                df_clean['sala'] = df_clean['sala'].astype(str).str.upper()
            except Exception as e:
                logger.warning(f"Error al normalizar salas: {e}")
        
        # Normalizar centros
        if 'centro' in df_clean.columns:
            try:
                df_clean['centro'] = self._normalize_center(df_clean['centro'])
            except Exception as e:
                logger.warning(f"Error al normalizar centros: {e}")
        
        # Eliminar duplicados
        df_clean = df_clean.drop_duplicates()
        
        logger.info(f"Datos limpios. Filas resultantes: {len(df_clean)}")
        return df_clean
    
    def _normalize_center(self, center_series: pd.Series) -> pd.Series:
        """Normaliza los nombres de centros médicos."""
        center_mapping = {
            'san carlos': 'SCA',
            'san carlos de apoquindo': 'SCA',
            'sca': 'SCA',
            'san joaquin': 'SJ',
            'san joaquín': 'SJ',
            'sj': 'SJ'
        }
        
        try:
            # Convertir a string y luego a minúsculas
            normalized = center_series.astype(str).str.lower()
            
            for pattern, replacement in center_mapping.items():
                normalized = normalized.str.replace(pattern, replacement, regex=False)
            
            return normalized.str.upper()
        except Exception as e:
            logger.warning(f"Error al normalizar centros: {e}")
            return center_series
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Valida los datos según las reglas de negocio.
        
        Args:
            df: DataFrame a validar
            
        Returns:
            Tupla con (datos_validos, datos_invalidos)
        """
        errors = []
        
        # Verificar campos requeridos
        required_fields = VALIDATION_RULES["required_fields"]
        missing_fields = [field for field in required_fields if field not in df.columns]
        
        if missing_fields:
            logger.warning(f"Campos requeridos faltantes: {missing_fields}")
        
        # Crear máscara de filas válidas
        valid_mask = pd.Series(True, index=df.index)
        
        # Validar que los campos requeridos no estén vacíos
        for field in required_fields:
            if field in df.columns:
                valid_mask &= df[field].notna()
        
        # FILTRO CRÍTICO: Solo incluir exámenes de SCA o SJ
        if 'sala' in df.columns:
            # Convertir a string y buscar SCA o SJ
            sala_str = df['sala'].astype(str).str.upper()
            centro_mask = sala_str.str.contains('SCA|SJ', na=False, regex=True)
            valid_mask &= centro_mask
            
            # Log de cuántos registros se filtran por centro
            registros_sca = sala_str.str.contains('SCA', na=False).sum()
            registros_sj = sala_str.str.contains('SJ', na=False).sum()
            logger.info(f"Filtro de centros: SCA={registros_sca}, SJ={registros_sj}, Otros={len(df) - registros_sca - registros_sj}")
        else:
            logger.warning("No se encontró columna 'sala' para filtrar por centro")
        
        # Validar fechas
        if 'fecha' in df.columns:
            # Verificar rango de fechas
            fecha_min = datetime.now() - pd.Timedelta(days=VALIDATION_RULES["date_range_days"])
            fecha_max = datetime.now() + pd.Timedelta(days=VALIDATION_RULES["date_range_days"])
            valid_mask &= (df['fecha'] >= fecha_min) & (df['fecha'] <= fecha_max)
        
        # Separar datos válidos e inválidos
        df_valid = df[valid_mask].copy()
        df_invalid = df[~valid_mask].copy()
        
        # Agregar columna 'centro' basada en la sala para facilitar el procesamiento posterior
        if 'sala' in df_valid.columns:
            df_valid['centro'] = df_valid['sala'].apply(self._extract_center_from_sala)
        
        logger.info(f"Validación completada. Válidos: {len(df_valid)} (solo SCA/SJ), Inválidos: {len(df_invalid)}")
        
        return df_valid, df_invalid
    
    def _extract_center_from_sala(self, sala: str) -> str:
        """Extrae el centro (SCA o SJ) del nombre de la sala."""
        if pd.isna(sala):
            return 'DESCONOCIDO'
        
        sala_upper = str(sala).upper()
        if 'SCA' in sala_upper:
            return 'SCA'
        elif 'SJ' in sala_upper:
            return 'SJ'
        else:
            return 'OTRO'
    
    def process_file(self, file_path: Union[str, Path], 
                    output_path: Optional[Union[str, Path]] = None) -> Dict[str, any]:
        """
        Procesa un archivo completo de principio a fin.
        
        Args:
            file_path: Ruta al archivo a procesar
            output_path: Ruta donde guardar el archivo procesado
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        file_path = Path(file_path)
        
        # Determinar tipo de archivo y leer
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = self.read_excel(file_path)
        elif file_path.suffix.lower() == '.csv':
            df = self.read_csv(file_path)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_path.suffix}")
        
        # Detectar columnas
        column_mapping = self.detect_columns(df)
        
        # Limpiar datos
        df_clean = self.clean_data(df, column_mapping)
        
        # Validar datos
        df_valid, df_invalid = self.validate_data(df_clean)
        
        # Guardar resultados si se especifica ruta de salida
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_path.suffix.lower() == '.csv':
                df_valid.to_csv(output_path, index=False, encoding=self.encoding)
            else:
                df_valid.to_excel(output_path, index=False, engine='openpyxl')
            
            # Guardar también los registros inválidos si hay
            if len(df_invalid) > 0:
                invalid_path = output_path.parent / f"{output_path.stem}_invalidos{output_path.suffix}"
                if output_path.suffix.lower() == '.csv':
                    df_invalid.to_csv(invalid_path, index=False, encoding=self.encoding)
                else:
                    df_invalid.to_excel(invalid_path, index=False, engine='openpyxl')
        
        # Retornar estadísticas
        stats = {
            'total_rows': len(df),
            'valid_rows': len(df_valid),
            'invalid_rows': len(df_invalid),
            'columns_detected': list(column_mapping.keys()),
            'processing_date': datetime.now().isoformat(),
            'file_name': file_path.name
        }
        
        logger.info(f"Procesamiento completado: {stats}")
        return stats
    
    def batch_process(self, input_dir: Union[str, Path], 
                     output_dir: Union[str, Path]) -> List[Dict[str, any]]:
        """
        Procesa múltiples archivos en lote.
        
        Args:
            input_dir: Directorio con archivos a procesar
            output_dir: Directorio donde guardar archivos procesados
            
        Returns:
            Lista con estadísticas de cada archivo procesado
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        # Buscar archivos Excel y CSV
        files = list(input_dir.glob("*.xlsx")) + \
                list(input_dir.glob("*.xls")) + \
                list(input_dir.glob("*.csv"))
        
        logger.info(f"Encontrados {len(files)} archivos para procesar")
        
        for file_path in files:
            try:
                output_path = output_dir / f"{file_path.stem}_procesado.csv"
                stats = self.process_file(file_path, output_path)
                stats['status'] = 'success'
                results.append(stats)
            except Exception as e:
                logger.error(f"Error procesando {file_path}: {e}")
                results.append({
                    'file_name': file_path.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results


def extract_exam_info(text: str) -> Dict[str, any]:
    """
    Extrae información estructurada de un texto de procedimiento.
    
    Args:
        text: Texto del procedimiento/examen
        
    Returns:
        Diccionario con información extraída
    """
    info = {
        'original': text,
        'tipo': None,
        'region': None,
        'contraste': False,
        'urgente': False
    }
    
    text_lower = text.lower()
    
    # Detectar tipo de examen
    if 'tac' in text_lower or 'tomograf' in text_lower:
        info['tipo'] = 'TAC'
    elif 'rx' in text_lower or 'radiograf' in text_lower:
        info['tipo'] = 'RX'
    elif 'resonancia' in text_lower or ' rm ' in text_lower:
        info['tipo'] = 'RM'
    elif 'eco' in text_lower or 'ultrason' in text_lower:
        info['tipo'] = 'ECO'
    
    # Detectar región anatómica
    regiones = ['cabeza', 'torax', 'abdomen', 'pelvis', 'columna', 
                'extremidad', 'cuello', 'cerebro', 'pulmon']
    for region in regiones:
        if region in text_lower:
            info['region'] = region.upper()
            break
    
    # Detectar si usa contraste
    if 'contraste' in text_lower or 'contrastado' in text_lower:
        info['contraste'] = True
    
    # Detectar si es urgente
    if 'urgente' in text_lower or 'urgencia' in text_lower:
        info['urgente'] = True
    
    return info


def normalize_exam_name(exam_name: str) -> str:
    """
    Normaliza el nombre de un examen para facilitar comparaciones.
    
    Args:
        exam_name: Nombre original del examen
        
    Returns:
        Nombre normalizado
    """
    # Convertir a mayúsculas
    normalized = exam_name.upper()
    
    # Eliminar espacios múltiples
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Eliminar caracteres especiales
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Reemplazar abreviaciones comunes
    replacements = {
        'TAC': 'TOMOGRAFIA COMPUTADA',
        'RX': 'RADIOGRAFIA',
        'RM': 'RESONANCIA MAGNETICA',
        'ECO': 'ECOGRAFIA',
        'US': 'ULTRASONIDO'
    }
    
    for abbr, full in replacements.items():
        if normalized.startswith(abbr + ' '):
            normalized = normalized.replace(abbr + ' ', full + ' ', 1)
    
    return normalized.strip()


# Funciones de utilidad para compatibilidad con código existente
def leer_archivo_excel(ruta: str, hoja: Optional[str] = None) -> pd.DataFrame:
    """Función de compatibilidad para leer archivos Excel."""
    processor = DataProcessor()
    return processor.read_excel(ruta, hoja)


def procesar_archivo(ruta_entrada: str, ruta_salida: str) -> Dict[str, any]:
    """Función de compatibilidad para procesar archivos."""
    processor = DataProcessor()
    return processor.process_file(ruta_entrada, ruta_salida) 