"""
Módulo de clasificación de exámenes médicos.

Este módulo maneja la clasificación, codificación y categorización
de diferentes tipos de exámenes médicos (TAC, RX, RM, etc.).
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from config.settings import EXAM_TYPES, KNOWLEDGE_DIR, TIME_ESTIMATES

logger = logging.getLogger(__name__)


class ExamClassifier:
    """Clasificador principal para exámenes médicos."""
    
    def __init__(self):
        """Inicializa el clasificador cargando los patrones de conocimiento."""
        self.knowledge_dir = Path(KNOWLEDGE_DIR)
        self.exam_types = EXAM_TYPES
        self.time_estimates = TIME_ESTIMATES
        
        # Cargar patrones desde archivos JSON
        self.procedimientos = self._load_json("procedimientos.json")
        self.salas = self._load_json("salas.json")
        self.patrones_tac_doble = self._load_json("patrones_tac_doble.json")
        self.patrones_tac_triple = self._load_json("patrones_tac_triple.json")
        
        # Cache para clasificaciones
        self._classification_cache = {}
        
    def _load_json(self, filename: str) -> Dict:
        """Carga un archivo JSON desde el directorio de conocimiento."""
        file_path = self.knowledge_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Archivo de conocimiento no encontrado: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON {file_path}: {e}")
            return {}
    
    def classify_exam(self, exam_name: str) -> Dict[str, any]:
        """
        Clasifica un examen basándose en su nombre.
        
        Args:
            exam_name: Nombre del examen/procedimiento
            
        Returns:
            Diccionario con la clasificación completa
        """
        # Verificar cache
        if exam_name in self._classification_cache:
            return self._classification_cache[exam_name]
        
        # Normalizar nombre
        exam_name_lower = exam_name.lower()
        
        # Detectar tipo principal
        exam_type = self._detect_exam_type(exam_name_lower)
        
        # Detectar subtipo y características especiales
        subtype = self._detect_subtype(exam_name_lower, exam_type)
        
        # Detectar si es TAC doble o triple
        is_double = self._is_tac_double(exam_name)
        is_triple = self._is_tac_triple(exam_name)
        
        # Detectar región anatómica
        anatomical_region = self._detect_anatomical_region(exam_name_lower)
        
        # Detectar características especiales
        uses_contrast = self._uses_contrast(exam_name_lower)
        is_urgent = self._is_urgent(exam_name_lower)
        
        # Estimar complejidad y tiempo
        complexity = self._estimate_complexity(exam_type, subtype, uses_contrast)
        estimated_time = self._estimate_time(exam_type, subtype, is_double, is_triple)
        
        # Generar código único
        code = self._generate_code(exam_name, exam_type, subtype)
        
        # Determinar sala apropiada
        appropriate_room = self._determine_room(exam_type, complexity)
        
        classification = {
            'original_name': exam_name,
            'type': exam_type,
            'subtype': subtype,
            'code': code,
            'is_tac_double': is_double,
            'is_tac_triple': is_triple,
            'anatomical_region': anatomical_region,
            'uses_contrast': uses_contrast,
            'is_urgent': is_urgent,
            'complexity': complexity,
            'estimated_time': estimated_time,
            'appropriate_room': appropriate_room,
            'classification_date': datetime.now().isoformat()
        }
        
        # Guardar en cache
        self._classification_cache[exam_name] = classification
        
        return classification
    
    def _detect_exam_type(self, exam_name: str) -> str:
        """Detecta el tipo principal de examen."""
        # Revisar cada tipo de examen definido
        for exam_type, patterns in self.exam_types.items():
            for subtype_patterns in patterns.values():
                for pattern in subtype_patterns:
                    if pattern.lower() in exam_name:
                        return exam_type
        
        # Si no se encuentra coincidencia
        return "OTRO"
    
    def _detect_subtype(self, exam_name: str, exam_type: str) -> str:
        """Detecta el subtipo del examen."""
        if exam_type not in self.exam_types:
            return "general"
        
        # Buscar en los patrones del tipo específico
        for subtype, patterns in self.exam_types[exam_type].items():
            for pattern in patterns:
                if pattern.lower() in exam_name:
                    return subtype
        
        return "simple"
    
    def _is_tac_double(self, exam_name: str) -> bool:
        """Determina si es un TAC doble basándose en el número de regiones anatómicas."""
        exam_upper = exam_name.upper()
        
        # Solo es TAC si contiene la palabra TAC
        if 'TAC' not in exam_upper:
            return False
        
        # Contar regiones anatómicas
        regiones = self._contar_regiones_anatomicas(exam_upper)
        
        # Es TAC doble si tiene exactamente 2 regiones
        return regiones == 2
    
    def _is_tac_triple(self, exam_name: str) -> bool:
        """Determina si es un TAC triple basándose en el número de regiones anatómicas."""
        exam_upper = exam_name.upper()
        
        # Solo es TAC si contiene la palabra TAC
        if 'TAC' not in exam_upper:
            return False
        
        # Contar regiones anatómicas
        regiones = self._contar_regiones_anatomicas(exam_upper)
        
        # Es TAC triple si tiene 3 o más regiones
        return regiones >= 3
    
    def _contar_regiones_anatomicas(self, exam_name: str) -> int:
        """Cuenta el número de regiones anatómicas en el nombre del examen."""
        exam_upper = exam_name.upper()
        
        # Primero verificar si tiene "ABDOMEN Y PELVIS" o variantes como una sola región
        abdomen_pelvis_patterns = [
            'ABDOMEN Y PELVIS',
            'ABDOMEN-PELVIS', 
            'ABD/PEL',
            'ABD/PLV',
            'ABDOMINAL Y PELVICO',
            'ABDOMINOPELVICO',
            'ABDOMINOPELVIS'
        ]
        
        # Reemplazar patrones de abdomen-pelvis con un marcador único
        temp_exam = exam_upper
        for pattern in abdomen_pelvis_patterns:
            if pattern in temp_exam:
                temp_exam = temp_exam.replace(pattern, 'ABDOMEN_PELVIS_REGION')
        
        # Lista de regiones anatómicas principales
        regiones_encontradas = set()
        
        # Buscar regiones individuales
        if any(region in temp_exam for region in ['CABEZA', 'CRANEO', 'CEREBRO', 'ENCEFALICO']):
            regiones_encontradas.add('CABEZA')
            
        if any(region in temp_exam for region in ['CUELLO', 'CERVICAL']):
            regiones_encontradas.add('CUELLO')
            
        if any(region in temp_exam for region in ['TORAX', 'TORACICO', 'TX', 'PULMON', 'CARDIACO', 'PECHO']):
            regiones_encontradas.add('TORAX')
            
        # Si encontramos el marcador de abdomen-pelvis, es una región
        if 'ABDOMEN_PELVIS_REGION' in temp_exam:
            regiones_encontradas.add('ABDOMEN_PELVIS')
        else:
            # Si no, buscar abdomen y pelvis por separado
            if any(region in temp_exam for region in ['ABDOMEN', 'ABDOMINAL', 'ABD', 'HEPATICO', 'RENAL']):
                regiones_encontradas.add('ABDOMEN')
                
            if any(region in temp_exam for region in ['PELVIS', 'PELVICO', 'PLV', 'PEL', 'PROSTATA', 'UTERO']):
                regiones_encontradas.add('PELVIS')
        
        if any(region in temp_exam for region in ['COLUMNA', 'VERTEBRAL', 'LUMBAR', 'DORSAL']):
            regiones_encontradas.add('COLUMNA')
            
        if any(region in temp_exam for region in ['EXTREMIDAD', 'BRAZO', 'PIERNA', 'MANO', 'PIE']):
            regiones_encontradas.add('EXTREMIDAD')
        
        return len(regiones_encontradas)
    
    def _detect_anatomical_region(self, exam_name: str) -> Optional[str]:
        """Detecta la región anatómica del examen."""
        regions = {
            'cabeza': ['cabeza', 'craneo', 'cerebro', 'encefalico'],
            'cuello': ['cuello', 'cervical', 'tiroides'],
            'torax': ['torax', 'toracico', 'pulmon', 'cardiaco'],
            'abdomen': ['abdomen', 'abdominal', 'hepatico', 'renal'],
            'pelvis': ['pelvis', 'pelvico', 'prostata', 'utero'],
            'columna': ['columna', 'vertebral', 'lumbar', 'dorsal'],
            'extremidades': ['extremidad', 'brazo', 'pierna', 'mano', 'pie'],
            'cuerpo_completo': ['cuerpo completo', 'total body', 'whole body']
        }
        
        for region, keywords in regions.items():
            for keyword in keywords:
                if keyword in exam_name:
                    return region
        
        return None
    
    def _uses_contrast(self, exam_name: str) -> bool:
        """Determina si el examen usa medio de contraste."""
        contrast_keywords = [
            'contraste', 'contrastado', 'contrastada',
            'gadolinio', 'medio de contraste', 'c/c',
            'con contraste', 'contrast'
        ]
        
        return any(keyword in exam_name for keyword in contrast_keywords)
    
    def _is_urgent(self, exam_name: str) -> bool:
        """Determina si el examen es urgente."""
        urgent_keywords = [
            'urgente', 'urgencia', 'emergencia',
            'stat', 'prioritario', 'inmediato'
        ]
        
        return any(keyword in exam_name for keyword in urgent_keywords)
    
    def _estimate_complexity(self, exam_type: str, subtype: str, uses_contrast: bool) -> int:
        """
        Estima la complejidad del examen (1-5).
        
        Returns:
            Nivel de complejidad del 1 al 5
        """
        # Complejidad base por tipo
        base_complexity = {
            'RX': 1,
            'ECO': 2,
            'TAC': 3,
            'RM': 4,
            'PET': 5,
            'OTRO': 2
        }
        
        complexity = base_complexity.get(exam_type, 2)
        
        # Ajustes por subtipo
        if subtype in ['doble', 'triple', 'especial', 'doppler']:
            complexity += 1
        
        # Ajuste por contraste
        if uses_contrast:
            complexity += 1
        
        # Limitar entre 1 y 5
        return max(1, min(5, complexity))
    
    def _estimate_time(self, exam_type: str, subtype: str, 
                      is_double: bool, is_triple: bool) -> int:
        """
        Estima el tiempo del examen en minutos.
        
        Returns:
            Tiempo estimado en minutos
        """
        # Obtener tiempo base
        if exam_type in self.time_estimates:
            time_config = self.time_estimates[exam_type]
            base_time = time_config.get(subtype, time_config.get('simple', 20))
            prep_time = time_config.get('preparacion', 5)
            cleanup_time = time_config.get('limpieza', 5)
        else:
            base_time = 20
            prep_time = 5
            cleanup_time = 5
        
        # Ajustes para TAC doble y triple
        if is_triple:
            base_time = self.time_estimates.get('TAC', {}).get('triple', 45)
        elif is_double:
            base_time = self.time_estimates.get('TAC', {}).get('doble', 30)
        
        # Tiempo total
        total_time = prep_time + base_time + cleanup_time
        
        return total_time
    
    def _generate_code(self, exam_name: str, exam_type: str, subtype: str) -> str:
        """
        Genera un código único para el examen.
        
        Returns:
            Código único del examen
        """
        # Prefijos por tipo
        type_prefixes = {
            'TAC': 'T',
            'RX': 'R',
            'RM': 'M',
            'ECO': 'E',
            'PET': 'P',
            'OTRO': 'X'
        }
        
        prefix = type_prefixes.get(exam_type, 'X')
        
        # Agregar indicador de subtipo
        if subtype == 'doble':
            prefix += '2'
        elif subtype == 'triple':
            prefix += '3'
        elif subtype == 'contraste':
            prefix += 'C'
        
        # Generar parte única basada en el nombre
        name_parts = re.sub(r'[^a-zA-Z0-9]', '', exam_name.upper())[:3]
        
        # Timestamp para unicidad
        timestamp = datetime.now().strftime('%H%M%S')[-4:]
        
        return f"{prefix}{name_parts}{timestamp}"
    
    def _determine_room(self, exam_type: str, complexity: int) -> str:
        """
        Determina la sala apropiada para el examen.
        
        Returns:
            Identificador de la sala apropiada
        """
        # Esta es una lógica simplificada
        # En producción, esto debería considerar disponibilidad real
        if exam_type == 'TAC':
            return 'SALA_TAC_1' if complexity <= 3 else 'SALA_TAC_2'
        elif exam_type == 'RX':
            return 'SALA_RX_1'
        elif exam_type == 'RM':
            return 'SALA_RM_1'
        elif exam_type == 'ECO':
            return 'SALA_ECO_1'
        else:
            return 'SALA_GENERAL_1'
    
    def get_exam_info(self, code: str) -> Optional[Dict]:
        """
        Obtiene información de un examen por su código.
        
        Args:
            code: Código del examen
            
        Returns:
            Información del examen o None si no se encuentra
        """
        # Buscar en cache por código
        for exam_name, classification in self._classification_cache.items():
            if classification.get('code') == code:
                return classification
        
        return None
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Obtiene estadísticas de las clasificaciones realizadas.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self._classification_cache:
            return {
                'total_exams': 0,
                'by_type': {},
                'by_complexity': {},
                'average_time': 0
            }
        
        # Calcular estadísticas
        total_exams = len(self._classification_cache)
        by_type = {}
        by_complexity = {i: 0 for i in range(1, 6)}
        total_time = 0
        
        for classification in self._classification_cache.values():
            # Por tipo
            exam_type = classification['type']
            by_type[exam_type] = by_type.get(exam_type, 0) + 1
            
            # Por complejidad
            complexity = classification['complexity']
            by_complexity[complexity] += 1
            
            # Tiempo total
            total_time += classification['estimated_time']
        
        return {
            'total_exams': total_exams,
            'by_type': by_type,
            'by_complexity': by_complexity,
            'average_time': total_time / total_exams if total_exams > 0 else 0,
            'cache_size': len(self._classification_cache)
        }
    
    def clear_cache(self):
        """Limpia el cache de clasificaciones."""
        self._classification_cache.clear()
        logger.info("Cache de clasificaciones limpiado")


# Funciones de utilidad para compatibilidad
def clasificar_examen(nombre_examen: str) -> Dict[str, any]:
    """Función de compatibilidad para clasificar un examen."""
    classifier = ExamClassifier()
    return classifier.classify_exam(nombre_examen)


def es_tac_doble(nombre_examen: str) -> bool:
    """Función de compatibilidad para detectar TAC doble."""
    classifier = ExamClassifier()
    classification = classifier.classify_exam(nombre_examen)
    return classification.get('is_tac_double', False)


def es_tac_triple(nombre_examen: str) -> bool:
    """Función de compatibilidad para detectar TAC triple."""
    classifier = ExamClassifier()
    classification = classifier.classify_exam(nombre_examen)
    return classification.get('is_tac_triple', False) 