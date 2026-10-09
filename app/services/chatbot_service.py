from pathlib import Path
import re

import numpy as np
import torch

from transformers import (
    AutoTokenizer,
    AutoModel,
)

from app.services.pdf_service import (
    tokenizer as qwen_tokenizer,
    model as qwen_model,
    DEVICE,
)

from app.services.chat_session_service import (
    ensure_session,
    save_message,
    get_history,
)

from app.services.chat_document_service import (
    get_session_document_chunks,
)


# =========================================================
# SETTINGS
# =========================================================

KNOWLEDGE_THRESHOLD = 0.52

MAX_CHAT_INPUT_TOKENS = 3500

MAX_CHAT_OUTPUT_TOKENS = 350

MAX_HISTORY_MESSAGES = 8


# PDF RAG
DOCUMENT_SIMILARITY_THRESHOLD = 0.32

DOCUMENT_FOLLOWUP_THRESHOLD = 0.22

MAX_DOCUMENT_CONTEXT_CHUNKS = 4


# =========================================================
# KNOWLEDGE BASE
# =========================================================

KNOWLEDGE_FILE = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "data"
    / "knowledge_base.txt"
)


# =========================================================
# EMBEDDINGS
# =========================================================

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


print(
    "Loading multilingual chatbot embedding model..."
)


embedding_tokenizer = (
    AutoTokenizer.from_pretrained(
        EMBEDDING_MODEL_NAME
    )
)


EMBEDDING_DEVICE = (
    torch.device("cpu")
)


embedding_model = (
    AutoModel.from_pretrained(
        EMBEDDING_MODEL_NAME
    )
    .to(
        EMBEDDING_DEVICE
    )
)


embedding_model.eval()


print(
    "Multilingual embedding model loaded on CPU"
)


print(
    f"Chatbot Qwen device: {DEVICE}"
)


# =========================================================
# LANGUAGE
# =========================================================

def detect_language(
    text
):

    arabic_count = len(
        re.findall(
            r"[\u0600-\u06FF]",
            text,
        )
    )

    english_count = len(
        re.findall(
            r"[A-Za-z]",
            text,
        )
    )

    if (
        arabic_count
        >
        english_count
    ):

        return "ar"

    return "en"


# =========================================================
# TEXT
# =========================================================

def normalize_text(
    text
):

    text = str(
        text
    ).strip()

    return re.sub(
        r"\s+",
        " ",
        text,
    )


# =========================================================
# EAST ASIAN FILTER
# =========================================================

def contains_east_asian_characters(
    text
):

    pattern = (
        r"[\u3400-\u4DBF"
        r"\u4E00-\u9FFF"
        r"\u3040-\u30FF"
        r"\uAC00-\uD7AF]"
    )

    return bool(
        re.search(
            pattern,
            text,
        )
    )


