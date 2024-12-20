# API de Análisis Semántico y RAG en artículos científicos de química

## Descripción General
Esta API permite realizar análisis semánticos avanzados y responder preguntas sobre artículos científicos,utilizando un flujo de generación aumentada por recuperación (RAG). Combina modelos de lenguaje de Cohere con búsquedas en bases de datos vectoriales (ChromaDB) para ofrecer respuestas precisas y contextualizadas basadas en documentos.

El sistema utiliza vectores embebidos para localizar información relevante sobre un determinado contenido.
Se encuentran en desarrollo herramientas para realizar búsquedas por DOI y autor.

## Estructura del Proyecto
El proyecto está organizado de la siguiente manera:
📂 project_root/
├── main.py # Archivo principal para arrancar la API 
├── 📂 models/ 
|    └── models.py # Configuración del vectorstore y modelos 
├── 📂 routers/ │ 
|    └── endpoints.py # Definición de los endpoints 
├── 📂 utils/ 
│   └── utils.py # Funciones auxiliares y herramientas  
└── requirements.txt # Lista de dependencias

## Requisitos Previos
Para ejecutar esta API, necesitas instalar las siguientes dependencias. Estas están enumeradas en el archivo `requirements.txt`.

### Dependencias Principales
- **uvicorn**: Servidor ASGI para ejecutar la API.
- **fastapi**: Framework para construir APIs web modernas y rápidas.
- **cohere**: Librería para interactuar con los modelos de lenguaje de Cohere.
- **python-dotenv**: Manejo de variables de entorno desde un archivo `.env`.
- **chromadb**: Base de datos vectorial para recuperación de información.
- **langchain**: Framework para construir cadenas de procesamiento con LLMs.
- **langchain_chroma**: Conector para usar ChromaDB con LangChain.
- **langchain_cohere**: Conector para integrar Cohere con LangChain.

## Requisitos Adicionales
- Python: Asegúrate de tener Python 3.9 o superior instalado.
- Acceso a Internet: Para interactuar con Cohere y descargar dependencias.

## Guía Rápida
1. Clona este repositorio.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
3. Crea un archivo .env en el directorio raíz para configurar las claves de acceso necesarias. 
    Ejemplo de archivo .env: 
    COHERE_API_KEY=<tu-api-key-de-cohere>

## Endpoints de la API

### 1. Subida de documentos XML

#### POST `/upload`

**Descripción**

Este endpoint permite subir un archivo XML, extraer su contenido, generar fragmentos (chunks) con metadatos, y almacenarlos en un diccionario interno para su posterior procesamiento.

**Parámetros del cuerpo de la solicitud:**

- `file`: Archivo XML que contiene el documento a procesar. Debe cumplir con el formato `.xml`.

**Funcionamiento:**

1. **Validación del archivo:** Verifica que el archivo tenga la extensión `.xml`. Si no cumple, retorna un error `400 Bad Request`.
2. **Procesamiento del contenido XML:** Convierte el contenido del archivo a un diccionario usando `xmltodict` y maneja cualquier error durante el proceso.
3. **Extracción de información:** Usa la función `extract_information_XMLdict` para extraer datos como:
   - `title`: Título del documento.
   - `doi`: DOI del documento.
   - `authors`: Lista de autores.
   - `sections`: Secciones del documento.
4. **Verificación de duplicados:** Comprueba si el DOI ya está cargado en el diccionario interno `chunks_con_metadata`. Si ya existe, retorna un error `400 Bad Request`.
5. **Generación de chunks:** Usa la función `chunks_generation` para dividir las secciones en fragmentos manejables y añade metadatos como `id`, `text`, `title`, `authors` y `doi`.
6. **Almacenamiento:** Guarda los fragmentos generados en el diccionario `chunks_con_metadata`.

**Respuesta exitosa (200 OK):**

```json
{
  "message": "Document uploaded successfully",
  "DOI": "10.1234/example.doi"
}
```

**Errores posibles:**

- 400 Bad Request:

    - Si el archivo no es un XML:
        ```json
        {
        "detail": "El archivo debe ser un XML."
        }
        ```
    - Si el DOI ya está cargado:
        ```json
        {
        "detail": "El DOI '10.1234/example.doi' ya está cargado pero no embebido."
        }
        ```
