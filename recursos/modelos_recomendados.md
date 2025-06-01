# Modelos Recomendados para Análisis de Datos Médicos

## phi-2: Recomendación Principal

Phi-2 es una excelente opción, sobre todo si buscas un modelo:
* liviano (solo 1.7B parámetros)
* rápido en CPU (ideal si no tienes GPU dedicada o no quieres usarla)
* muy fácil de correr, incluso sin complicaciones de dependencias
* y que ofrece buen rendimiento en tareas estructuradas, como generación de SQL o respuestas lógicas

## ¿Por qué recomendamos phi-2?

1. **Ultra liviano y rápido**  
   Lo puedes correr incluso en laptops antiguas o servidores con pocos recursos. En tu caso (con un servidor Ryzen y SSD rápido), va a correr muy fluido.

2. **Gran precisión para tareas estructuradas**  
   Microsoft entrenó phi-2 con fuerte foco en razonamiento matemático, sintaxis lógica y tareas tipo código, por lo que genera SQL muy limpio y comprensible.

3. **Muy fácil de usar con Ollama**  
   Lo puedes levantar con un solo comando usando Docker u Ollama nativo:
   ```
   ollama run phi
   ```

4. **Ideal para flujos tipo asistente SQL local**  
   Puedes usarlo como backend para herramientas de consulta sobre SQLite sin depender de la nube ni GPU.

5. **Más fiable y ordenado que modelos pequeños** como TinyLLM o GPT4All en consultas estructuradas.

## ¿Cuándo no usar phi-2?

* Si necesitas comprensión profunda de lenguaje natural con muchos matices clínicos o técnicos complejos (como textos médicos extensos), phi-2 se queda corto.
* Tampoco sirve si esperas respuestas largas o discursivas: está optimizado para precisión, no para conversación.

En ese caso, puedes considerar:
- **Mistral 7B cuantizado Q4** (más potente, pero aún razonable en CPU con 16 GB de RAM)
- **LLaMA 3 8B Q4** si quieres un equilibrio mayor entre rendimiento y lenguaje natural.

## Conclusión

Recomendamos phi-2 para consultas naturales sobre SQLite, especialmente como primera capa liviana, rápida y local.

Si más adelante necesitas una capa más poderosa (por ejemplo, interpretación clínica o textos largos), puedes agregar otro modelo como Mistral o LLaMA en tu stack modularmente.

## Implementación

Para integrar phi-2 con nuestro sistema de análisis de turnos médicos, podríamos crear un componente adicional que permita hacer consultas naturales sobre la base de datos SQLite. Esto facilitaría enormemente la extracción de información sin necesidad de conocer SQL.