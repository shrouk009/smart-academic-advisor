from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from pydantic import BaseModel

from app.services.chatbot_service import (
    answer_question,
)

from app.services.chat_session_service import (
    create_session,
    ensure_session,
    get_full_history,
    list_sessions,
    clear_session_history,
    session_belongs_to_user,
)

from app.services.chat_document_service import (
    save_document,
    get_session_documents,
    MAX_CHAT_PDF_SIZE_MB,
)


router = APIRouter()


# =========================================================
# MODELS
# =========================================================

class ChatRequest(BaseModel):

    question: str

    session_id: str | None = None

    user_id: str | None = None


class SessionRequest(BaseModel):

    user_id: str | None = None


class ClearRequest(BaseModel):

    session_id: str

    user_id: str | None = None


# =========================================================
# ASK
# =========================================================

@router.post("/ask")
def ask_chatbot(
    request: ChatRequest,
):

    return answer_question(
        question=request.question,
        session_id=request.session_id,
        user_id=request.user_id,
    )


# =========================================================
# NEW SESSION
# =========================================================

@router.post("/session")
def new_chat_session(
    request: SessionRequest,
):

    session_id = create_session(
        request.user_id
    )

    return {
        "session_id":
            session_id
    }


# =========================================================
# HISTORY
# =========================================================

@router.get(
    "/history/{session_id}"
)
def chat_history(
    session_id: str,
    user_id: str | None = None,
):

    resolved_session_id = (
        ensure_session(
            session_id=session_id,
            user_id=user_id,
        )
    )

    if (
        resolved_session_id
        !=
        session_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Chat session was not found "
                "for this user."
            ),
        )

    return {
        "session_id":
            session_id,

        "messages":
            get_full_history(
                session_id,
                user_id,
            ),
    }


# =========================================================
# SAVED CHATS
# =========================================================

@router.get("/sessions")
def user_sessions(
    user_id: str | None = None,
):

    return {
        "sessions":
            list_sessions(
                user_id
            )
    }


# =========================================================
# CLEAR
# =========================================================

@router.post("/clear")
def clear_chat(
    request: ClearRequest,
):

    cleared = (
        clear_session_history(
            request.session_id,
            request.user_id,
        )
    )

    if not cleared:

        raise HTTPException(
            status_code=404,
            detail=(
                "Chat session was not found "
                "for this user."
            ),
        )

    return {
        "message":
            "Conversation cleared successfully.",

        "session_id":
            request.session_id,
    }


# =========================================================
# UPLOAD PDF
# =========================================================

@router.post("/upload-pdf")
async def upload_chat_pdf(

    session_id: str = Form(...),

    user_id: str = Form(...),

    file: UploadFile = File(...),

):

    if not session_belongs_to_user(
        session_id,
        user_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="Invalid chat session.",
        )

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read()

    max_bytes = (
        MAX_CHAT_PDF_SIZE_MB
        *
        1024
        *
        1024
    )

    if len(pdf_bytes) > max_bytes:

        raise HTTPException(
            status_code=413,
            detail=(
                f"PDF is too large. "
                f"Maximum size is "
                f"{MAX_CHAT_PDF_SIZE_MB} MB."
            ),
        )

    try:

        result = save_document(
            session_id=session_id,
            user_id=user_id,
            filename=file.filename,
            pdf_bytes=pdf_bytes,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "Chat PDF upload error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not process this PDF."
            ),
        )

    return {
        "message":
            "PDF attached to this chat.",

        **result,
    }


# =========================================================
# GET SESSION PDF FILES
# =========================================================

@router.get(
    "/documents/{session_id}"
)
def session_documents(
    session_id: str,
    user_id: str,
):

    if not session_belongs_to_user(
        session_id,
        user_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="Invalid chat session.",
        )

    return {
        "documents":
            get_session_documents(
                session_id,
                user_id,
            )
    }