- 500 Internal Server Error:

    - Error interno al procesar el XML:
        ```json
        {
        "detail": "Error al procesar el XML: [descripción del error]"
        }
        ```
    - Error al extraer información del XML:
        ```json
        {
        "detail": "Error al extraer información del XML: [descripción del error]"
        }
        ```
    - Error al generar los chunks:
        ```json
        {
        "detail": "Error al generar chunks: [descripción del error]"
        }
        ```
    - Error inesperado:
        ```json
        {
        "detail": "Error interno en el servidor.",
        "traceback": "[pila de errores]"
        }
        ```
    
**Notas adicionales:**

Este endpoint no almacena los datos en una base de datos persistente. Los fragmentos se almacenan temporalmente en el diccionario chunks_con_metadata para procesamientos adicionales.
El diccionario chunks_con_metadata utiliza el DOI como clave única.

### 2. Embedding de documentos

#### POST `/embed`

**Descripción:**

Este endpoint genera embeddings para los **chunks** del documento especificado por el **DOI** y los añade a la colección de ChromaDB. Los embeddings generados se utilizan para realizar búsquedas de similitud posteriormente.

El proceso involucra los siguientes pasos:

    - Verificación del DOI: Se verifica si el DOI está presente en el diccionario de datos cargados (chunks_con_metadata).
    - Preparación de los Chunks y Metadatos: Los chunks de texto y sus metadatos (DOI, título y autores) son extraídos.
    - Generación de Embeddings: Los embeddings generados se añaden a la colección de ChromaDB.
    - Limpieza: Los chunks procesados son eliminados del diccionario local para evitar duplicados en futuras solicitudes.

**Parámetros del cuerpo de la solicitud:**

- **doi** (tipo: `str`): El **DOI** del documento para el cual se generarán los embeddings y se añadirán a la colección.

**Funcionamiento:**

1. **Parámetros de entrada:** Se detalla el parámetro **DOI** que debe ser enviado en la solicitud.
2. **Respuesta:** Se describe la respuesta con un campo **message** que indica si los embeddings fueron generados y añadidos exitosamente.
3. **Excepciones:** Se describen las excepciones posibles, como si el **DOI** no se encuentra en los datos cargados o si hay errores en el procesamiento.
4. **Implementación en el código:** Se muestra cómo se implementa el endpoint en FastAPI para generar los embeddings y agregarlos a la colección de ChromaDB.

**Respuesta:**

- **message** (tipo: `str`): Mensaje indicando si los embeddings fueron generados y añadidos correctamente a la colección.

**Ejemplo de solicitud:**

- **Request:**

        ```json
        {
        "doi": "10.1021/acs.jctc.8b00959"
        }
        ```

**Ejemplo de respuesta:**

- **Response:**

        ```json
        {
        "message": "Embeddings generados y añadidos con éxito para el DOI 10.1021/acs.jctc.8b00959"
        }
        ```

**Modelos de datos utilizados:**

- **ChunkMetadata:** Representa la metadata y los chunks de un documento. Se utiliza para almacenar información sobre el contenido, título, autores, sección, y DOI.

**Errores posibles:**

- 404 - DOI no encontrado en los datos cargados: Si el DOI especificado no existe en los datos cargados (en el diccionario chunks_con_metadata).

- 500 - Los datos de chunks no están en el formato esperado: Si los datos de los chunks no están en el formato esperado (una lista de diccionarios).

- 500 - Error al acceder a las claves en los datos: Si ocurre un error al intentar acceder a las claves necesarias en los chunks.

- 500 - Error al agregar a la colección: Si ocurre un error al intentar agregar los chunks y metadatos al vectorstore de ChromaDB.

**Consideraciones adicionales:**

- El **DOI** es un identificador único para los documentos, y este endpoint asume que cada **DOI** tiene un conjunto de **chunks** de texto que pueden ser procesados para generar embeddings.
- El código maneja errores como la falta de un **DOI** en los datos, problemas con el formato de los **chunks**, o errores al intentar agregar los datos a la colección de ChromaDB.

### 3. Búsqueda en la base de datos

#### POST `/search`

**Descripción:**
Este endpoint realiza una búsqueda en la colección de ChromaDB utilizando LangChain y devuelve los documentos más relevantes junto con sus puntuaciones de similitud. 