def remove_east_asian_characters(
    text
):

    pattern = (
        r"[\u3400-\u4DBF"
        r"\u4E00-\u9FFF"
        r"\u3040-\u30FF"
        r"\uAC00-\uD7AF]+"
    )

    text = re.sub(
        pattern,
        "",
        text,
    )

    text = re.sub(
        r"[ \t]{2,}",
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
# SMALL TALK
# =========================================================

def is_small_talk(
    question
):

    q = normalize_text(
        question
    ).lower()

    phrases = [

        "ازيك",
        "إزيك",

        "عامل ايه",
        "عامل إيه",

        "اخبارك",
        "أخبارك",

        "صباح الخير",
        "مساء الخير",

        "السلام عليكم",

        "اهلا",
        "أهلا",

        "مرحبا",
        "مرحباً",

        "هاي",
        "هلو",

        "شكرا",
        "شكراً",

        "تسلم",

        "مين انت",
        "مين أنت",

        "انت مين",
        "أنت مين",

        "hi",
        "hello",
        "hey",

        "how are you",
        "how are u",

        "good morning",
        "good evening",

        "thanks",
        "thank you",

        "who are you",
        "what are you",
    ]

    return any(
        phrase in q
        for phrase in phrases
    )


def generate_small_talk_response(
    question,
    language,
):

    q = normalize_text(
        question
    ).lower()

    if (
        language
        ==
        "ar"
    ):

        if (
            "السلام عليكم"
            in q
        ):

            return (
                "وعليكم السلام ورحمة الله وبركاته 🌟 "
                "أهلًا بيك! أقدر أساعدك في الدراسة، "
                "الجامعة، الـPDF، البرمجة أو أي سؤال عام."
            )

        if (
            "صباح الخير"
            in q
        ):

            return (
                "صباح النور 😊 "
                "تحب أساعدك في إيه؟"
            )

        if (
            "مساء الخير"
            in q
        ):

            return (
                "مساء النور 🌙 "
                "تحب أساعدك في إيه؟"
            )

        if (
            "ازيك" in q
            or
            "إزيك" in q
            or
            "عامل ايه" in q
            or
            "عامل إيه" in q
            or
            "اخبارك" in q
            or
            "أخبارك" in q
        ):

            return (
                "أنا تمام الحمد لله 😊 "
                "وأنت عامل إيه؟ "
                "أنا جاهز أساعدك."
            )

        if (
            "مين انت" in q
            or
            "مين أنت" in q
            or
            "انت مين" in q
            or
            "أنت مين" in q
        ):

            return (
                "أنا Smart Academic Advisor 🤖 "
                "مساعد ذكي للدراسة والجامعة "
                "والـPDF والأسئلة العامة."
            )

        if (
            "شكرا" in q
            or
            "شكراً" in q
            or
            "تسلم" in q
        ):

            return (
                "العفو 😊 "
                "في أي وقت."
            )

        return (
            "أهلًا بيك 😊 "
            "أنا جاهز أساعدك."
        )

    if (
        "how are you"
        in q
        or
        "how are u"
        in q
    ):

        return (
            "I'm doing great 😊 "
            "What can I help you with?"
        )

    if (
        "thank you"
        in q
        or
        "thanks"
        in q
    ):

        return (
            "You're welcome! 😊"
        )

    return (
        "Hi! 😊 "
        "I'm ready to help."
    )


# =========================================================
# UNIVERSITY QUESTION
# =========================================================

def is_university_related(
    question
):

    q = normalize_text(
        question
    ).lower()

    keywords = [

        # English
        "university",
        "college",
        "faculty",

        "course",
        "courses",

        "registration",
        "register",

        "prerequisite",
        "prerequisites",

        "graduation",

        "academic warning",
        "academic probation",

        "credit hour",
        "credit hours",

        "semester",

        "advisor",

        "gpa",
        "cgpa",
        "sgpa",

        # Arabic
        "الجامعة",
        "جامعة",

        "الكلية",
        "كلية",

        "المقرر",
        "المقررات",

        "المادة",
        "المواد",

        "التسجيل",

        "متطلب",
        "متطلبات",

        "التخرج",

        "الإنذار الأكاديمي",
        "الانذار الاكاديمي",

        "الساعات المعتمدة",

        "المعدل",
        "المعدل التراكمي",
        "المعدل الفصلي",

        "الفصل الدراسي",

        "المرشد الأكاديمي",
        "المرشد الاكاديمي",

        "الخطة الدراسية",
    ]

    return any(
        keyword in q
        for keyword in keywords
    )


# =========================================================
# KNOWLEDGE BASE
# =========================================================

def load_knowledge_base():

    if not KNOWLEDGE_FILE.exists():

        print(
            "Warning: knowledge_base.txt was not found."
        )

        return []

    text = (
        KNOWLEDGE_FILE.read_text(
            encoding="utf-8"
        )
    )

    return [

        section.strip()

        for section
        in text.split(
            "\n\n"
        )

        if section.strip()
    ]


# =========================================================
# EMBEDDING FUNCTIONS
# =========================================================

def mean_pooling(
    model_output,
    attention_mask,
):

    token_embeddings = (
        model_output[0]
    )

    mask = (
        attention_mask
        .unsqueeze(-1)
        .expand(
            token_embeddings.size()
        )
        .float()
    )

    summed = torch.sum(
        token_embeddings
        *
        mask,

        dim=1,
    )

    divisor = torch.clamp(
        mask.sum(
            dim=1
        ),

        min=1e-9,
    )

    return (
        summed
        /
        divisor
    )


def create_embedding(
    text
):

    encoded_input = (
        embedding_tokenizer(
            text,

            padding=True,

            truncation=True,

            max_length=256,

            return_tensors="pt",
        )
    )

    encoded_input = {

        key:
            value.to(
                EMBEDDING_DEVICE
            )

        for key, value
        in encoded_input.items()

    }

    with torch.inference_mode():

        output = (
            embedding_model(
                **encoded_input
            )
        )

    embedding = mean_pooling(
        output,

        encoded_input[
            "attention_mask"
        ],
    )

    embedding = (
        torch.nn.functional
        .normalize(
            embedding,

            p=2,

            dim=1,
        )
    )

    return (
        embedding[0]
        .cpu()
        .numpy()
    )


def cosine_similarity(
    vector1,
    vector2,
):

    return float(
        np.dot(
            vector1,
            vector2,
        )
    )


# =========================================================
# UNIVERSITY EMBEDDINGS
# =========================================================

KNOWLEDGE_SECTIONS = (
    load_knowledge_base()
)


KNOWLEDGE_EMBEDDINGS = []


print(
    "Preparing university knowledge base..."
)


for section in KNOWLEDGE_SECTIONS:

    try:

        KNOWLEDGE_EMBEDDINGS.append(
            create_embedding(
                section
            )
        )

    except Exception as error:

        print(
            "Knowledge embedding error:",
            error,
        )


print(
    "Knowledge base ready:",
    len(
        KNOWLEDGE_EMBEDDINGS
    ),
    "sections",
)


def retrieve_context(
    question,
    top_k=2,
):

    if (
        not KNOWLEDGE_SECTIONS
        or
        not KNOWLEDGE_EMBEDDINGS
    ):

        return (
            "",
            0.0,
        )

    question_embedding = (
        create_embedding(
            question
        )
    )

    results = []

    for (
        index,
        embedding
    ) in enumerate(
        KNOWLEDGE_EMBEDDINGS
    ):

        score = (
            cosine_similarity(
                question_embedding,
                embedding,
            )
        )

        results.append(
            (
                score,

                KNOWLEDGE_SECTIONS[
                    index
                ],
            )
        )

    results.sort(
        key=lambda item:
            item[0],

        reverse=True,
    )

    results = (
        results[
            :top_k
        ]
    )

    context = (
        "\n\n".join(
            item[1]
            for item
            in results
        )
    )

    score = (
        results[0][0]
        if results
        else 0.0
    )

    return (
        context,
        score,
    )


# =========================================================
# PDF QUESTION DETECTION
# =========================================================

def is_document_related_question(
    question,
):

    q = normalize_text(
        question
    ).lower()

    keywords = [

        # English
        "pdf",
        "document",
        "file",

        "uploaded file",
        "attached file",

        "summarize this",
        "summarize the file",

        "according to the file",
        "according to this document",

        "in the pdf",
        "in the file",

        "from the pdf",
        "from the file",

        "this pdf",
        "this document",

        # Arabic
        "الملف",
        "المستند",
        "المرفق",

        "الـ pdf",
        "الـpdf",

        "لخص الملف",
        "لخصه",

        "اشرح الملف",

        "حسب الملف",

        "في الملف",

        "من الملف",
    ]

    return any(
        keyword in q
        for keyword in keywords
    )


# =========================================================
# AMBIGUOUS PDF FOLLOW-UP
# =========================================================

def is_ambiguous_document_followup(
    question,
):

    q = normalize_text(
        question
    ).lower()

    words = re.findall(
        r"[A-Za-z\u0600-\u06FF0-9]+",
        q,
    )

    # لا نعتبر السؤال الطويل Follow-up مبهم.
    if (
        len(words)
        >
        10
    ):

        return False

    english_starters = [

        "who",
        "what",
        "when",
        "where",
        "why",
        "how",
        "which",

        "explain",
        "describe",

        "summarize",
        "summary",

        "tell me",
        "give me",

        "is there",
        "are there",

        "does it",
        "do they",

        "what does",
        "what is",

        "who is",
        "who was",

        "when was",
        "where is",

        "how many",
        "how much",
    ]

    arabic_starters = [

        "من",
        "مين",

        "ما",
        "ماذا",

        "ايه",
        "إيه",

        "متى",
        "امتى",
        "إمتى",

        "أين",
        "اين",
        "فين",

        "ليه",
        "لماذا",

        "ازاي",
        "إزاي",
        "كيف",

        "اشرح",
        "وضح",
        "وضّح",

        "لخص",
        "لخصه",

        "احكي",
        "قول",

        "مين هو",
        "مين هي",

        "ما هو",
        "ما هي",

        "ايه هو",
        "إيه هو",

        "ايه هي",
        "إيه هي",

        "كام",
        "كم",
    ]

    starters = (
        english_starters
        +
        arabic_starters
    )

    return any(
        q.startswith(
            starter
        )

        for starter
        in starters
    )


# =========================================================
# PDF KEYWORD OVERLAP
# =========================================================

def has_document_keyword_overlap(
    question,
    context,
):

    question_words = set(
        re.findall(
            r"[A-Za-z\u0600-\u06FF]{3,}",
            question.lower(),
        )
    )

    stop_words = {

        # English
        "who",
        "what",
        "when",
        "where",
        "why",
        "how",

        "which",

        "the",
        "this",
        "that",

        "with",
        "from",
        "about",

        "does",
        "have",
        "has",

        "are",
        "was",
        "were",

        "can",
        "could",
        "would",
        "should",

        "tell",
        "give",

        "there",

        # Arabic
        "هذا",
        "هذه",
        "ذلك",
        "تلك",

        "الذي",
        "التي",

        "على",
        "إلى",
        "الى",

        "في",
        "من",
        "عن",

        "كيف",
        "ماذا",

        "ليه",
        "لماذا",

        "ايه",
        "إيه",

        "مين",

        "قول",
        "اشرح",
        "وضح",
    }

    meaningful_words = (
        question_words
        -
        stop_words
    )

    if not meaningful_words:

        return False

    context_lower = (
        context.lower()
    )

    matches = [

        word

        for word
        in meaningful_words

        if word
        in context_lower
    ]

    return (
        len(matches)
        >=
        1
    )


# =========================================================
# PDF RETRIEVAL
# =========================================================

def retrieve_document_context(
    question,
    session_id,
    user_id,
    top_k=MAX_DOCUMENT_CONTEXT_CHUNKS,
):

    chunks = (
        get_session_document_chunks(
            session_id,
            user_id,
        )
    )

    if not chunks:

        return (
            "",
            0.0,
            [],
        )

    question_embedding = (
        create_embedding(
            question
        )
    )

    results = []

    for chunk in chunks:

        try:

            chunk_embedding = (
                create_embedding(
                    chunk[
                        "content"
                    ]
                )
            )

            score = (
                cosine_similarity(
                    question_embedding,
                    chunk_embedding,
                )
            )

            results.append(
                (
                    score,
                    chunk,
                )
            )

        except Exception as error:

            print(
                "Document chunk embedding error:",
                error,
            )

    results.sort(
        key=lambda item:
            item[0],

        reverse=True,
    )

    best_results = (
        results[
            :top_k
        ]
    )

    if not best_results:

        return (
            "",
            0.0,
            [],
        )

    context_parts = []

    filenames = []

    for (
        score,
        chunk
    ) in best_results:

        filename = (
            chunk[
                "filename"
            ]
        )

        if (
            filename
            not in filenames
        ):

            filenames.append(
                filename
            )

        context_parts.append(
            (
                f"File: {filename}\n\n"
                f"{chunk['content']}"
            )
        )

    context = (
        "\n\n---\n\n".join(
            context_parts
        )
    )

    return (
        context,

        best_results[
            0
        ][0],

        filenames,
    )


# =========================================================
# HISTORY MESSAGES
# =========================================================

def build_messages(
    system_prompt,
    user_prompt,
    session_id,
    user_id,
):

    messages = [
        {
            "role":
                "system",

            "content":
                system_prompt,
        }
    ]

    history = (
        get_history(
            session_id,
            user_id,
            limit=MAX_HISTORY_MESSAGES,
        )
    )

    for item in history:

        messages.append(
            {
                "role":
                    item[
                        "role"
                    ],

                "content":
                    item[
                        "content"
                    ],
            }
        )

    messages.append(
        {
            "role":
                "user",

            "content":
                user_prompt,
        }
    )

    return messages


# =========================================================
# QWEN
# =========================================================

def _run_qwen_generation(
    messages,
    max_new_tokens,
):

    formatted_prompt = (
        qwen_tokenizer
        .apply_chat_template(
            messages,

            tokenize=False,

            add_generation_prompt=True,
        )
    )

    inputs = (
        qwen_tokenizer(
            formatted_prompt,

            return_tensors="pt",

            truncation=True,

            max_length=(
                MAX_CHAT_INPUT_TOKENS
            ),
        )
    )

    inputs = {

        key:
            value.to(
                DEVICE
            )

        for key, value
        in inputs.items()

    }

    input_length = (
        inputs[
            "input_ids"
        ]
        .shape[1]
    )

    with torch.inference_mode():

        generated_ids = (
            qwen_model.generate(
                **inputs,

                max_new_tokens=(
                    max_new_tokens
                ),

                do_sample=False,

                num_beams=1,

                repetition_penalty=1.04,

                no_repeat_ngram_size=3,

                pad_token_id=(
                    qwen_tokenizer
                    .eos_token_id
                ),
            )
        )

    new_tokens = (
        generated_ids[
            0,
            input_length:
        ]
    )

    return (
        qwen_tokenizer.decode(
            new_tokens,

            skip_special_tokens=True,
        )
        .strip()
    )


def generate_qwen_response(
    system_prompt,
    user_prompt,
    language,
    session_id,
    user_id,
):

    if (
        language
        ==
        "ar"
    ):

        language_rule = """
أجب بالعربية فقط.

يمكن استخدام المصطلحات الإنجليزية الضرورية مثل:
Active Recall
GPA
AI
PDF

ممنوع استخدام الصينية أو اليابانية أو الكورية.
"""

    else:

        language_rule = """
Answer in English.

Do not output Chinese, Japanese or Korean characters.
"""

    full_system_prompt = (
        system_prompt
        +
        "\n"
        +
        language_rule
    )

    messages = (
        build_messages(
            full_system_prompt,
            user_prompt,
            session_id,
            user_id,
        )
    )

    answer = (
        _run_qwen_generation(
            messages,

            MAX_CHAT_OUTPUT_TOKENS,
        )
    )

    if (
        contains_east_asian_characters(
            answer
        )
    ):

        print(
            "East Asian characters detected. Retrying..."
        )

        if (
            language
            ==
            "ar"
        ):

            retry_instruction = """
أعد كتابة الإجابة بالعربية الطبيعية فقط.

يمكن إبقاء المصطلحات الإنجليزية الضرورية فقط.

ممنوع استخدام الصينية أو اليابانية أو الكورية.

أرسل الإجابة النهائية فقط.
"""

        else:

            retry_instruction = """
Rewrite the answer in clear English only.

Do not use Chinese, Japanese or Korean.

Return only the final answer.
"""

        retry_messages = [

            {
                "role":
                    "system",

                "content":
                    full_system_prompt,
            },

            {
                "role":
                    "user",

                "content":
                    (
                        retry_instruction
                        +
                        "\n\n"
                        +
                        user_prompt
                    ),
            },

        ]

        answer = (
            _run_qwen_generation(
                retry_messages,

                MAX_CHAT_OUTPUT_TOKENS,
            )
        )

        if (
            contains_east_asian_characters(
                answer
            )
        ):

            answer = (
                remove_east_asian_characters(
                    answer
                )
            )

    return answer.strip()


# =========================================================
# GENERAL AI
# =========================================================

def generate_general_answer(
    question,
    language,
    session_id,
    user_id,
):

    if (
        language
        ==
        "ar"
    ):

        system_prompt = """
أنت المساعد الذكي داخل Smart Academic Advisor.

ساعد المستخدم في:
- الأسئلة العامة.
- الدراسة والتعليم.
- العلوم.
- البرمجة.
- التكنولوجيا.
- الكتابة.
- مهارات التعلم.

استخدم سياق المحادثة السابقة لفهم أسئلة المتابعة.

إذا كان السؤال عامًا فاستخدم معرفتك العامة.

لا تخترع سياسات أو لوائح جامعية خاصة.
"""

    else:

        system_prompt = """
You are the intelligent assistant inside Smart Academic Advisor.

Help with:
- General knowledge.
- Studying and education.
- Science.
- Programming.
- Technology.
- Writing.
- Learning skills.

Use previous conversation context for follow-up questions.

For general questions, use your general knowledge.

Do not invent university-specific policies.
"""

    return (
        generate_qwen_response(
            system_prompt,
            question,
            language,
            session_id,
            user_id,
        )
    )


# =========================================================
# UNIVERSITY RAG
# =========================================================

def generate_rag_answer(
    question,
    context,
    language,
    session_id,
    user_id,
):

    if (
        language
        ==
        "ar"
    ):

        system_prompt = """
أنت مساعد أكاديمي جامعي.

لديك معلومات رسمية مسترجعة من قاعدة معرفة الجامعة.

استخدم هذه المعلومات كمصدر أساسي للإجابة.

لا تخترع سياسات أو متطلبات أو مواعيد غير موجودة.

اجعل الإجابة واضحة ومباشرة.
"""

        user_prompt = f"""
معلومات الجامعة:

{context}


سؤال الطالب:

{question}


أجب اعتمادًا على معلومات الجامعة السابقة.
"""

    else:

        system_prompt = """
You are a university academic assistant.

You have official university information retrieved from the university knowledge base.

Use the provided information as the source of truth.

Do not invent university rules, requirements or deadlines.
"""

        user_prompt = f"""
University Knowledge:

{context}


Student Question:

{question}


Answer using the university information above.
"""

    return (
        generate_qwen_response(
            system_prompt,
            user_prompt,
            language,
            session_id,
            user_id,
        )
    )


# =========================================================
# PDF RAG ANSWER
# =========================================================

def generate_document_answer(
    question,
    context,
    language,
    session_id,
    user_id,
):

    if (
        language
        ==
        "ar"
    ):

        system_prompt = """
أنت مساعد ذكي يجيب عن ملفات PDF التي رفعها المستخدم داخل المحادثة الحالية.

القواعد:

- اعتمد على محتوى الـPDF المسترجع.
- إذا كان سؤال المستخدم مختصرًا أو سؤال متابعة فاستفد من سياق المحادثة السابقة.
- افترض أن كلمات مثل "هو" أو "هي" أو "ده" أو "هذا" قد تشير إلى موضوع الملف إذا كان السياق يدعم ذلك.
- لا تخترع معلومات غير موجودة في الملف.
- إذا كانت الإجابة غير موجودة في المحتوى المسترجع قل ذلك بوضوح.
- أجب بشكل طبيعي وواضح.
"""

        user_prompt = f"""
محتوى مسترجع من ملف PDF الخاص بالمستخدم:

{context}


سؤال المستخدم:

{question}


أجب اعتمادًا على محتوى الملف وسياق المحادثة.
"""

    else:

        system_prompt = """
You answer questions about PDFs uploaded by the user in the current chat.

Rules:

- Use the retrieved PDF content as the primary source.
- Understand short or ambiguous follow-up questions using conversation context.
- Pronouns such as "he", "she", "it", "this", or "they" may refer to people or concepts in the uploaded PDF when the context supports that.
- Do not invent unsupported information.
- If the retrieved PDF content does not support the answer, clearly say so.
"""

        user_prompt = f"""
Retrieved content from the user's PDF:

{context}


User question:

{question}


Answer using the PDF content and the conversation context.
"""

    return (
        generate_qwen_response(
            system_prompt,
            user_prompt,
            language,
            session_id,
            user_id,
        )
    )


# =========================================================
# MAIN PIPELINE
# =========================================================

def answer_question(
    question,
    session_id=None,
    user_id=None,
):

    question = (
        normalize_text(
            question
        )
    )

    user_id = (
        user_id
        or
        "anonymous"
    ).strip() or "anonymous"

    session_id = (
        ensure_session(
            session_id=session_id,
            user_id=user_id,
        )
    )

    if not question:

        return {
            "answer":
                "Please enter a question.",

            "context":
                None,

            "similarity_score":
                0.0,

            "mode":
                "general",

            "session_id":
                session_id,
        }

    language = (
        detect_language(
            question
        )
    )

    print(
        "\n================================"
    )

    print(
        "Chat session:",
        session_id,
    )

    print(
        "Chat user:",
        user_id,
    )

    print(
        "Chat question:",
        question,
    )

    print(
        "Detected language:",
        language,
    )


    # =====================================================
    # SMALL TALK
    # =====================================================

    if (
        is_small_talk(
            question
        )
    ):

        print(
            "Chat mode: SMALL TALK"
        )

        answer = (
            generate_small_talk_response(
                question,
                language,
            )
        )

        save_message(
            session_id,
            user_id,
            "user",
            question,
        )

        save_message(
            session_id,
            user_id,
            "assistant",
            answer,
        )

        return {
            "answer":
                answer,

            "context":
                None,

            "similarity_score":
                0.0,

            "mode":
                "small_talk",

            "session_id":
                session_id,
        }


    # =====================================================
    # PDF RAG
    # =====================================================

    document_context = ""

    document_score = 0.0

    document_filenames = []


    try:

        (
            document_context,
            document_score,
            document_filenames,

        ) = retrieve_document_context(

            question,
            session_id,
            user_id,

        )

    except Exception as error:

        print(
            "Document retrieval error:",
            error,
        )


    print(
        "Document similarity:",
        round(
            document_score,
            3,
        ),
    )


    document_related = (
        is_document_related_question(
            question
        )
    )


    document_followup = (
        is_ambiguous_document_followup(
            question
        )
    )


    document_keyword_match = (
        has_document_keyword_overlap(
            question,
            document_context,
        )

        if document_context

        else False
    )


    print(
        "Document explicit:",
        document_related,
    )


    print(
        "Document follow-up:",
        document_followup,
    )


    print(
        "Document keyword match:",
        document_keyword_match,
    )


    use_document_rag = (
        bool(
            document_context
        )
        and
        (
            # المستخدم ذكر الملف صراحة.
            document_related

            or

            # تشابه قوي مع محتوى الملف.
            document_score
            >=
            DOCUMENT_SIMILARITY_THRESHOLD

            or

            # سؤال قصير / مبهم ومعاه
            # تشابه مقبول بالملف.
            (
                document_followup
                and
                document_score
                >=
                DOCUMENT_FOLLOWUP_THRESHOLD
            )

            or

            # كلمة رئيسية من السؤال
            # موجودة بالفعل في المحتوى المسترجع.
            document_keyword_match
        )
    )


    if use_document_rag:

        print(
            "Chat mode: SESSION PDF RAG"
        )

        try:

            answer = (
                generate_document_answer(
                    question,
                    document_context,
                    language,
                    session_id,
                    user_id,
                )
            )

            save_message(
                session_id,
                user_id,
                "user",
                question,
            )

            save_message(
                session_id,
                user_id,
                "assistant",
                answer,
            )

            if (
                DEVICE.type
                ==
                "cuda"
            ):

                torch.cuda.empty_cache()

            return {
                "answer":
                    answer,

                "context":
                    document_context,

                "similarity_score":
                    round(
                        document_score,
                        3,
                    ),

                "mode":
                    "document_rag",

                "session_id":
                    session_id,

                "documents":
                    document_filenames,
            }

        except Exception as error:

            print(
                "Document answer error:",
                error,
            )


    # =====================================================
    # UNIVERSITY RAG
    # =====================================================

    university_related = (
        is_university_related(
            question
        )
    )


    print(
        "University-related:",
        university_related,
    )


    context = ""

    score = 0.0


    if university_related:

        try:

            context, score = (
                retrieve_context(
                    question
                )
            )

        except Exception as error:

            print(
                "University retrieval error:",
                error,
            )


    print(
        "University similarity:",
        round(
            score,
            3,
        ),
    )


    # =====================================================
    # UNIVERSITY OR GENERAL AI
    # =====================================================

    try:

        if (
            university_related
            and
            context
            and
            score
            >=
            KNOWLEDGE_THRESHOLD
        ):

            print(
                "Chat mode: UNIVERSITY RAG"
            )

            answer = (
                generate_rag_answer(
                    question,
                    context,
                    language,
                    session_id,
                    user_id,
                )
            )

            mode = (
                "rag"
            )

            response_context = (
                context
            )

            final_score = (
                score
            )

        else:

            print(
                "Chat mode: GENERAL AI"
            )

            answer = (
                generate_general_answer(
                    question,
                    language,
                    session_id,
                    user_id,
                )
            )

            mode = (
                "general"
            )

            response_context = (
                None
            )

            final_score = (
                0.0
            )

    except RuntimeError as error:

        print(
            "Chat GPU error:",
            error,
        )

        if (
            DEVICE.type
            ==
            "cuda"
        ):

            torch.cuda.empty_cache()

        answer = (
            "حصلت مشكلة أثناء توليد الإجابة. حاول مرة أخرى."

            if language == "ar"

            else

            "The AI model could not generate a response right now."
        )

        mode = (
            "error"
        )

        response_context = (
            None
        )

        final_score = (
            0.0
        )

    except Exception as error:

        print(
            "Chat generation error:",
            error,
        )

        answer = (
            "حدث خطأ أثناء توليد الإجابة. حاول مرة أخرى."

            if language == "ar"

            else

            "An error occurred while generating the answer."
        )

        mode = (
            "error"
        )

        response_context = (
            None
        )

        final_score = (
            0.0
        )


    # =====================================================
    # SAVE HISTORY
    # =====================================================

    save_message(
        session_id,
        user_id,
        "user",
        question,
    )

    save_message(
        session_id,
        user_id,
        "assistant",
        answer,
    )


    if (
        DEVICE.type
        ==
        "cuda"
    ):

        torch.cuda.empty_cache()


    return {
        "answer":
            answer,

        "context":
            response_context,

        "similarity_score":
            round(
                final_score,
                3,
            ),

        "mode":
            mode,

        "session_id":
            session_id,
    }