#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo Avanzado de Autenticación para Streamlit
-----------------------------------------------
Proporciona funcionalidades de autenticación segura para proteger
el acceso a la aplicación Calculadora de Turnos en Radiología.

Características:
- Autenticación basada en roles
- Almacenamiento seguro de credenciales con salts
- Integración con variables de entorno
- Detección automática de Cloudflare Access
- Gestión de usuarios desde la interfaz
"""

import os
import sys
import json
import hashlib
import secrets
import logging
import streamlit as st
from functools import wraps
from typing import Dict, Callable, Any, Optional, Tuple, List, Union

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("autenticacion_streamlit")

# Constantes
DEFAULT_USERS_FILE = "usuarios.json"
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASSWORD = "calculadora2025"
DEFAULT_SECRET_KEY = "calculadora_secret_key_2025"


def obtener_clave_secreta() -> str:
    """
    Obtiene la clave secreta desde las variables de entorno o usa la predeterminada.
    
    Returns:
        Clave secreta para cifrado.
    """
    return os.environ.get("AUTH_SECRET_KEY", DEFAULT_SECRET_KEY)


def generar_salt() -> str:
    """
    Genera un salt aleatorio para el hashing de contraseñas.
    
    Returns:
        String hexadecimal con el salt.
    """
    return secrets.token_hex(16)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashea una contraseña con un salt (generado o proporcionado).
    
    Args:
        password: Contraseña en texto plano.
        salt: Salt para el hash (opcional, se genera si no se proporciona).
        
    Returns:
        Tupla (hash_password, salt).
    """
    if salt is None:
        salt = generar_salt()
    
    # Obtener la clave secreta
    secret_key = obtener_clave_secreta()
    
    # Crear un hash con salt y clave secreta
    salted_password = f"{password}{salt}{secret_key}"
    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    
    return password_hash, salt