La búsqueda se ejecuta en función de la consulta proporcionada por el usuario, utilizando un modelo de similitud (por ejemplo, cosine) que compara los vectores de la consulta con los documentos almacenados en ChromaDB.

***Parámetros del cuerpo de la solicitud:**

- **query** (tipo: `AskRequest`): 
  - **question** (tipo: `str`): La consulta de búsqueda que se utilizará para encontrar documentos relacionados.

**Funcionamiento:**

1. **Parámetros de entrada:** Se detalla que la solicitud debe incluir un campo `question` con la consulta de búsqueda.
2. **Respuesta:** Se explica la estructura de los resultados, incluyendo los campos `doi`, `title`, `content_snippet` y `similarity_score`.
3. **Excepciones:** Se describe cómo se manejan los errores (por ejemplo, cuando no se encuentran resultados o cuando ocurre un error del servidor).
4. **Implementación en el código:** Se muestra cómo se implementa el endpoint en FastAPI para realizar la búsqueda y retornar los resultados.

**Respuesta:**

- **results** (tipo: `list`): Lista de resultados de búsqueda, cada uno con los siguientes campos:
  - **doi** (tipo: `str`): DOI del documento.
  - **title** (tipo: `str`): Título del documento.
  - **content_snippet** (tipo: `str`): Fragmento de texto del documento relevante para la consulta.
  - **similarity_score** (tipo: `float`): Puntuación de similitud entre el documento y la consulta.

**Ejemplo de solicitud:**

- **Request:**
        Modelo Utilizado:
            AskRequest: Solicitud que contiene la pregunta del usuario.

        ```json
        {
        "question": "Machine Learning en la química"
        }
        ```

- **Response:**
        Modelos Utilizados:
            SearchResult: Representa un resultado de búsqueda con su DOI, título, fragmento de contenido y puntuación de similitud.
            SearchResponse: Respuesta que contiene una lista de SearchResult.

        ```json
        {
        "results": [
            {
            "doi": "10.1021/acs.chemrev.1c00033",
            "title": "Machine Learning for Chemical Reactions",
            "content_snippet": "use of machine learning. The combination of electronic structure theory, molecular dynamics, machine learning, and virtual reality brings this one step closer and will also have potentially far reachi",
            "similarity_score": 0.5680800080299377
            },
            {
            "doi": "10.1039/d2sc05089g",
            "title": "Predictive chemistry: machine learning for reaction deployment, reaction development, and reaction discovery",
            "content_snippet": "Up to this point, the focus of this review has been on ML applications involving known chemistry, i.e., interpolation based on existing data, which inherently implies that the prediction is constraine",
            "similarity_score": 0.6289628744125366
            },
            {
            "doi": "10.1021/acs.chemrev.1c00033",
            "title": "Machine Learning for Chemical Reactions",
            "content_snippet": "Machine learning (ML) techniques applied to chemical reactions have a long history. The present contribution discusses applications ranging from small molecule reaction dynamics to computational platf",
            "similarity_score": 0.6620815396308899
            },
            {
            "doi": "10.1039/d2sc05089g",
            "title": "Predictive chemistry: machine learning for reaction deployment, reaction development, and reaction discovery",
            "content_snippet": "Advances in the high-throughput generation and availability of chemical reaction data have spurred a rapidly growing interest in the intersection of machine learning and chemical synthesis.  Deep lear",
            "similarity_score": 0.6723558902740479
            },
            {
            "doi": "10.1021/acs.chemrev.1c00033",
            "title": "Machine Learning for Chemical Reactions",
            "content_snippet": "problems involving reactions in the gas phase, in solution, and in enzymes. Most problems concerning the representation of the underlying potential energy surfaces are excluded, as these are already w",
            "similarity_score": 0.6779579520225525
            }
        ]
        }
        ```

**Errores posibles:**

- 404 - No se encontraron resultados relevantes: Si no se encuentran documentos relevantes en la base de datos de ChromaDB para la consulta proporcionada.

- 500 - Error en el servidor: Si ocurre un error durante la ejecución de la búsqueda o procesamiento de la consulta.

### 4. Pregunta a la base de datos

#### POST `/ask`

**Descripción:**
Este endpoint responde a una pregunta utilizando los resultados más relevantes obtenidos desde **ChromaDB** y el modelo **Cohere**, con el contexto extraído de artículos científicos. La respuesta se genera en base al contexto relevante de los documentos almacenados.

