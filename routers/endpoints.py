from pydantic import BaseModel
from models.models import RAG_context, RAG_answer, vectorstore, embedding_function_lc, determine_tool, search_by_author, search_by_content, search_by_doi
from utils.utils import chunks_generation, extract_information_XMLdict, extract_doi_from_query, extract_author_from_query
from fastapi import FastAPI, UploadFile, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from langchain.text_splitter import RecursiveCharacterTextSplitter
import xmltodict
import traceback

router = APIRouter()

# Diccionario global para almacenar los chunks con metadata
chunks_con_metadata = {}

class ChunkMetadata(BaseModel):    # Modelo para representar la metadata y chunks
    text: str
    title: str
    authors: str
    section_title: str
    doi: str

class AskRequest(BaseModel):    # Modelo de la solicitud
    question: str

class SearchResult(BaseModel):
    doi: str  # Identificador único del documento
    title: str         # Título del documento
    content_snippet: str  # Fragmento relevante del contenido
    similarity_score: float  # Puntuación de relevancia (entre 0 y 1)

class SearchResponse(BaseModel):
    results: list[SearchResult]  # Lista de documentos relevantes

class AskResponse(BaseModel):
    question: str  # La pregunta del usuario
    answer: str    # La respuesta generada por el modelo

@router.post("/upload")
async def upload_file(file: UploadFile):
    try:
        # Validar el tipo de archivo
        if not file.filename.endswith(".xml"):
            raise HTTPException(status_code=400, detail="El archivo debe ser un XML.")
        
        # Leer el contenido del archivo
        xml_content = await file.read()
        
        # Convertir el contenido XML a un diccionario
        try:
            xml_dict = xmltodict.parse(xml_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al procesar el XML: {str(e)}")
        
        # Extraer información del XML
        try:
            title, doi, authors, sections = extract_information_XMLdict(xml_content, xml_dict)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al extraer información del XML: {str(e)}")

        # Verificar si el DOI ya está cargado en el diccionario
        if doi in chunks_con_metadata and chunks_con_metadata[doi]:
            raise HTTPException(status_code=400, detail=f"El DOI '{doi}' ya está cargado pero no embebido.")
        
        # Generar los chunks a partir de las secciones
        try:
            chunks_con_metadata_list = chunks_generation(title, doi, authors, sections)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar chunks: {str(e)}")

        # Si el DOI no existe en el diccionario, creamos una nueva entrada
        if doi not in chunks_con_metadata:
            chunks_con_metadata[doi] = []

        # Añadir los chunks con metadata
        for i, chunk_data in enumerate(chunks_con_metadata_list):
            # Agregar el chunk al diccionario con su ID, texto y metadata
            chunks_con_metadata[doi].append({
                "id": f"{doi}_{i+1}",  # Generar un ID único basado en el DOI y un índice
                "text": chunk_data["text"],
                "title": chunk_data["title"],
                "authors": chunk_data["authors"],
                #"section_title": chunk_data["section_title"],
                "doi": chunk_data["doi"]
            })
        
        # Imprimir el diccionario para verificar el contenido
        print(f"Chunks cargados para el DOI {doi}: {chunks_con_metadata[doi]}")

        # Retornar solo el ID (DOI) y un mensaje de éxito
        return {
            "message": "Document uploaded successfully",
            "DOI": doi
        }
    
    except HTTPException as e:
        raise e
    except Exception:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno en el servidor.", "traceback": traceback_str},
        )


@router.post("/embed")
async def generate_embeddings(doi: str):
    """
    Generar embeddings para los chunks del documento especificado por DOI
    y añadirlos a la colección.
    """
    # Verificar si el DOI está en el diccionario
    if doi not in chunks_con_metadata:
        raise HTTPException(status_code=404, detail="DOI no encontrado en los datos cargados.")
    
    # Obtener los chunks y metadatos del diccionario
    chunk_data_list = chunks_con_metadata[doi]
    
    if not isinstance(chunk_data_list, list):
        raise HTTPException(status_code=500, detail="Los datos de chunks no están en el formato esperado.")
    
    # Asegurarse de que cada chunk tenga las claves necesarias
    try:
        chunks = [data["text"] for data in chunk_data_list if "text" in data]
        metadatas = [{"doi": data["doi"],
                    "title": data["title"],
                    "authors":  ", ".join(data["authors"]) if isinstance(data["authors"], list) else data["authors"],
                    #"section_title": data["section_title"]
                    } 
                    for data in chunk_data_list if "doi" in data]
        ids = [f"{doi}_{i+1}" for i, _ in enumerate(chunks)]
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Error al acceder a las claves en los datos: {str(e)}")

    try:
        vectorstore.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al agregar a la colección: {str(e)}")
    
    # Borrar los chunks procesados del diccionario local
    del chunks_con_metadata[doi]

    return {"message": f"Embeddings generados y añadidos con éxito para el DOI {doi}"}

