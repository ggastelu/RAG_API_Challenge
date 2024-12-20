import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

#Carga de archivos PDF
def extract_information_XMLdict(file_content: dict, xml_dict):
    """
    Procesa un archivo XML de un artículo científico para extraer el cuerpo y metadata.
    Guarda metadata del artículo.
    :param file_content: Contenido del archivo PDF en bytes.
    :return: Lista de historias con título y sus respectivos chunks.
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

def chunks_generation(title, doi, authors, sections) -> list[dict]:
    """
    Toma la información extraída del XML de un artículo científico  y divide las secciones en chunks.
    Guarda metadata del artículo: título, doi, autores, abstract y título de sección.
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

def extract_doi_from_query(query: str) -> str:
    """
    Extrae el DOI de una consulta basada en su formato estándar.
    
    :param query: La consulta proporcionada por el usuario.
    :return: El DOI encontrado en la consulta o None si no se encuentra.
    """
    # Expresión regular para identificar DOIs
    doi_pattern = r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b"
    match = re.search(doi_pattern, query, re.IGNORECASE)
    
    if match:
        return match.group(0)  # Retorna el DOI encontrado
    return None  # Si no se encuentra, retorna None

def extract_author_from_query(query: str) -> str:
    """
    Extrae el nombre de un autor mencionado en una consulta.
    
    :param query: La consulta proporcionada por el usuario.
    :return: El nombre del autor encontrado en la consulta o None si no se encuentra.
    """
    # Palabras clave comunes para buscar autores
    keywords = ["autor", "autor es", "escrito por", "de", "by", "author is"]
    
    # Pasar a minúsculas para búsqueda insensible a mayúsculas
    query_lower = query.lower()
    
    for keyword in keywords:
        if keyword in query_lower:
            # Intentar extraer el autor después de la palabra clave
            author_index = query_lower.find(keyword) + len(keyword)
            author = query[author_index:].strip()  # Obtener texto después de la palabra clave
            # Dividir por posibles delimitadores de oración y quedarse con la primera parte
            author = author.split(".")[0].split(",")[0]
            return author.strip()  # Retornar autor sin espacios sobrantes
    
    return None  # Si no se encuentra, retorna None