Utiliza la técnica de RAG (Retrieval-Augmented Generation) para generar una respuesta basada en el contenido de los documentos relevantes encontrados. Los pasos detallados del proceso son:

    - Búsqueda en ChromaDB: Se realiza una búsqueda en la colección de ChromaDB utilizando la pregunta proporcionada.
    - Obtención del contexto relevante: Los textos de los documentos más relevantes son extraídos y concatenados en un único bloque de contexto.
    - Verificación de la existencia de DOIs: Se extraen los DOIs de los documentos relevantes, que se incluyen en la respuesta para proporcionar referencias a las fuentes.
    - Generación de la respuesta: Si el contexto es adecuado, se utiliza el modelo Cohere para generar una respuesta. Si no, se devuelve una validación indicando que no se pudo generar una respuesta.

**Parámetros de entrada**

- **question** (tipo: `str`): La **pregunta** que se quiere hacer al sistema. El modelo buscará en ChromaDB los documentos más relevantes para esta consulta.

**Respuesta:**

- **question** (tipo: `str`): La pregunta que se recibió en la solicitud.
- **answer** (tipo: `str`): La respuesta generada basada en los documentos relevantes encontrados en la búsqueda, o una validación de que no se encontró un contexto relevante para la respuesta.

**Funcionamiento:**

- **Parámetros de entrada:** Se detalla el parámetro question que debe ser enviado en la solicitud.
- **Respuesta:** La respuesta contiene la pregunta que fue enviada y la respuesta generada por el modelo Cohere, basada en los documentos relevantes obtenidos.
- **Excepciones:** Se describen las excepciones posibles, como si no se encontraron resultados relevantes en la búsqueda o si ocurre un error en el proceso de generación de la respuesta.
- **Implementación en el código:** Se proporciona el código de FastAPI para este endpoint, que realiza la búsqueda y genera la respuesta utilizando el contexto relevante de los documentos.

**Ejemplo de solicitud:**

- **Request:**
        Modelo Utilizado:
            AskRequest: Solicitud que contiene la pregunta del usuario.

        ```json
        {
        "question": "¿Cómo se puede usar 'Machine Learning' en la química?"
        }
        ```

- **Response:**
        Modelo Utilizado:
            AskResponse: Respuesta que contiene la pregunta y la respuesta generada.

        ```json
        {
        "question": "como se puede usar machine learning en la química?",
        "answer": "Las técnicas de aprendizaje automático (machine learning) en química tienen un amplio rango de aplicaciones, desde la dinámica de reacciones de pequeñas moléculas hasta plataformas computacionales para la planificación de reacciones. Estas técnicas son especialmente útiles para problemas que involucran tanto computación como experimentos, permitiendo el desarrollo de modelos consistentes con el conocimiento experimental y abordando problemas que son intratables con métodos convencionales. La combinación de aprendizaje automático, experimentación y simulación puede optimizar sistemas de reacciones químicas para tareas específicas, como maximizar rendimientos o minimizar el uso de disolventes problemáticos.\n\nBibliografía: 10.1039/d2sc05089g, 10.1021/acs.chemrev.1c00033"
        }
        ```

**Errores posibles:**

- 404 - No se encontraron resultados relevantes: Si no se encuentran documentos relevantes en la base de datos de ChromaDB que se ajusten a la pregunta.

- 500 - Error al generar la respuesta: Si ocurre un error al procesar la pregunta o generar la respuesta basada en el contexto.

### 5. Listado de DOIs de la base de datos

#### GET `/get_all_dois`

**Descripción:**

Este endpoint recupera todos los documentos almacenados en la colección de **ChromaDB** y extrae el valor del **DOI** de los metadatos de cada documento. Los DOIs se almacenan en un set para asegurar que no haya duplicados y luego se devuelve como una lista. Los pasos detallados del proceso son:

    - Recuperación de documentos: Se accede a la colección de ChromaDB y se obtienen todos los documentos almacenados.
    - Extracción de DOIs: Se extraen los DOIs de los metadatos de los documentos.
    - Eliminación de duplicados: Se utiliza un set para eliminar duplicados y asegurar que cada DOI aparezca solo una vez.
    - Devolución de DOIs: Los DOIs únicos se devuelven en una lista como respuesta.