@router.post("/search", response_model=SearchResponse)
async def search(query: AskRequest):
    """
    Realiza una búsqueda en la colección de ChromaDB utilizando LangChain.
    Devuelve documentos relevantes con sus puntuaciones de similitud.
    """
    try:
        # Ejecutar búsqueda en ChromaDB
        search_results = vectorstore.similarity_search_with_score(query=query.question, k=5)
        if not search_results:
            raise HTTPException(status_code=404, detail="No se encontraron resultados relevantes.")
        print(search_results)
        # Formatear resultados para la respuesta
        results = [
            SearchResult(
                doi=res.metadata["doi"],
                title=res.metadata["title"],
                content_snippet=res.page_content[:200],  # Fragmento de texto relevante
                similarity_score=score
            )
            for res,score in search_results
        ]

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la búsqueda: {str(e)}")

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Responde a una pregunta usando los resultados más relevantes obtenidos 
    desde ChromaDB y el modelo Cohere con contexto de artículos científicos.
    """
    # Obtener los resultados relevantes para la consulta
    search_results = vectorstore.similarity_search_with_score(query=request.question, k=5)
    
    if not search_results:
        raise HTTPException(status_code=404, detail="No se encontraron resultados relevantes.")

    # Unimos los textos en un solo contexto
    context = "\n".join(
    doc.page_content for doc, _ in search_results  # search_results es una lista de (Document, score)
    if hasattr(doc, "page_content")  # Nos aseguramos de que el documento tenga contenido
    )

    # Extraer los DOIs de los documentos en search_results
    dois = set(doc.metadata.get("doi", "Sin DOI") for doc, _ in search_results if doc.metadata and "doi" in doc.metadata)

    # Unir los DOIs en una cadena para incluir en la respuesta
    dois_str = ", ".join(dois) if dois else "No se encontraron DOIs"

    # Chequear si la respuesta está en el contexto
    check_context = RAG_context(context, request.question)
    print(check_context)
    # Generar la respuesta usando la función RAG_answer
    if check_context == "Si":
        answer = RAG_answer(context, dois_str, request.question)
    
    else:
        answer = check_context
    # Devolver la pregunta y la respuesta generada
    return {"question": request.question, "answer": answer}

@router.post("/ask_tools")
async def ask_question(query: str, vectorstore:object):
    """
    ENDPOINT EN CONSTRUCCIÓN
    -
    Endpoint para responder preguntas utilizando el flujo RAG con herramientas.
    """
    try:
        # 1. Determinar la herramienta adecuada con el modelo
        tool_response = determine_tool(query)

        # Extraer herramienta y parámetros
        tool = tool_response.get("tool")
        parameters = tool_response.get("parameters")

        if not tool or not parameters:
            return {"error": "No se pudo determinar una herramienta adecuada."}

        # 2. Ejecutar la herramienta seleccionada
        if tool == "search_by_doi":
            doi = parameters.get("doi")
            search_results = search_by_doi(doi)

        elif tool == "search_by_author":
            author = parameters.get("author")
            search_results = search_by_author(author)

        elif tool == "search_by_content":
            content_query = parameters.get("query")
            search_results = search_by_content(content_query)

        else:
            return {"error": "La herramienta seleccionada no es válida."}

        if not search_results:
            return {"error": "No se encontraron resultados relevantes para la consulta."}

        # 3. Generar la respuesta
        response_text = RAG_answer(search_results, query)

        return {"query": query, "response": response_text}

    except Exception as e:
        return {"error": f"Error procesando la consulta: {str(e)}"}


@router.get("/get_all_dois")
async def get_all_dois():
    all_docs = vectorstore._collection.get()  # Acceder a la colección interna para obtener los documentos
    
    # Set para almacenar los DOIs y evitar duplicados
    dois = set(doc['doi'] for doc in all_docs['metadatas'] if 'doi' in doc)
    
    # Convertir el set de nuevo a lista para devolverlo
    return {"dois": list(dois)}

