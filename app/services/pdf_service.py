import io
import re

import torch
import pymupdf

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


print("Loading Qwen multilingual summarization model...")


# =========================================================
# DEVICE
# =========================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


print(f"Using device: {DEVICE}")


# =========================================================
# TOKENIZER
# =========================================================

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


# =========================================================
# MODEL
# =========================================================

if DEVICE.type == "cuda":

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16
    )

else:

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32
    )


model = model.to(DEVICE)

model.eval()


print(
    f"Qwen summarization model loaded on {DEVICE}"
)


if DEVICE.type == "cuda":

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )


# =========================================================
# PDF PAGE COUNT
# =========================================================

def get_pdf_page_count(
    pdf_bytes: bytes
):

    document = pymupdf.open(
        stream=io.BytesIO(pdf_bytes),
        filetype="pdf"
    )

    page_count = len(document)

    document.close()

    return page_count


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_text_from_pdf(
    pdf_bytes: bytes
):

    document = pymupdf.open(
        stream=io.BytesIO(pdf_bytes),
        filetype="pdf"
    )


    pages = []


    for page_number, page in enumerate(
        document,
        start=1
    ):

        text = page.get_text("text")


        if text.strip():

            pages.append(
                f"\n--- Page {page_number} ---\n{text}"
            )


    document.close()


    full_text = "\n".join(pages)


    return clean_text(full_text)


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(
    text: str
):

    if not text:
        return ""


    text = text.replace(
        "\x00",
        " "
    )


    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )


    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )


    return text.strip()


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(
    text: str
):

    arabic_count = len(
        re.findall(
            r"[\u0600-\u06FF]",
            text
        )
    )


    english_count = len(
        re.findall(
            r"[A-Za-z]",
            text
        )
    )


    if arabic_count > english_count:
        return "ar"


    return "en"


# =========================================================
# TOKEN COUNT
# =========================================================

def count_tokens(
    text: str
):

    return len(
        tokenizer.encode(
            text,
            add_special_tokens=False
        )
    )


# =========================================================
# TEXT CHUNKING
# =========================================================

def split_text(
    text: str,
    max_tokens: int = 1800
):

    if not text:
        return []


    paragraphs = [

        paragraph.strip()

        for paragraph in text.split("\n")

        if paragraph.strip()

    ]


    chunks = []

    current_chunk = []

    current_tokens = 0


    for paragraph in paragraphs:

        paragraph_tokens = count_tokens(
            paragraph
        )


        # Very large paragraph
        if paragraph_tokens > max_tokens:

            if current_chunk:

                chunks.append(
                    "\n".join(
                        current_chunk
                    )
                )

                current_chunk = []

                current_tokens = 0


            words = paragraph.split()

            temporary = []


            for word in words:

                temporary.append(word)


                test_text = " ".join(
                    temporary
                )


                if (
                    count_tokens(test_text)
                    >= max_tokens
                ):

                    chunks.append(
                        test_text
                    )

                    temporary = []


            if temporary:

                chunks.append(
                    " ".join(
                        temporary
                    )
                )


            continue


        if (
            current_tokens
            + paragraph_tokens
            > max_tokens
        ):

            chunks.append(
                "\n".join(
                    current_chunk
                )
            )


            current_chunk = [
                paragraph
            ]

            current_tokens = (
                paragraph_tokens
            )


        else:

            current_chunk.append(
                paragraph
            )

            current_tokens += (
                paragraph_tokens
            )


    if current_chunk:

        chunks.append(
            "\n".join(
                current_chunk
            )
        )


    return chunks


# =========================================================
# BUILD PROMPT
# =========================================================

def build_summary_prompt(
    text: str,
    language: str,
    final_summary=False
):

    if language == "ar":

        if final_summary:

            instruction = """
أنت مساعد أكاديمي متخصص.

المطلوب:
- أنشئ ملخصًا نهائيًا من الملخصات الجزئية الموجودة أدناه.
- اعتمد فقط على المعلومات الموجودة في النص.
- لا تضف أي معلومة من عندك.
- لا تخترع أسماء أو أرقام أو أمثلة غير موجودة.
- احتفظ بالمفاهيم والتعريفات والنقاط الأكاديمية المهمة.
- احذف التكرار.
- اكتب النتيجة باللغة العربية.
- نظّم الملخص في نقاط واضحة وعناوين عند الحاجة.

إذا كانت معلومة غير موجودة في المصدر فلا تضفها.
"""

        else:

            instruction = """
أنت مساعد أكاديمي متخصص في تلخيص المحاضرات والكتب.

لخص النص التالي اعتمادًا على النص المرفق فقط.

قواعد مهمة جدًا:
- لا تضف أي معلومة غير موجودة في النص.
- لا تستخدم معلوماتك العامة.
- لا تخترع أسماء أو أحداث أو أرقام.
- حافظ على المفاهيم والتعريفات والمصطلحات المهمة.
- ركز على الأفكار الأساسية.
- اكتب باللغة العربية.
- استخدم نقاطًا واضحة عند الحاجة.

إذا لم يكن النص كافيًا فلا تخمن.
"""

    else:

        if final_summary:

            instruction = """
You are an academic summarization assistant.

Create one final summary from the partial summaries below.

Strict rules:
- Use ONLY information contained in the provided text.
- Do not add outside knowledge.
- Do not invent names, facts, examples, statistics, or events.
- Preserve important academic concepts and definitions.
- Remove repetition.
- Write in English.
- Organize the result clearly with headings or bullet points when useful.

If information is not present in the source, do not add it.
"""

        else:

            instruction = """
You are an academic summarization assistant.

Summarize the following academic text.

Strict rules:
- Use ONLY information contained in the provided text.
- Do not use outside knowledge.
- Do not invent names, facts, examples, statistics, or events.
- Preserve important academic concepts, definitions, and key points.
- Focus on the most important ideas.
- Write in English.
- Use clear bullet points when useful.

If the source does not contain enough information, do not guess.
"""


    return (
        instruction
        + "\n\nSOURCE TEXT:\n"
        + text
    )