**Respuesta:**

- **dois** (tipo: `list`): Lista de **DOIs** únicos extraídos de los metadatos de los documentos en la colección.

**Funcionamiento:**

- **Recuperación de documentos:** Se usa vectorstore._collection.get() para acceder a los documentos almacenados en la colección de ChromaDB.
- **Extracción de DOIs:** Se extraen los DOIs de los metadatos de cada documento y se almacenan en un set para eliminar duplicados.
- **Devolución de la respuesta:** Se devuelve la lista de DOIs únicos en el formato adecuado.

**Ejemplo de solicitud:**

- **Request:**

        ```http
        GET /get_all_dois
        ```

- **Response:**

        ```json
        {
        "dois": [
            "10.1021/acs.jctc.8b00959",
            "10.1038/s41586-020-2015-2",
            "10.1126/science.abc123"
        ]
        }
        ```


### 6. Pregunta a la base de datos por herramientas

#### POST `/embed`

**Descripción:**## Endpoint: `POST /ask_tools`

**Descripción:**
Este endpoint está actualmente en construcción. Se proporcionará más información sobre su funcionamiento próximamente.

**Estado:**

En construcción

---

**Notas:**
- **Objetivo:** Proveer una función para poder obtener distintas respuestas del modelo según la pregunta que se realice. Por ejemplo, que sea capaz de identificar un DOI, buscar contexto en la base de ChromaDB y devolver información.

### Modelos de Datos

#### 1. ChunkMetadata
Representa la metadata y los chunks de un documento. Se utiliza para almacenar información sobre el contenido, título, autores, sección, y DOI.

class ChunkMetadata(BaseModel):
    text: str  # Texto del chunk
    title: str  # Título del documento
    authors: str  # Autores del documento
    section_title: str  # Título de la sección dentro del documento
    doi: str  # DOI (identificador único del documento)

#### 2. AskRequest
Modelo de solicitud para enviar una pregunta al sistema. Contiene un campo de tipo str para la pregunta.

class AskRequest(BaseModel):
    question: str  # Pregunta a responder

#### 3. SearchResult
Representa un resultado de búsqueda, incluyendo el DOI, el título, un fragmento del contenido relevante, y la puntuación de similitud.

class SearchResult(BaseModel):
    doi: str  # Identificador único del documento
    title: str  # Título del documento
    content_snippet: str  # Fragmento relevante del contenido
    similarity_score: float  # Puntuación de relevancia (entre 0 y 1)

#### 4. SearchResponse
Modelo de respuesta para una búsqueda. Contiene una lista de SearchResult que representan los documentos más relevantes encontrados.

class SearchResponse(BaseModel):
    results: list[SearchResult]  # Lista de documentos relevantes

#### 5. AskResponse
Modelo de respuesta a una consulta. Contiene la pregunta y la respuesta generada por el modelo.

class AskResponse(BaseModel):
    question: str  # La pregunta realizada
    answer: str  # Respuesta generada por el modelo

## Lógica de Modelos de Lenguaje

### Función: `RAG_context`

#### Descripción
Verifica si el contexto contiene suficiente información para responder a una pregunta específica, utilizando el modelo Cohere para tomar una decisión.

#### Parámetros de Entrada
| Nombre     | Tipo   | Descripción                                                                 |
|------------|--------|-----------------------------------------------------------------------------|
| `context`  | `str`  | Información relevante obtenida de documentos científicos o bases de datos. |
| `query`    | `str`  | La pregunta formulada por el usuario.                                       |

#### Retorno
- `str`: Una respuesta categórica:
  - `"Si"`: El contexto es suficiente para responder la pregunta.
  - `"No encontré información relevante en los trabajos disponibles."`: No hay suficiente información en el contexto.

