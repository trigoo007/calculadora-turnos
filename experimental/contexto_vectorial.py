#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Almacenamiento Vectorial para el Proyecto Calculadora de Turnos en Radiología
---------------------------------------------------------------------------------------
Este módulo implementa un sistema de embeddings y almacenamiento vectorial para mantener
el contexto histórico del proyecto, permitiendo recuperar información relevante
según las consultas del usuario.
"""

import os
import uuid
import json
import datetime
import chromadb
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Configuraciones
VECTORSTORE_DIR = os.path.expanduser("~/vectorstore")
COLLECTION_NAME = "radiologia_turnos"
# Modelo recomendado, pero usa un modelo de respaldo si no está disponible
try:
    from sentence_transformers import util
    MODEL_NAME = "sentence-transformers/gte-base"
except ImportError:
    # Si hay problemas con sentence-transformers, usar un modelo más simple
    MODEL_NAME = "all-MiniLM-L6-v2"
MAX_DOCUMENTS = 1000  # Límite para activar resúmenes jerárquicos
MAX_SIZE_MB = 5  # Tamaño máximo en MB para activar resúmenes

class ContextoVectorial:
    """
    Sistema de almacenamiento y recuperación vectorial para el contexto del proyecto.
    Implementa la estrategia RAPTOR (Retrieval Augmented Prompt with Tree Organized Resumes).
    """
    
    def __init__(self, persist_dir: str = VECTORSTORE_DIR, collection_name: str = COLLECTION_NAME):
        """
        Inicializa el sistema de almacenamiento vectorial.
        
        Args:
            persist_dir: Directorio para persistir el almacén vectorial
            collection_name: Nombre de la colección en Chroma
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Crear directorio si no existe
        os.makedirs(persist_dir, exist_ok=True)
        
        # Inicializar cliente Chroma
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Crear o obtener colección
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Colección '{collection_name}' cargada correctamente.")
        except Exception as e:
            # Crear nueva colección si no existe o hay cualquier error
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Contexto histórico de Calculadora de Turnos en Radiología"}
            )
            print(f"Colección '{collection_name}' creada correctamente.")
        
        # Cargar modelo de embeddings
        try:
            self.model = SentenceTransformer(MODEL_NAME)
            print(f"Modelo de embeddings '{MODEL_NAME}' cargado correctamente.")
        except Exception as e:
            print(f"Error al cargar modelo de embeddings: {e}")
            self.model = None
    
    def generar_embedding(self, texto: str) -> List[float]:
        """
        Genera un embedding para el texto dado.
        
        Args:
            texto: Texto para generar embedding
            
        Returns:
            Lista de flotantes representando el embedding
        """
        if self.model is None:
            # Sistema de respaldo usando hashing simple si no hay modelo disponible
            print("Advertencia: Usando sistema de respaldo de embeddings simple.")
            import hashlib
            import struct
            import math
            
            # Crear un hash del texto
            hash_obj = hashlib.md5(texto.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            # Convertir el hash a un vector de 16 flotantes (128/8 = 16)
            embedding = []
            for i in range(0, 16, 2):
                val = struct.unpack('<Q', hash_bytes[i:i+8])[0]
                # Normalizar a valores entre -1 y 1
                embedding.append(math.sin(val % 10000))
                embedding.append(math.cos(val % 10000))
            
            return embedding
        
        # Generar embedding con el modelo
        try:
            embedding = self.model.encode(texto)
            return embedding.tolist()
        except Exception as e:
            print(f"Error al generar embedding con el modelo: {e}")
            # Llamar recursivamente para usar el sistema de respaldo
            self.model = None
            return self.generar_embedding(texto)
    
    def guardar_documento(self, 
                          contenido: str, 
                          autor: str, 
                          tipo_doc: str, 
                          id_version: Optional[str] = None,
                          nivel: str = "documento",
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Guarda un documento en el almacén vectorial.
        
        Args:
            contenido: Contenido del documento
            autor: Autor del documento
            tipo_doc: Tipo de documento (código, changelog, requisito, etc.)
            id_version: Identificador de versión para control de duplicados
            nivel: Nivel del documento (documento, resumen_semana, delta)
            metadata: Metadatos adicionales
            
        Returns:
            ID del documento guardado
        """
        if not contenido or not autor or not tipo_doc:
            raise ValueError("Contenido, autor y tipo_doc son obligatorios")
        
        # Generar resumen de 128 tokens (aproximadamente)
        resumen = self._generar_resumen(contenido)
        
        # Generar ID único
        doc_id = str(uuid.uuid4())
        
        # Verificar si existe un documento con el mismo tipo e id_version
        if id_version:
            # Buscar documentos existentes con el mismo tipo e id_version
            resultados = self.collection.query(
                where={"tipo_doc": tipo_doc, "id_version": id_version, "obsoleto": False}
            )
            
            if resultados and resultados.get("ids") and len(resultados["ids"]) > 0:
                # Marcar versión anterior como obsoleta
                doc_anterior_id = resultados["ids"][0]
                self._marcar_como_obsoleto(doc_anterior_id)
                
                # Generar delta (diferencia) entre versiones
                doc_anterior = self.collection.get(ids=[doc_anterior_id])
                contenido_anterior = doc_anterior["documents"][0]
                delta = self._generar_delta(contenido_anterior, contenido)
                
                # Guardar delta como documento separado
                delta_id = str(uuid.uuid4())
                self.collection.add(
                    ids=[delta_id],
                    documents=[delta],
                    metadatas=[{
                        "tipo_doc": tipo_doc,
                        "autor": autor,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "id_version": id_version,
                        "nivel": "delta",
                        "doc_original_id": doc_anterior_id,
                        "doc_nuevo_id": doc_id,
                        "obsoleto": False,
                        "archivado": False
                    }]
                )
        
        # Preparar metadatos base
        meta = {
            "tipo_doc": tipo_doc,
            "autor": autor,
            "timestamp": datetime.datetime.now().isoformat(),
            "nivel": nivel,
            "obsoleto": False,
            "archivado": False,
            "last_access": datetime.datetime.now().isoformat()
        }
        
        # Añadir id_version si existe
        if id_version:
            meta["id_version"] = id_version
            
        # Añadir metadatos adicionales si existen
        if metadata:
            meta.update(metadata)
        
        # Generar embedding y guardar documento
        try:
            embedding = self.generar_embedding(contenido)
            
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[contenido],
                metadatas=[meta]
            )
            
            # Verificar si se necesita mantenimiento
            self._verificar_mantenimiento()
            
            return doc_id
        except Exception as e:
            print(f"Error al guardar documento: {e}")
            raise
    
    def recuperar_contexto(self, consulta: str, k: int = 5, score_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Recupera el contexto relevante para una consulta.
        
        Args:
            consulta: Consulta para buscar contexto relevante
            k: Número máximo de documentos a recuperar
            score_threshold: Umbral mínimo de similitud para considerar un documento relevante
            
        Returns:
            Lista de documentos relevantes con sus metadatos
        """
        if not consulta:
            return []
        
        try:
            # Generar embedding para la consulta
            query_embedding = self.generar_embedding(consulta)
            
            # Primero buscar en resúmenes jerárquicos (más eficiente)
            resultados_resumenes = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"nivel": "resumen_semana", "obsoleto": False, "archivado": False}
            )
            
            # Filtrar por umbral de similitud
            documentos_relevantes = []
            if resultados_resumenes and "documents" in resultados_resumenes:
                for i, (doc, meta, dist) in enumerate(zip(
                    resultados_resumenes["documents"],
                    resultados_resumenes["metadatas"],
                    resultados_resumenes["distances"]
                )):
                    # Convertir distancia a score (1 - dist) porque Chroma usa distancia
                    score = 1 - dist
                    if score >= score_threshold:
                        # Actualizar last_access
                        doc_id = resultados_resumenes["ids"][i]
                        self._actualizar_ultimo_acceso(doc_id)
                        
                        documentos_relevantes.append({
                            "id": doc_id,
                            "contenido": doc,
                            "metadata": meta,
                            "score": score
                        })
            
            # Si no hay suficientes resultados, buscar en documentos individuales
            if len(documentos_relevantes) < k:
                resultados_docs = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k - len(documentos_relevantes),
                    where={"nivel": "documento", "obsoleto": False, "archivado": False}
                )
                
                if resultados_docs and "documents" in resultados_docs:
                    for i, (doc, meta, dist) in enumerate(zip(
                        resultados_docs["documents"],
                        resultados_docs["metadatas"],
                        resultados_docs["distances"]
                    )):
                        score = 1 - dist
                        if score >= score_threshold:
                            # Actualizar last_access
                            doc_id = resultados_docs["ids"][i]
                            self._actualizar_ultimo_acceso(doc_id)
                            
                            documentos_relevantes.append({
                                "id": doc_id,
                                "contenido": doc,
                                "metadata": meta,
                                "score": score
                            })
            
            # Ordenar por relevancia (score)
            documentos_relevantes.sort(key=lambda x: x["score"], reverse=True)
            
            return documentos_relevantes[:k]
        
        except Exception as e:
            print(f"Error al recuperar contexto: {e}")
            return []
    
    def formatear_contexto_recuperado(self, documentos: List[Dict[str, Any]]) -> str:
        """
        Formatea los documentos recuperados como un bloque de contexto.
        
        Args:
            documentos: Lista de documentos recuperados
            
        Returns:
            Texto formateado con el contexto recuperado
        """
        if not documentos:
            return "No se encontró contexto relevante para esta consulta."
        
        contexto = "### Contexto recuperado\n\n"
        
        for i, doc in enumerate(documentos):
            meta = doc["metadata"]
            fecha = datetime.datetime.fromisoformat(meta["timestamp"]).strftime("%d/%m/%Y %H:%M")
            tipo = meta["tipo_doc"]
            autor = meta["autor"]
            nivel = meta["nivel"]
            
            if nivel == "resumen_semana":
                contexto += f"**Resumen semanal** ({fecha}) - {tipo} - {autor}:\n"
            else:
                contexto += f"**Documento** ({fecha}) - {tipo} - {autor}:\n"
            
            # Limitar longitud del contenido para evitar contextos muy largos
            contenido = doc["contenido"]
            if len(contenido) > 500:
                contenido = contenido[:497] + "..."
            
            contexto += f"{contenido}\n\n"
            
            if i < len(documentos) - 1:
                contexto += "---\n\n"
        
        return contexto
    
    def crear_resumenes_jerarquicos(self) -> int:
        """
        Crea resúmenes jerárquicos de documentos para optimizar el almacenamiento.
        Implementa la estrategia RAPTOR.
        
        Returns:
            Número de resúmenes creados
        """
        # Obtener todos los documentos no archivados y no obsoletos
        resultados = self.collection.get(
            where={"nivel": "documento", "obsoleto": False, "archivado": False}
        )
        
        if not resultados or "ids" not in resultados or not resultados["ids"]:
            return 0
        
        # Agrupar por semana y tipo de documento
        grupos = self._agrupar_por_semana_y_tipo(
            resultados["ids"],
            resultados["documents"],
            resultados["metadatas"]
        )
        
        resumenes_creados = 0
        
        # Crear resumen para cada grupo
        for grupo_key, grupo_docs in grupos.items():
            semana, tipo_doc = grupo_key
            
            # Solo resumir si hay al menos 3 documentos en el grupo
            if len(grupo_docs["ids"]) < 3:
                continue
                
            # Generar resumen del grupo
            contenido_combinado = "\n".join([doc[:1000] for doc in grupo_docs["documents"]])
            resumen = self._generar_resumen(contenido_combinado, max_tokens=256)
            
            # Guardar resumen como documento de nivel "resumen_semana"
            resumen_id = self.guardar_documento(
                contenido=resumen,
                autor="sistema",
                tipo_doc=tipo_doc,
                nivel="resumen_semana",
                metadata={
                    "semana": semana,
                    "docs_incluidos": grupo_docs["ids"]
                }
            )
            
            # Marcar documentos originales como archivados
            for doc_id in grupo_docs["ids"]:
                self._marcar_como_archivado(doc_id)
            
            resumenes_creados += 1
        
        return resumenes_creados
    
    def procesar_dataset(self, df, nombre: str) -> str:
        """
        Procesa un dataset (DataFrame) para generar un perfil y guardarlo.
        
        Args:
            df: DataFrame a procesar
            nombre: Nombre del dataset
            
        Returns:
            ID del documento guardado
        """
        import pandas as pd
        
        # Verificar que sea un DataFrame
        if not isinstance(df, pd.DataFrame):
            raise ValueError("El objeto debe ser un DataFrame de pandas")
        
        # Generar estadísticas descriptivas
        n_filas, n_columnas = df.shape
        columnas = df.columns.tolist()
        tipos = df.dtypes.astype(str).to_dict()
        
        # Analizar primeras 200 filas como muestra
        muestra = df.head(200)
        
        # Generar estadísticas básicas
        estadisticas = {}
        for col in columnas:
            if pd.api.types.is_numeric_dtype(df[col]):
                estadisticas[col] = {
                    "min": float(muestra[col].min()),
                    "max": float(muestra[col].max()),
                    "mean": float(muestra[col].mean()),
                    "missing": int(muestra[col].isna().sum())
                }
            elif pd.api.types.is_string_dtype(df[col]):
                valores_unicos = muestra[col].dropna().unique()
                estadisticas[col] = {
                    "unique_count": len(valores_unicos),
                    "sample_values": valores_unicos[:5].tolist() if len(valores_unicos) > 0 else [],
                    "missing": int(muestra[col].isna().sum())
                }
            else:
                # Para otros tipos
                estadisticas[col] = {
                    "tipo": str(df[col].dtype),
                    "missing": int(muestra[col].isna().sum())
                }
        
        # Crear contenido del perfil
        perfil = {
            "nombre": nombre,
            "n_filas": n_filas,
            "n_columnas": n_columnas,
            "columnas": columnas,
            "tipos": tipos,
            "estadisticas": estadisticas,
            "muestra_json": muestra.head(5).to_dict(orient="records")
        }
        
        # Convertir a texto para almacenar
        contenido = (
            f"Perfil del dataset: {nombre}\n"
            f"Filas: {n_filas}, Columnas: {n_columnas}\n\n"
            f"Columnas: {', '.join(columnas)}\n\n"
            "Estadísticas:\n"
        )
        
        for col, stats in estadisticas.items():
            contenido += f"- {col}: {json.dumps(stats)}\n"
        
        contenido += "\nMuestra de datos:\n"
        for i, registro in enumerate(perfil["muestra_json"]):
            contenido += f"{i+1}. {json.dumps(registro)}\n"
        
        # Guardar como documento de tipo "dataset_profile"
        doc_id = self.guardar_documento(
            contenido=contenido,
            autor="sistema",
            tipo_doc="dataset_profile",
            id_version=nombre,  # Usar nombre como ID de versión para evitar duplicados
            metadata={
                "nombre_dataset": nombre,
                "filas": n_filas,
                "columnas": n_columnas
            }
        )
        
        return doc_id
    
    def mantenimiento_automatico(self) -> Dict[str, Any]:
        """
        Realiza mantenimiento automático del almacén vectorial.
        
        Returns:
            Diccionario con estadísticas del mantenimiento
        """
        resultados = {
            "documentos_procesados": 0,
            "resumenes_creados": 0,
            "documentos_archivados": 0,
            "tamano_antes_mb": self._obtener_tamano_almacen(),
            "tamano_despues_mb": 0
        }
        
        # Verificar tamaño
        if resultados["tamano_antes_mb"] <= 1024:  # 1 GB
            return resultados
        
        # Obtener documentos antiguos no accedidos en 30 días
        hace_30_dias = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        documentos_antiguos = self.collection.get(
            where={
                "last_access": {"$lt": hace_30_dias},
                "nivel": "documento",
                "obsoleto": False,
                "archivado": False
            }
        )
        
        if not documentos_antiguos or "ids" not in documentos_antiguos or not documentos_antiguos["ids"]:
            return resultados
        
        # Tomar la mitad menos consultada
        ids = documentos_antiguos["ids"]
        docs = documentos_antiguos["documents"]
        metas = documentos_antiguos["metadatas"]
        
        mitad = len(ids) // 2
        ids_mitad = ids[:mitad]
        docs_mitad = docs[:mitad]
        metas_mitad = metas[:mitad]
        
        resultados["documentos_procesados"] = len(ids_mitad)
        
        # Crear resúmenes ultracortos (64 tokens)
        for i, (doc_id, doc, meta) in enumerate(zip(ids_mitad, docs_mitad, metas_mitad)):
            resumen = self._generar_resumen(doc, max_tokens=64)
            
            # Actualizar documento con el resumen
            self.collection.update(
                ids=[doc_id],
                documents=[resumen],
                metadatas=[{**meta, "resumido": True, "longitud_original": len(doc)}]
            )
            
            # Marcar como archivado
            self._marcar_como_archivado(doc_id)
            resultados["documentos_archivados"] += 1
        
        # Reconstruir índice
        self.client.reset()
        
        # Actualizar tamaño después
        resultados["tamano_despues_mb"] = self._obtener_tamano_almacen()
        
        return resultados
    
    def _generar_resumen(self, texto: str, max_tokens: int = 128) -> str:
        """
        Genera un resumen del texto dado.
        
        Args:
            texto: Texto a resumir
            max_tokens: Número máximo de tokens en el resumen
            
        Returns:
            Resumen del texto
        """
        # Implementación simple de resumen por extracción
        if not texto:
            return ""
        
        # Dividir en párrafos
        parrafos = texto.split("\n")
        parrafos = [p.strip() for p in parrafos if p.strip()]
        
        # Si hay menos de 3 párrafos, devolver el texto original truncado
        if len(parrafos) <= 3:
            return texto[:max_tokens * 4]  # Aproximación: 1 token ≈ 4 caracteres
        
        # Seleccionar primer párrafo y algunos intermedios
        resumen = [parrafos[0]]
        
        # Seleccionar párrafos relevantes (por ahora simplemente algunos distribuidos)
        step = max(1, len(parrafos) // 4)
        for i in range(step, len(parrafos), step):
            if len(parrafos[i]) > 20:  # Solo párrafos con contenido sustancial
                resumen.append(parrafos[i])
            
            # Verificar si ya tenemos suficiente texto
            texto_actual = "\n".join(resumen)
            if len(texto_actual) >= max_tokens * 4:
                break
        
        # Truncar si es necesario
        texto_final = "\n".join(resumen)
        if len(texto_final) > max_tokens * 4:
            texto_final = texto_final[:max_tokens * 4 - 3] + "..."
            
        return texto_final
    
    def _generar_delta(self, texto_anterior: str, texto_nuevo: str) -> str:
        """
        Genera un resumen de diferencias entre dos versiones de texto.
        
        Args:
            texto_anterior: Versión anterior del texto
            texto_nuevo: Nueva versión del texto
            
        Returns:
            Descripción de las diferencias
        """
        # Implementación simple, en el futuro podría usar difflib
        long_anterior = len(texto_anterior)
        long_nuevo = len(texto_nuevo)
        
        if long_anterior > long_nuevo:
            return f"Cambio: Se eliminaron {long_anterior - long_nuevo} caracteres. Versión más corta."
        elif long_nuevo > long_anterior:
            return f"Cambio: Se añadieron {long_nuevo - long_anterior} caracteres. Versión más larga."
        else:
            return "Cambio: Modificación sin cambio de longitud."
    
    def _agrupar_por_semana_y_tipo(self, ids: List[str], docs: List[str], metas: List[Dict]) -> Dict:
        """
        Agrupa documentos por semana y tipo.
        
        Args:
            ids: Lista de IDs de documentos
            docs: Lista de contenidos de documentos
            metas: Lista de metadatos de documentos
            
        Returns:
            Diccionario agrupado por semana y tipo
        """
        grupos = {}
        
        for i, (doc_id, doc, meta) in enumerate(zip(ids, docs, metas)):
            timestamp = meta.get("timestamp")
            tipo_doc = meta.get("tipo_doc")
            
            if not timestamp or not tipo_doc:
                continue
                
            # Determinar semana
            fecha = datetime.datetime.fromisoformat(timestamp)
            semana = fecha.strftime("%Y-W%W")  # Formato año-semana
            
            # Clave de grupo
            grupo_key = (semana, tipo_doc)
            
            # Inicializar grupo si no existe
            if grupo_key not in grupos:
                grupos[grupo_key] = {
                    "ids": [],
                    "documents": [],
                    "metadatas": []
                }
                
            # Añadir documento al grupo
            grupos[grupo_key]["ids"].append(doc_id)
            grupos[grupo_key]["documents"].append(doc)
            grupos[grupo_key]["metadatas"].append(meta)
        
        return grupos
    
    def _verificar_mantenimiento(self) -> None:
        """
        Verifica si se necesita mantenimiento del almacén vectorial.
        """
        try:
            # Contar documentos
            info = self.collection.count()
            
            # Tamaño aproximado en MB
            tamano_mb = self._obtener_tamano_almacen()
            
            # Verificar si se superan los límites
            if info > MAX_DOCUMENTS or tamano_mb > MAX_SIZE_MB:
                print(f"Iniciando creación de resúmenes jerárquicos. Documentos: {info}, Tamaño: {tamano_mb:.2f} MB")
                self.crear_resumenes_jerarquicos()
        except Exception as e:
            print(f"Error al verificar mantenimiento: {e}")
    
    def _obtener_tamano_almacen(self) -> float:
        """
        Obtiene el tamaño aproximado del almacén vectorial en MB.
        
        Returns:
            Tamaño en MB
        """
        try:
            ruta = Path(self.persist_dir)
            tamano_bytes = sum(f.stat().st_size for f in ruta.glob('**/*') if f.is_file())
            return tamano_bytes / (1024 * 1024)  # Convertir a MB
        except Exception as e:
            print(f"Error al obtener tamaño del almacén: {e}")
            return 0
    
    def _marcar_como_obsoleto(self, doc_id: str) -> None:
        """
        Marca un documento como obsoleto.
        
        Args:
            doc_id: ID del documento a marcar
        """
        try:
            # Obtener metadatos actuales
            resultado = self.collection.get(ids=[doc_id])
            if not resultado or "metadatas" not in resultado or not resultado["metadatas"]:
                return
                
            meta = resultado["metadatas"][0]
            meta["obsoleto"] = True
            
            # Actualizar metadatos
            self.collection.update(
                ids=[doc_id],
                metadatas=[meta]
            )
        except Exception as e:
            print(f"Error al marcar documento como obsoleto: {e}")
    
    def _marcar_como_archivado(self, doc_id: str) -> None:
        """
        Marca un documento como archivado.
        
        Args:
            doc_id: ID del documento a marcar
        """
        try:
            # Obtener metadatos actuales
            resultado = self.collection.get(ids=[doc_id])
            if not resultado or "metadatas" not in resultado or not resultado["metadatas"]:
                return
                
            meta = resultado["metadatas"][0]
            meta["archivado"] = True
            
            # Actualizar metadatos
            self.collection.update(
                ids=[doc_id],
                metadatas=[meta]
            )
        except Exception as e:
            print(f"Error al marcar documento como archivado: {e}")
    
    def _actualizar_ultimo_acceso(self, doc_id: str) -> None:
        """
        Actualiza la fecha de último acceso de un documento.
        
        Args:
            doc_id: ID del documento a actualizar
        """
        try:
            # Obtener metadatos actuales
            resultado = self.collection.get(ids=[doc_id])
            if not resultado or "metadatas" not in resultado or not resultado["metadatas"]:
                return
                
            meta = resultado["metadatas"][0]
            meta["last_access"] = datetime.datetime.now().isoformat()
            
            # Actualizar metadatos
            self.collection.update(
                ids=[doc_id],
                metadatas=[meta]
            )
        except Exception as e:
            print(f"Error al actualizar último acceso: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia
    contexto = ContextoVectorial()
    
    # Probar guardar documento
    doc_id = contexto.guardar_documento(
        contenido="Este es un documento de prueba para el sistema de almacenamiento vectorial.",
        autor="sistema",
        tipo_doc="prueba"
    )
    
    print(f"Documento guardado con ID: {doc_id}")
    
    # Probar recuperar contexto
    resultados = contexto.recuperar_contexto("sistema almacenamiento")
    
    print(f"Resultados encontrados: {len(resultados)}")
    for doc in resultados:
        print(f"- {doc['metadata']['tipo_doc']} (Score: {doc['score']:.2f}): {doc['contenido'][:50]}...")