# =========================================================
# QWEN GENERATION
# =========================================================

def generate_with_qwen(
    prompt: str,
    max_new_tokens: int = 220
):

    messages = [

        {
            "role": "system",
            "content": (
                "You are a careful academic assistant. "
                "Never introduce information that is not "
                "contained in the supplied source."
            )
        },

        {
            "role": "user",
            "content": prompt
        }

    ]


    formatted_prompt = (
        tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    )


    inputs = tokenizer(
        formatted_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096
    )


    inputs = {

        key: value.to(DEVICE)

        for key, value
        in inputs.items()

    }


    input_length = (
        inputs["input_ids"]
        .shape[1]
    )


    with torch.inference_mode():

        generated_ids = model.generate(

            **inputs,

            max_new_tokens=max_new_tokens,

            do_sample=False,

            num_beams=1,

            repetition_penalty=1.05,

            no_repeat_ngram_size=3,

            pad_token_id=tokenizer.eos_token_id

        )


    new_tokens = generated_ids[
        0,
        input_length:
    ]


    answer = tokenizer.decode(
        new_tokens,
        skip_special_tokens=True
    )


    return answer.strip()


# =========================================================
# SUMMARIZE ONE CHUNK
# =========================================================

def summarize_chunk(
    text: str,
    language: str
):

    prompt = build_summary_prompt(
        text=text,
        language=language,
        final_summary=False
    )


    return generate_with_qwen(
        prompt,
        max_new_tokens=220
    )


# =========================================================
# SUMMARIZE ALL CHUNKS
# =========================================================

def summarize_chunks(
    chunks,
    language
):

    summaries = []

    total = len(chunks)


    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print(
            f"Summarizing chunk "
            f"{index}/{total}"
        )


        try:

            summary = summarize_chunk(
                chunk,
                language
            )


            if summary:

                summaries.append(
                    summary
                )


        except RuntimeError as error:

            print(
                f"GPU/runtime error "
                f"in chunk {index}: "
                f"{error}"
            )


            if DEVICE.type == "cuda":

                torch.cuda.empty_cache()


        except Exception as error:

            print(
                f"Error in chunk "
                f"{index}: {error}"
            )


    return summaries


# =========================================================
# REDUCE SUMMARIES
# =========================================================

def reduce_summaries(
    summaries,
    language
):

    if not summaries:

        return ""


    current_text = "\n\n".join(
        summaries
    )


    round_number = 1


    while (
        count_tokens(current_text)
        > 2200
    ):

        print(
            f"Reduction round "
            f"{round_number}"
        )


        reduction_chunks = split_text(
            current_text,
            max_tokens=1800
        )


        reduced = []


        for index, chunk in enumerate(
            reduction_chunks,
            start=1
        ):

            print(
                f"Reducing "
                f"{index}/"
                f"{len(reduction_chunks)}"
            )


            prompt = build_summary_prompt(
                text=chunk,
                language=language,
                final_summary=True
            )


            result = generate_with_qwen(
                prompt,
                max_new_tokens=240
            )


            if result:

                reduced.append(
                    result
                )


        current_text = "\n\n".join(
            reduced
        )


        round_number += 1


    final_prompt = build_summary_prompt(
        text=current_text,
        language=language,
        final_summary=True
    )


    final_summary = generate_with_qwen(
        final_prompt,
        max_new_tokens=350
    )


    return final_summary


# =========================================================
# COMPLETE PIPELINE
# =========================================================

def ai_summary(
    text: str
):

    if not text.strip():

        return (
            "No readable text was "
            "found in this PDF."
        )


    language = detect_language(
        text
    )


    print(
        f"Detected language: "
        f"{language}"
    )


    chunks = split_text(
        text,
        max_tokens=1800
    )


    print(
        f"Total document chunks: "
        f"{len(chunks)}"
    )


    chunk_summaries = summarize_chunks(
        chunks,
        language
    )


    print(
        f"Completed summaries: "
        f"{len(chunk_summaries)}"
    )


    if not chunk_summaries:

        return (
            "The document could "
            "not be summarized."
        )


    final_summary = reduce_summaries(
        chunk_summaries,
        language
    )


    if DEVICE.type == "cuda":

        torch.cuda.empty_cache()


    return final_summary