#### Implementación
```python
def RAG_context(context: str, query: str):
    #Conexión con Cohere para chequear la pregunta con el contexto:
    #system_request
    system_message = f"""
    Debes decidir si puedes responder a la pregunta, utilizando las posibles respuestas.
    Lo único que sabes es la siguiente información:

    Información relevante:
    {context}

    Pregunta: {query}
    
    Posibles respuestas:
        "Si"
        "No encontré información relevante en los trabajos disponibles." 
    """
    
    # user request
    user_message = f"""Comprueba si tienes la información necesaria para responder.
    Si la tienes, responde: Si.
    Si no la tienes, solo responde: "No encontré información relevante en los trabajos disponibles."
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    #Consulta al modelo
    response = co.chat(
        model="command-r-plus-08-2024", #utilizamos el modelo más actual para obtener mejores respuestas
        messages=messages,
        seed=42 #agregamos semilla para disminuir aleatoriedad en las respuestas
    )

    model_answer = response.message.content[0].text
    return model_answer
    ```

#### Ejemplo de uso

contexto = "Este es el contexto relevante sobre machine learning y química en la base de datos."
pregunta = "¿Cómo se aplica el machine learning a la química?"
respuesta = RAG_context(contexto, pregunta)
print(respuesta)
# Output: "Si" o "No encontré información relevante en los trabajos disponibles."

### Función: `RAG_answer`

#### Descripción
Genera una respuesta detallada y técnica en español a una pregunta específica utilizando un contexto relevante y citando bibliografía.

#### Parámetros de Entrada
| Nombre      | Tipo   | Descripción                                                                 |
|-------------|--------|-----------------------------------------------------------------------------|
| `context`   | `str`  | Información relevante obtenida de documentos científicos o bases de datos. |
| `dois_str`  | `str`  | Lista de identificadores DOI como referencia bibliográfica.                 |
| `query`     | `str`  | La pregunta formulada por el usuario.                                       |

#### Retorno
- `str`: Una respuesta generada:
  - Responde la pregunta utilizando el contexto y mencionando la bibliografía al final.
  - Si no hay información suficiente, devuelve: `"No encontré información relevante en los trabajos disponibles."`

#### Implementación
```python
def RAG_answer(context: str, dois_str: str, query: str):
    #Conexión con Cohere para responder a la pregunta con el contexto:
    #system_request
    system_message = f"""
    Eres un experto en química que solo habla español. 
    Responde con lenguaje técnico y certero.
    Usa solamente la información proporcionada a continuación para responder la 
    pregunta de forma clara:

    Información relevante:
    {context}

    Pregunta: {query}
    Bibliografía: {dois_str}

    Si no tienes la información en información relevante, responde: "No encontré información relevante en los trabajos disponibles."
    """
    
    # user request
    user_message = f"""Comprueba si tienes la información necesaria para responder.
    Si la tienes, respondeme en 3 oraciones. Menciona la bibliografía al final.
    Si no la tienes, solo responde: "No encontré información relevante en los trabajos disponibles."
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    #Consulta al modelo
    response = co.chat(
        model="command-r-plus-08-2024", #utilizamos el modelo más actual para obtener mejores respuestas
        messages=messages,
        seed=42 #agregamos semilla para disminuir aleatoriedad en las respuestas
    )

    model_answer = response.message.content[0].text
    return model_answer
    ```

#### Ejemplo de uso
contexto = "Aquí está el contexto relevante sobre compuestos químicos y su uso, en la base de datos."
dois = "10.1021/acs.jctc.8b00959, 10.1016/j.cplett.2023.139865"
pregunta = "¿Cómo se pueden aplicar estos compuestos en reacciones catalíticas?"
respuesta = RAG_answer(contexto, dois, pregunta)
print(respuesta)
# Output: Respuesta técnica en español con cita de DOI.

### Funciones en construcción

Varias funciones se encuentran en construcción para el endpoint POST/ask_tool

- determine_tool: un modelo de lenguaje determina qué herramienta debe usar en función de la consulta.
- search_by_doi: herramienta para buscar todos los documentos con determinado DOI en metadata.
- search_by_author: herramiento para buscar todos los documentos de determinado autor.
- search_by_content: herramienta para responder según contexto encontrado por similitud (reemplazo actual post/ask)

## Funciones auxiliares

### Función Auxiliar: `extract_information_XMLdict`

#### Descripción
Procesa un archivo XML que contiene información estructurada de un artículo científico. Extrae el título, DOI, autores, abstract y el cuerpo del artículo con sus respectivas secciones.

#### Parámetros de Entrada
| Nombre         | Tipo  | Descripción                                                   |
|----------------|-------|---------------------------------------------------------------|
| `file_content` | `dict` | Contenido del archivo PDF en formato diccionario (sin uso directo en esta función). |
| `xml_dict`     | `dict` | Diccionario que representa el contenido del archivo XML.      |

