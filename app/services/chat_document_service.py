import re

import fitz

from app.services.chat_session_service import (
    get_connection,
    session_belongs_to_user,
    utc_now,
)


MAX_CHAT_PDF_SIZE_MB = 20

PDF_CHUNK_SIZE = 1200
PDF_CHUNK_OVERLAP = 200


# =========================================================
# DATABASE TABLES
# =========================================================

def initialize_document_tables():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            character_count INTEGER NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY(session_id)
                REFERENCES chat_sessions(session_id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,

            FOREIGN KEY(document_id)
                REFERENCES chat_documents(id)
                ON DELETE CASCADE,

            FOREIGN KEY(session_id)
                REFERENCES chat_sessions(session_id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chat_documents_session
        ON chat_documents(session_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chat_document_chunks_session
        ON chat_document_chunks(session_id)
        """
    )

    connection.commit()
    connection.close()


initialize_document_tables()


# =========================================================
# TEXT
# =========================================================

def normalize_pdf_text(text):

    text = str(text).replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# =========================================================
# PDF EXTRACTION
# =========================================================

def extract_pdf_text(pdf_bytes):

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    try:

        page_count = document.page_count

        pages = []

        for page_number in range(page_count):

            page = document.load_page(
                page_number
            )

            text = page.get_text(
                "text"
            )

            text = normalize_pdf_text(
                text
            )

            if text:

                pages.append(
                    f"[Page {page_number + 1}]\n{text}"
                )

        full_text = "\n\n".join(
            pages
        )

        return (
            full_text,
            page_count,
        )

    finally:

        document.close()


# =========================================================
# CHUNKING
# =========================================================

def chunk_text(
    text,
    chunk_size=PDF_CHUNK_SIZE,
    overlap=PDF_CHUNK_OVERLAP,
):

    text = normalize_pdf_text(
        text
    )

    if not text:
        return []

    chunks = []

    start = 0

    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[
            start:end
        ].strip()

        if chunk:

            chunks.append(
                chunk
            )

        if end >= text_length:
            break

        start = max(
            end - overlap,
            start + 1,
        )

    return chunks


# =========================================================
# SAVE PDF
# =========================================================

def save_document(
    session_id,
    user_id,
    filename,
    pdf_bytes,
):

    if not session_belongs_to_user(
        session_id,
        user_id,
    ):

        raise ValueError(
            "Invalid chat session."
        )

    full_text, page_count = (
        extract_pdf_text(
            pdf_bytes
        )
    )

    if not full_text.strip():

        raise ValueError(
            "No readable text was found in this PDF. "
            "Scanned image-only PDFs are not supported yet."
        )

    chunks = chunk_text(
        full_text
    )

    if not chunks:

        raise ValueError(
            "Could not create document chunks."
        )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chat_documents (
            session_id,
            filename,
            page_count,
            character_count,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            filename,
            page_count,
            len(full_text),
            utc_now(),
        ),
    )

    document_id = (
        cursor.lastrowid
    )

    for index, chunk in enumerate(
        chunks
    ):

        cursor.execute(
            """
            INSERT INTO chat_document_chunks (
                document_id,
                session_id,
                chunk_index,
                content
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                document_id,
                session_id,
                index,
                chunk,
            ),
        )

    connection.commit()

    connection.close()

    return {
        "document_id":
            document_id,

        "filename":
            filename,

        "pages":
            page_count,

        "characters":
            len(full_text),

        "chunks":
            len(chunks),
    }


# =========================================================
# SESSION DOCUMENTS
# =========================================================

def get_session_documents(
    session_id,
    user_id,
):

    if not session_belongs_to_user(
        session_id,
        user_id,
    ):

        return []

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            filename,
            page_count,
            character_count,
            created_at

        FROM chat_documents

        WHERE session_id = ?

        ORDER BY id DESC
        """,
        (
            session_id,
        ),
    ).fetchall()

    connection.close()

    return [
        {
            "document_id":
                row["id"],

            "filename":
                row["filename"],

            "pages":
                row["page_count"],

            "characters":
                row["character_count"],

            "created_at":
                row["created_at"],
        }

        for row in rows
    ]


# =========================================================
# DOCUMENT CHUNKS
# =========================================================

def get_session_document_chunks(
    session_id,
    user_id,
):

    if not session_belongs_to_user(
        session_id,
        user_id,
    ):

        return []

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            c.id,
            c.document_id,
            c.chunk_index,
            c.content,
            d.filename

        FROM chat_document_chunks c

        JOIN chat_documents d
            ON d.id = c.document_id

        WHERE c.session_id = ?

        ORDER BY
            c.document_id DESC,
            c.chunk_index ASC
        """,
        (
            session_id,
        ),
    ).fetchall()

    connection.close()

    return [
        {
            "id":
                row["id"],

            "document_id":
                row["document_id"],

            "chunk_index":
                row["chunk_index"],

            "content":
                row["content"],

            "filename":
                row["filename"],
        }

        for row in rows
    ]