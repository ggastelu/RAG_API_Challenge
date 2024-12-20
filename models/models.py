import os
import chromadb
import cohere
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings
import json

load_dotenv()
api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2()
persistent_client = chromadb.PersistentClient()

embedding_function_lc = CohereEmbeddings(
                model="embed-multilingual-v3.0",
                )

# Crear o acceder a la colección de ChromaDB
vectorstore = Chroma(
    client=persistent_client,
    collection_name="scientific_articles",
    collection_metadata={"hnsw:space":"cosine"},
    embedding_function=embedding_function_lc,
)

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
    
    # user request. La separación de indicaciones en system prompt y user prompt funciona mucho mejor que si utilizamos solo una de las partes
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
    
    # user request. La separación de indicaciones en system prompt y user prompt funciona mucho mejor que si utilizamos solo una de las partes
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

def determine_tool(query: str) -> dict:
    messages = [
        {"role": "system", "content": "Eres un asistente que elige la mejor herramienta para responder preguntas."},
        {"role": "user", "content": query},
    ]

    # Realizar la consulta al modelo
    response = co.chat(
        model="command-r-plus-08-2024",
        messages=messages,
        tools=tools,
    )

    # Imprimir la respuesta completa para depuración
    print("Respuesta completa del modelo:", response)

    # Verificar si tool_calls está en la respuesta y tiene datos
    if not response.message.tool_calls:
        raise ValueError("No se encontró ninguna herramienta en la respuesta del modelo.")

    # Extraer la herramienta y sus parámetros de la respuesta
    tool_call = response.message.tool_calls[0]
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    # Verificar que la herramienta esté en el mapa de funciones
    if tool_name not in functions_map:
        raise ValueError(f"La herramienta '{tool_name}' no está definida en functions_map.")

    # Llamar a la herramienta correspondiente
    tool_result = functions_map[tool_name](**arguments)

    # Almacenar el resultado de la herramienta
    messages.append({
        'role': 'tool', 
        'tool_call_id': tool_call.id, 
        'content': tool_result
    })

    return {"tool_result": tool_result, "messages": messages}

# Función para buscar por DOI
def search_by_doi(doi: str):
    # Obtener todos los documentos del vectorstore (esto puede ser lento si tienes muchos documentos)
    all_docs = vectorstore._collection.get()

    # Filtrar los documentos que contienen el DOI en su metadata
    matching_docs = [
        (doc, score) for doc, score in all_docs if doc.metadata.get("doi") == doi
    ]

    # Retornar los documentos coincidentes
    return matching_docs

def search_by_author(author: str):
    # Implementación de la búsqueda por autor usando vectorstore
    pass

def search_by_content(query: str):
    # Implementación de la búsqueda por contenido usando vectorstore
    pass


functions_map = {
    "search_by_doi": search_by_doi,
    "search_by_author": search_by_author,
    "search_by_content": search_by_content
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_by_doi",
            "description": "Search for articles based on DOI and retrieve the relevant content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doi": {"type": "string", "description": "The DOI of the article to search for."}
                },
                "required": ["doi"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_author",
            "description": "Search for articles by a specific author and retrieve relevant content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "author": {"type": "string", "description": "The name of the author to search for."}
                },
                "required": ["author"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_content",
            "description": "Search for articles based on a text query and retrieve the relevant content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A text query to search for in the content of articles."}
                },
                "required": ["query"],
            },
        },
    },
]