#### Retorno
- `title` (`str`): Título del artículo.
- `doi` (`str` o `None`): DOI del artículo, si está disponible.
- `authors` (`list[str]`): Lista de nombres completos de los autores.
- `sections` (`list[dict]`): Lista de secciones con títulos y contenido:
  - `section_title`: Título de la sección.
  - `section_content`: Contenido textual de la sección.

#### Implementación
```python
def extract_information_XMLdict(file_content: dict, xml_dict):
    """
    Procesa un archivo XML de un artículo científico para extraer el cuerpo y metadata.
    Guarda metadata del artículo.
    :param file_content: Contenido del archivo PDF en bytes.
    :param xml_dict: Diccionario que contiene el contenido del archivo XML.
    :return: Título, DOI, lista de autores y secciones del artículo.
    """
    # Extraer título
    title = "Sin título"
    try:
        if isinstance(xml_dict, dict):
            title = xml_dict.get("TEI", {}).get("teiHeader", {}).get("fileDesc", {}).get("titleStmt", {}).get("title", {}).get("#text", "Sin título")
    except Exception as e:
        print(f"Error al extraer título: {e}")
    
    # Extraer DOI
    doi = None
    try:
        biblStruct = xml_dict.get("TEI", {}).get("teiHeader", {}).get("fileDesc", {}).get("sourceDesc", {}).get("biblStruct", {})
        if isinstance(biblStruct, dict):
            idno_list = biblStruct.get("idno", [])
            for idno in idno_list:
                if isinstance(idno, dict) and idno.get("@type") == "DOI":
                    doi = idno.get("#text", None)
                    break
    except Exception as e:
        print(f"Error al extraer DOI: {e}")

    # Extraer autores
    authors = []
    try:
        authors_section = xml_dict.get("TEI", {}).get("teiHeader", {}).get("fileDesc", {}).get("sourceDesc", {}).get("biblStruct", {}).get("analytic", {}).get("author", [])
        if isinstance(authors_section, list):
            for author in authors_section:
                persName = author.get("persName", {})
                forename = ""
                surname = ""
                if persName:
                    if isinstance(persName.get("forename", []), list):
                        for name in persName["forename"]:
                            forename += name.get("#text", "") + " "
                    else:
                        forename = persName.get("forename", {}).get("#text", "")
                    surname = persName.get("surname", "")
                if forename or surname:
                    authors.append(f"{forename.strip()} {surname}".strip())
        elif isinstance(authors_section, dict):
            persName = authors_section.get("persName", {})
            forename = persName.get("forename", {}).get("#text", "")
            surname = persName.get("surname", "")
            if forename or surname:
                authors.append(f"{forename} {surname}")
    except Exception as e:
        print(f"Error al extraer autores: {e}")

    # Extraer abstract
    abstract = "Sin abstract"
    try:
        if isinstance(xml_dict, dict):
            abstract = xml_dict.get("TEI", {}).get("teiHeader", {}).get("profileDesc", {}).get("abstract", {}).get("div", {}).get("p", "Sin abstract")
    except Exception as e:
        print(f"Error al extraer abstract: {e}")

    # Filtrar cuerpo (body) y mantener secciones diferenciadas
    sections = []
    try:
        body = xml_dict.get("TEI", {}).get("text", {}).get("body", {}).get("div", [])
        if isinstance(body, list):
            for section in body:
                section_title = section.get("head", "Sin título de sección")
                section_content = section.get("p", "Sin contenido")
                if isinstance(section_content, list):
                    section_content = " ".join([p.get("#text", "") for p in section_content if isinstance(p, dict)])
                elif isinstance(section_content, dict):
                    section_content = section_content.get("#text", section_content)
                sections.append({"section_title": section_title, "section_content": section_content})
        else:
            sections.append({"section_title": "Sin título de sección", "section_content": body.get("p", "Sin contenido")})
    except Exception as e:
        print(f"Error al extraer secciones: {e}")

    sections.append({"section_title": "Abstract", "section_content": abstract})
    
    return title, doi, authors, sections
```

#### Ejemplo de uso

Supongamos que tenemos un archivo XML convertido en un diccionario.

