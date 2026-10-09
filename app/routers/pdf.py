from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from app.services.pdf_service import (
    extract_text_from_pdf,
    ai_summary,
    get_pdf_page_count,
    detect_language
)


router = APIRouter()


# 50 MB maximum upload
MAX_FILE_SIZE = (
    50
    * 1024
    * 1024
)


@router.post(
    "/summarize"
)
async def summarize_pdf(
    file: UploadFile = File(...)
):

    if (
        not file.filename
        .lower()
        .endswith(".pdf")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload "
                "a PDF file."
            )
        )


    pdf_bytes = await file.read()


    if (
        len(pdf_bytes)
        >
        MAX_FILE_SIZE
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "The PDF is too large. "
                "Maximum file size "
                "is 50 MB."
            )
        )


    try:

        page_count = (
            get_pdf_page_count(
                pdf_bytes
            )
        )


        text = (
            extract_text_from_pdf(
                pdf_bytes
            )
        )


    except Exception:

        raise HTTPException(
            status_code=400,
            detail=(
                "The PDF could "
                "not be read."
            )
        )


    if not text.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text "
                "was found in this PDF. "
                "The PDF may contain "
                "scanned images only."
            )
        )


    language = detect_language(
        text
    )


    summary = ai_summary(
        text
    )


    return {

        "filename":
            file.filename,

        "pages":
            page_count,

        "language":
            (
                "Arabic"
                if language == "ar"
                else "English"
            ),

        "characters_extracted":
            len(text),

        "summary":
            summary

    }