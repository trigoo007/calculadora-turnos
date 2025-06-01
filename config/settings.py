"""
Configuración centralizada para la aplicación Calculadora de Turnos.

Este archivo contiene todas las configuraciones, rutas y constantes
utilizadas en toda la aplicación.
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios principales
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "output"
KNOWLEDGE_DIR = BASE_DIR / "config" / "knowledge"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuración de la base de datos
DATABASE_CONFIG = {
    "path": DATA_DIR / "calculadora_turnos.db",
    "backup_path": DATA_DIR / "calculadora_turnos_backup.db",
    "timeout": 30,
    "check_same_thread": False
}

# Configuración del asistente AI
AI_CONFIG = {
    "model_name": "microsoft/phi-2",
    "max_length": 2048,
    "temperature": 0.7,
    "top_p": 0.95,
    "cache_dir": BASE_DIR / ".cache" / "models",
    "device": "cpu"  # Cambiar a "cuda" si hay GPU disponible
}

# Configuración de procesamiento de datos
PROCESSING_CONFIG = {
    "batch_size": 1000,
    "encoding": "utf-8",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M:%S",
    "datetime_format": "%Y-%m-%d %H:%M:%S"
}

# Configuración de la interfaz de usuario
UI_CONFIG = {
    "title": "Calculadora de Turnos - Sistema de Gestión",
    "page_icon": "🏥",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "theme": {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#262730"
    }
}

# Configuración de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "calculadora_turnos.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Configuración de tipos de exámenes
EXAM_TYPES = {
    "TAC": {
        "simple": ["TAC", "TOMOGRAFIA"],
        "doble": ["TAC DOBLE", "TAC DUPLA", "DOBLE TAC"],
        "triple": ["TAC TRIPLE", "TRIPLE TAC"]
    },
    "RX": {
        "simple": ["RX", "RADIOGRAFIA", "RAYOS X"],
        "especial": ["RX CONTRASTADA", "RX CON CONTRASTE"]
    },
    "ECO": {
        "simple": ["ECO", "ECOGRAFIA", "ULTRASONIDO"],
        "doppler": ["ECO DOPPLER", "DOPPLER"]
    },
    "RM": {
        "simple": ["RM", "RESONANCIA", "RESONANCIA MAGNETICA"],
        "contraste": ["RM CON CONTRASTE", "RESONANCIA CON GADOLINIO"]
    }
}

# Configuración de salas y centros
CENTERS = {
    "SCA": {
        "name": "San Carlos de Apoquindo",
        "code": "SCA",
        "salas": ["SALA 1", "SALA 2", "SALA 3", "SALA 4"]
    },
    "SJ": {
        "name": "San Joaquín",
        "code": "SJ",
        "salas": ["SALA A", "SALA B", "SALA C"]
    }
}

# Configuración de tiempos estimados (en minutos)
TIME_ESTIMATES = {
    "TAC": {
        "simple": 15,
        "doble": 30,
        "triple": 45,
        "preparacion": 5,
        "limpieza": 5
    },
    "RX": {
        "simple": 10,
        "especial": 20,
        "preparacion": 2,
        "limpieza": 3
    },
    "ECO": {
        "simple": 20,
        "doppler": 30,
        "preparacion": 5,
        "limpieza": 5
    },
    "RM": {
        "simple": 45,
        "contraste": 60,
        "preparacion": 10,
        "limpieza": 10
    }
}

# Configuración de validación
VALIDATION_RULES = {
    "min_exam_duration": 5,  # minutos
    "max_exam_duration": 120,  # minutos
    "max_exams_per_day": 100,
    "required_fields": ["fecha", "hora", "paciente", "procedimiento", "sala"],
    "date_range_days": 365  # Rango máximo de días para procesar
}

# Configuración de exportación
EXPORT_CONFIG = {
    "csv": {
        "encoding": "utf-8",
        "delimiter": ",",
        "quotechar": '"',
        "date_format": "%Y-%m-%d"
    },
    "excel": {
        "engine": "openpyxl",
        "date_format": "YYYY-MM-DD",
        "header_style": {
            "font": {"bold": True},
            "fill": {"color": "D3D3D3"}
        }
    },
    "pdf": {
        "page_size": "A4",
        "margin": 1,
        "font_family": "Helvetica"
    }
}

# Configuración de correo electrónico
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "use_tls": True,
    "sender": os.getenv("EMAIL_SENDER", ""),
    "template_path": BASE_DIR / "templates" / "email"
}

# Configuración de Docker
DOCKER_CONFIG = {
    "image_name": "calculadora-turnos",
    "container_name": "calculadora-turnos-app",
    "port": int(os.getenv("APP_PORT", "8501")),
    "environment": os.getenv("ENVIRONMENT", "production")
}

# Variables de entorno
ENV_VARS = {
    "DEBUG": os.getenv("DEBUG", "False").lower() == "true",
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    "DATABASE_URL": os.getenv("DATABASE_URL", str(DATABASE_CONFIG["path"])),
    "SECRET_KEY": os.getenv("SECRET_KEY", "your-secret-key-here"),
    "API_KEY": os.getenv("API_KEY", "")
}

# Configuración de caché
CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,  # segundos
    "max_size": 1000,  # número máximo de elementos en caché
    "cache_dir": BASE_DIR / ".cache"
}

# Crear directorio de caché si no existe
CACHE_CONFIG["cache_dir"].mkdir(parents=True, exist_ok=True)

# Configuración de respaldo
BACKUP_CONFIG = {
    "enabled": True,
    "interval": "daily",  # daily, weekly, monthly
    "retention_days": 30,
    "backup_dir": BASE_DIR / "backups",
    "compress": True
}

# Crear directorio de respaldo si no existe
BACKUP_CONFIG["backup_dir"].mkdir(parents=True, exist_ok=True)

def get_config() -> Dict[str, Any]:
    """Retorna toda la configuración como un diccionario."""
    return {
        "base_dir": str(BASE_DIR),
        "database": DATABASE_CONFIG,
        "ai": AI_CONFIG,
        "processing": PROCESSING_CONFIG,
        "ui": UI_CONFIG,
        "logging": LOGGING_CONFIG,
        "exam_types": EXAM_TYPES,
        "centers": CENTERS,
        "time_estimates": TIME_ESTIMATES,
        "validation": VALIDATION_RULES,
        "export": EXPORT_CONFIG,
        "email": EMAIL_CONFIG,
        "docker": DOCKER_CONFIG,
        "env": ENV_VARS,
        "cache": CACHE_CONFIG,
        "backup": BACKUP_CONFIG
    }

def validate_config():
    """Valida que la configuración sea correcta."""
    errors = []
    
    # Validar que los directorios existan
    for dir_path in [DATA_DIR, KNOWLEDGE_DIR]:
        if not dir_path.exists():
            errors.append(f"Directorio no encontrado: {dir_path}")
    
    # Validar archivos de conocimiento
    knowledge_files = ["procedimientos.json", "salas.json", 
                      "patrones_tac_doble.json", "patrones_tac_triple.json"]
    for file_name in knowledge_files:
        file_path = KNOWLEDGE_DIR / file_name
        if not file_path.exists():
            errors.append(f"Archivo de conocimiento no encontrado: {file_path}")
    
    # Validar configuración de AI
    if AI_CONFIG["device"] == "cuda":
        try:
            import torch
            if not torch.cuda.is_available():
                errors.append("GPU no disponible pero configurada en AI_CONFIG")
        except ImportError:
            errors.append("PyTorch no instalado pero GPU configurada")
    
    if errors:
        raise ValueError(f"Errores de configuración: {'; '.join(errors)}")
    
    return True

# Validar configuración al importar
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"Advertencia de configuración: {e}") 