``` python
xml_data = {
    "TEI": {
        "teiHeader": {
            "fileDesc": {
                "titleStmt": {"title": {"#text": "Título del Artículo"}},
                "sourceDesc": {"biblStruct": {"idno": [{"@type": "DOI", "#text": "10.1234/example"}]}}
            },
            "profileDesc": {"abstract": {"div": {"p": "Este es el abstract."}}}
        },
        "text": {"body": {"div": [{"head": "Introducción", "p": "Contenido de la introducción"}]}}
    }
}

titulo, doi, autores, secciones = extract_information_XMLdict({}, xml_data)
print(f"Título: {titulo}")
print(f"DOI: {doi}")
print(f"Autores: {autores}")
print(f"Secciones: {secciones}")
```

### Función Auxiliar: `chunks_generation`

#### Descripción
Toma la información estructurada de un artículo científico, como el título, DOI, autores y secciones, y divide el contenido de las secciones en fragmentos (chunks). A cada fragmento se le agrega metadata relevante, como el título del artículo, autores y DOI.

#### Parámetros de Entrada
| Nombre        | Tipo          | Descripción                                           |
|---------------|---------------|-------------------------------------------------------|
| `title`       | `str`         | Título del artículo científico.                      |
| `doi`         | `str` o `None`| DOI del artículo, si está disponible.                |
| `authors`     | `list[str]`   | Lista de nombres completos de los autores.           |
| `sections`    | `list[dict]`  | Lista de secciones con título y contenido.           |

#### Retorno
- `list[dict]`: Lista de fragmentos (chunks) con su contenido y metadatos asociados. Cada fragmento es un diccionario que contiene:
  - `text`: Contenido del fragmento.
  - `title`: Título del artículo.
  - `authors`: Lista de autores.
  - `doi`: DOI del artículo.

#### Implementación
```python
def chunks_generation(title, doi, authors, sections) -> list[dict]:
    """
    Toma la información extraída del XML de un artículo científico y divide las secciones en chunks.
    Guarda metadata del artículo: título, doi, autores, abstract y título de sección.
    :param title: Título del artículo.
    :param doi: DOI del artículo.
    :param authors: Lista de autores del artículo.
    :param sections: Lista de secciones del artículo, cada una con título y contenido.
    :return: Lista de historias con título y sus respectivos chunks.
    """
    # Configura el divisor de texto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Tamaño de cada fragmento
        chunk_overlap=30  # Superposición entre fragmentos
    )

    # Lista para almacenar los fragmentos con metadatos
    chunks_con_metadata = []

    # Itera sobre las secciones para dividir el contenido y agregar los metadatos
    for section in sections:
        section_title = section["section_title"]
        section_content = section["section_content"]
        
        # Divide el texto en fragmentos
        chunks = text_splitter.split_text(section_content)
        
        # Agrega metadatos a cada fragmento
        for chunk in chunks:
            chunks_con_metadata.append({
                "text": chunk,
                "title": title,
                "authors": authors,
                "doi": doi
            })

    return chunks_con_metadata
```

#### Ejemplo de uso

**Datos de entrada simulados**
title = "Ejemplo de Título"
doi = "10.1234/example"
authors = ["Autor Uno", "Autor Dos"]
sections = [
    {"section_title": "Introducción", "section_content": "Contenido de la introducción. Es algo extenso para demostrar la división."},
    {"section_title": "Resultados", "section_content": "Aquí se muestran los resultados obtenidos."}
]

**Generar chunks**
chunks = chunks_generation(title, doi, authors, sections)

**Mostrar los chunks generados**
for chunk in chunks:
    print(f"Texto: {chunk['text']}")
    print(f"Título: {chunk['title']}")
    print(f"Autores: {chunk['authors']}")
    print(f"DOI: {chunk['doi']}")
    print("---")

#### Notas
La función utiliza RecursiveCharacterTextSplitter para dividir el contenido en fragmentos manteniendo un tamaño fijo y cierta superposición.
Los metadatos incluidos en cada fragmento permiten rastrear el contexto del artículo y facilitar el análisis posterior.

### Funciones auxiliares en construcción

- extract_doi_from_query: extrae DOI de la solicitud del usuario para luego usar la herramienta search_by_doi. 
- extract_author_from_query: extrae nombre de autor de la solicitud del usuario para luego usar la herramienta search_by_author.