def verificar_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verifica si una contraseña coincide con un hash almacenado.
    
    Args:
        password: Contraseña en texto plano para verificar.
        stored_hash: Hash almacenado para comparar.
        salt: Salt usado para el hash original.
        
    Returns:
        True si la contraseña coincide, False en caso contrario.
    """
    # Calcular el hash con el mismo salt
    calculated_hash, _ = hash_password(password, salt)
    
    return calculated_hash == stored_hash


def cargar_usuarios() -> Dict[str, Dict[str, str]]:
    """
    Carga los usuarios desde el archivo JSON.
    
    Returns:
        Diccionario con usuarios y sus datos (hash, salt, rol).
    """
    # Determinar la ruta del archivo de usuarios
    script_dir = os.path.dirname(os.path.abspath(__file__))
    usuarios_file = os.path.join(script_dir, DEFAULT_USERS_FILE)
    
    # Si no existe el archivo, crear uno con usuario admin por defecto
    if not os.path.exists(usuarios_file):
        # Crear hash para admin
        admin_hash, admin_salt = hash_password(DEFAULT_ADMIN_PASSWORD)
        
        usuarios_default = {
            DEFAULT_ADMIN_USER: {
                "hash": admin_hash,
                "salt": admin_salt,
                "role": "admin"
            }
        }
        
        try:
            with open(usuarios_file, "w") as f:
                json.dump(usuarios_default, f, indent=2)
            logger.info(f"Archivo de usuarios creado con usuario admin predeterminado")
        except Exception as e:
            logger.error(f"No se pudo crear el archivo de usuarios: {e}")
            return usuarios_default
    
    # Cargar usuarios del archivo
    try:
        with open(usuarios_file, "r") as f:
            usuarios = json.load(f)
            
            # Actualizar formato antiguo si es necesario
            usuarios_actualizados = {}
            for usuario, datos in usuarios.items():
                # Si el valor es solo un hash (formato antiguo)
                if isinstance(datos, str):
                    logger.info(f"Actualizando usuario {usuario} al nuevo formato")
                    salt = generar_salt()
                    usuarios_actualizados[usuario] = {
                        "hash": datos,  # Mantener el hash antiguo
                        "salt": salt,   # Añadir salt nuevo
                        "role": "admin" if usuario == DEFAULT_ADMIN_USER else "user"
                    }
                else:
                    usuarios_actualizados[usuario] = datos
            
            # Si se actualizaron formatos, guardar cambios
            if len(usuarios_actualizados) != len(usuarios):
                with open(usuarios_file, "w") as f:
                    json.dump(usuarios_actualizados, f, indent=2)
                logger.info("Archivo de usuarios actualizado al nuevo formato")
            
            return usuarios_actualizados
            
    except Exception as e:
        logger.error(f"Error al cargar usuarios: {e}")
        # Crear usuario admin predeterminado en caso de error
        admin_hash, admin_salt = hash_password(DEFAULT_ADMIN_PASSWORD)
        return {
            DEFAULT_ADMIN_USER: {
                "hash": admin_hash,
                "salt": admin_salt,
                "role": "admin"
            }
        }


def guardar_usuarios(usuarios: Dict[str, Dict[str, str]]) -> bool:
    """
    Guarda el diccionario de usuarios en el archivo JSON.
    
    Args:
        usuarios: Diccionario con usuarios y sus datos.
        
    Returns:
        True si se guardó correctamente, False en caso contrario.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    usuarios_file = os.path.join(script_dir, DEFAULT_USERS_FILE)
    
    try:
        with open(usuarios_file, "w") as f:
            json.dump(usuarios, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error al guardar usuarios: {e}")
        return False


def autenticacion_requerida() -> bool:
    """
    Determina si se requiere autenticación basada en las variables de entorno.
    
    Lógica:
    - Si CLOUDFLARE_TUNNEL_TOKEN está presente y FORCE_STREAMLIT_AUTH no está activo,
      asumimos que se usa Cloudflare Access para autenticación.
    - En caso contrario, usar la variable ENABLE_AUTHENTICATION.
    
    Returns:
        True si se requiere autenticación local, False en caso contrario.
    """
    # Verificar si hay túnel Cloudflare configurado
    cloudflare_tunnel = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN", "")
    
    # Verificar si se fuerza la autenticación de Streamlit
    force_auth = os.environ.get("FORCE_STREAMLIT_AUTH", "").lower() in ("true", "1", "yes")
    
    # Verificar si la autenticación está habilitada
    enable_auth = os.environ.get("ENABLE_AUTHENTICATION", "").lower() in ("true", "1", "yes")
    
    # Si hay túnel Cloudflare y no se fuerza la autenticación local, no requerir autenticación
    if cloudflare_tunnel and not force_auth:
        logger.info("Detectado túnel Cloudflare. Se asume autenticación externa.")
        return False
    
    # En otros casos, usar la configuración de ENABLE_AUTHENTICATION
    logger.info(f"Autenticación local {'habilitada' if enable_auth else 'deshabilitada'}")
    return enable_auth


def requiere_autenticacion(func: Callable) -> Callable:
    """
    Decorador que requiere autenticación para acceder a una página.
    
    Args:
        func: Función a decorar.
        
    Returns:
        Función decorada que verifica autenticación.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar si la autenticación está habilitada
        if not autenticacion_requerida():
            return func(*args, **kwargs)
        
        # Verificar si el usuario ya está autenticado
        if not st.session_state.get("autenticado", False):
            st.warning("Por favor, inicie sesión para acceder a esta página")
            return mostrar_login()
        
        # Usuario autenticado, ejecutar la función original
        return func(*args, **kwargs)
    
    return wrapper


def requiere_rol(roles: Union[str, List[str]]) -> Callable:
    """
    Decorador que requiere un rol específico para acceder a una página.
    
    Args:
        roles: Un rol o lista de roles permitidos.
        
    Returns:
        Función decorada que verifica el rol del usuario.
    """
    if isinstance(roles, str):
        roles = [roles]
        
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Primero verificar autenticación
            if not autenticacion_requerida():
                return func(*args, **kwargs)
            
            if not st.session_state.get("autenticado", False):
                st.warning("Por favor, inicie sesión para acceder a esta página")
                return mostrar_login()
            
            # Verificar rol
            if st.session_state.get("rol", "") not in roles:
                st.error(f"No tiene permisos para acceder a esta página. Se requiere rol: {', '.join(roles)}")
                return
            
            # Usuario con rol adecuado, ejecutar la función original
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def mostrar_login() -> None:
    """
    Muestra la pantalla de inicio de sesión.
    """
    st.title("Calculadora de Turnos en Radiología")
    st.subheader("Inicio de sesión")
    
    usuarios = cargar_usuarios()
    
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar sesión")
    
    if submit:
        if usuario in usuarios:
            # Obtener datos del usuario
            user_data = usuarios[usuario]
            
            # Verificar formato nuevo vs antiguo
            if isinstance(user_data, dict) and "hash" in user_data and "salt" in user_data:
                # Formato nuevo con salt
                if verificar_password(password, user_data["hash"], user_data["salt"]):
                    st.session_state.autenticado = True
                    st.session_state.usuario = usuario
                    st.session_state.rol = user_data.get("role", "user")
                    st.success("Inicio de sesión exitoso")
                    st.experimental_rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                # Formato antiguo (solo hash)
                st.error("Formato de usuario obsoleto. Contacte al administrador.")
        else:
            st.error("Usuario o contraseña incorrectos")


@requiere_rol("admin")
def mostrar_admin() -> None:
    """
    Muestra la pantalla de administración de usuarios.
    Solo accesible para el rol de administrador.
    """
    st.title("Administración de Usuarios")
    
    usuarios = cargar_usuarios()
    
    # Listar usuarios existentes
    st.subheader("Usuarios existentes")
    
    # Crear tabla de usuarios
    data = []
    for usuario, user_data in usuarios.items():
        if isinstance(user_data, dict):
            rol = user_data.get("role", "user")
        else:
            rol = "user"  # Formato antiguo
        
        data.append({"Usuario": usuario, "Rol": rol})
    
    if data:
        st.table(data)
    else:
        st.info("No hay usuarios registrados.")
    
    # Formulario para añadir usuario
    st.subheader("Añadir nuevo usuario")
    with st.form("add_user_form"):
        nuevo_usuario = st.text_input("Nombre de usuario")
        nueva_password = st.text_input("Contraseña", type="password")
        confirmar_password = st.text_input("Confirmar contraseña", type="password")
        rol = st.selectbox("Rol", ["user", "admin"])
        submit_add = st.form_submit_button("Añadir usuario")
    
    if submit_add:
        if not nuevo_usuario:
            st.error("El nombre de usuario no puede estar vacío")
        elif nuevo_usuario in usuarios:
            st.error("El usuario ya existe")
        elif nueva_password != confirmar_password:
            st.error("Las contraseñas no coinciden")
        elif len(nueva_password) < 8:
            st.error("La contraseña debe tener al menos 8 caracteres")
        else:
            # Añadir nuevo usuario
            password_hash, salt = hash_password(nueva_password)
            
            usuarios[nuevo_usuario] = {
                "hash": password_hash,
                "salt": salt,
                "role": rol
            }
            
            if guardar_usuarios(usuarios):
                st.success(f"Usuario {nuevo_usuario} añadido correctamente")
                st.experimental_rerun()
            else:
                st.error("Error al añadir usuario")
    
    # Formulario para eliminar usuario
    if len(usuarios) > 1:  # Evitar eliminar todos los usuarios
        st.subheader("Eliminar usuario")
        with st.form("delete_user_form"):
            # Filtrar para no mostrar el usuario actual
            usuarios_eliminables = [u for u in usuarios.keys() if u != st.session_state.get("usuario")]
            
            if usuarios_eliminables:
                usuario_a_eliminar = st.selectbox("Seleccione usuario", usuarios_eliminables)
                submit_delete = st.form_submit_button("Eliminar usuario")
                
                if submit_delete:
                    # No permitir eliminar el último admin
                    admins = [u for u, data in usuarios.items() if isinstance(data, dict) and data.get("role") == "admin"]
                    
                    user_data = usuarios.get(usuario_a_eliminar, {})
                    is_admin = isinstance(user_data, dict) and user_data.get("role") == "admin"
                    
                    if is_admin and len(admins) <= 1:
                        st.error("No se puede eliminar el último usuario administrador")
                    else:
                        del usuarios[usuario_a_eliminar]
                        if guardar_usuarios(usuarios):
                            st.success(f"Usuario {usuario_a_eliminar} eliminado correctamente")
                            st.experimental_rerun()
                        else:
                            st.error("Error al eliminar usuario")
            else:
                st.info("No hay usuarios que se puedan eliminar")
    
    # Formulario para cambiar contraseña
    st.subheader("Cambiar contraseña")
    with st.form("change_password_form"):
        usuario_cambio = st.selectbox("Usuario", list(usuarios.keys()))
        nueva_password_cambio = st.text_input("Nueva contraseña", type="password", key="nueva_pw")
        confirmar_password_cambio = st.text_input("Confirmar nueva contraseña", type="password", key="conf_pw")
        submit_change = st.form_submit_button("Cambiar contraseña")
        
        if submit_change:
            if nueva_password_cambio != confirmar_password_cambio:
                st.error("Las contraseñas no coinciden")
            elif len(nueva_password_cambio) < 8:
                st.error("La contraseña debe tener al menos 8 caracteres")
            else:
                # Actualizar contraseña
                password_hash, salt = hash_password(nueva_password_cambio)
                
                # Preservar el rol actual
                if isinstance(usuarios[usuario_cambio], dict):
                    rol_actual = usuarios[usuario_cambio].get("role", "user")
                else:
                    rol_actual = "user"  # Formato antiguo
                
                usuarios[usuario_cambio] = {
                    "hash": password_hash,
                    "salt": salt,
                    "role": rol_actual
                }
                
                if guardar_usuarios(usuarios):
                    st.success(f"Contraseña de {usuario_cambio} actualizada correctamente")
                else:
                    st.error("Error al actualizar contraseña")


def cerrar_sesion() -> None:
    """
    Cierra la sesión del usuario actual.
    """
    if "autenticado" in st.session_state:
        del st.session_state.autenticado
    
    if "usuario" in st.session_state:
        del st.session_state.usuario
    
    if "rol" in st.session_state:
        del st.session_state.rol
    
    st.experimental_rerun()


def mostrar_boton_cerrar_sesion() -> None:
    """
    Muestra un botón para cerrar sesión en la barra lateral.
    """
    if autenticacion_requerida() and st.session_state.get("autenticado", False):
        with st.sidebar:
            st.text(f"Sesión iniciada como: {st.session_state.get('usuario', 'Desconocido')}")
            st.text(f"Rol: {st.session_state.get('rol', 'Desconocido')}")
            if st.button("Cerrar sesión"):
                cerrar_sesion()


def mostrar_link_admin() -> None:
    """
    Muestra un enlace para acceder a la administración si el usuario es admin.
    """
    if autenticacion_requerida() and st.session_state.get("rol") == "admin":
        with st.sidebar:
            if st.button("Administrar usuarios"):
                st.session_state.mostrar_admin = True


def inicializar_autenticacion() -> bool:
    """
    Inicializa el sistema de autenticación.
    Debe ser llamado al inicio de la aplicación.
    
    Returns:
        True si la autenticación está activa y es necesario mostrar login,
        False si no se requiere autenticación o el usuario ya está autenticado.
    """
    # Verificar si la autenticación es necesaria
    auth_required = autenticacion_requerida()
    
    # Si no se requiere autenticación, no hacer nada
    if not auth_required:
        return False
    
    # Verificar inicialización previa
    if not st.session_state.get("auth_initialized", False):
        st.session_state.auth_initialized = True
        st.session_state.mostrar_admin = False
    
    # Mostrar botón de cerrar sesión y link de admin si corresponde
    mostrar_boton_cerrar_sesion()
    mostrar_link_admin()
    
    # Si el usuario solicitó ver la página de admin
    if st.session_state.get("mostrar_admin", False):
        mostrar_admin()
        return True
    
    # Si el usuario no está autenticado, mostrar login
    if not st.session_state.get("autenticado", False):
        mostrar_login()
        return True
    
    # Usuario autenticado, permitir acceso normal
    return False


# Función principal para probar el módulo
if __name__ == "__main__":
    st.set_page_config(page_title="Sistema de Autenticación", layout="wide")
    
    # Para pruebas, forzar la autenticación
    os.environ["ENABLE_AUTHENTICATION"] = "true"
    
    if not inicializar_autenticacion():
        # Si no estamos en la pantalla de autenticación, mostrar la aplicación normal
        st.title("Aplicación Protegida")
        st.success("¡Bienvenido a la aplicación protegida!")
        st.write(f"Has iniciado sesión como: {st.session_state.get('usuario', 'Desconocido')}")
        st.write(f"Tu rol es: {st.session_state.get('rol', 'Desconocido')}")
        
        # Ejemplo de contenido solo para administradores
        if st.session_state.get("rol") == "admin":
            st.subheader("Sección de Administración")
            st.info("Este contenido solo es visible para administradores.")
        
        # Ejemplo de uso del decorador de autenticación
        @requiere_autenticacion
        def funcion_protegida():
            st.subheader("Función Protegida")
            st.write("Esta función solo se ejecuta si el usuario está autenticado.")
        
        funcion_protegida()
        
        # Ejemplo de uso del decorador de rol
        @requiere_rol("admin")
        def funcion_solo_admin():
            st.subheader("Función Solo Admin")
            st.write("Esta función solo se ejecuta si el usuario tiene rol de administrador.")
        
        funcion_solo_admin()