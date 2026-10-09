const API_BASE = "http://127.0.0.1:8000";


/* =========================
   LOGIN PROTECTION
========================= */

if (
    localStorage.getItem(
        "studentLoggedIn"
    ) !== "true"
) {
    window.location.href =
        "login.html";
}


/* =========================
   STUDENT DATA
========================= */

const studentName =
    localStorage.getItem(
        "studentName"
    ) || "Student";


const studentEmail =
    localStorage.getItem(
        "studentEmail"
    ) || "student@university.edu";


const savedTheme =
    localStorage.getItem(
        "theme"
    ) || "light";


const CHAT_SESSION_STORAGE_KEY =
    `chatSessionId:${studentEmail}`;


function getChatUserId() {

    return (
        studentEmail
        ||
        "anonymous"
    );
}


/* =========================
   PAGE LOAD
========================= */

window.addEventListener(
    "DOMContentLoaded",
    async function () {

        applyTheme(
            savedTheme
        );


        const nameElements = [

            document.getElementById(
                "studentName"
            ),

            document.getElementById(
                "topStudentName"
            ),

            document.getElementById(
                "heroStudentName"
            )

        ];


        nameElements.forEach(
            element => {

                if (element) {

                    element.innerText =
                        studentName;

                }

            }
        );


        const emailElements = [

            document.getElementById(
                "studentEmail"
            ),

            document.getElementById(
                "topStudentEmail"
            )

        ];


        emailElements.forEach(
            element => {

                if (element) {

                    element.innerText =
                        studentEmail;

                }

            }
        );


        const avatar =
            document.getElementById(
                "studentAvatar"
            );


        if (avatar) {

            avatar.innerText =
                studentName
                    .charAt(0)
                    .toUpperCase();

        }


        await initializeChatSession();

    }
);


/* =========================
   PAGE NAVIGATION
========================= */

const pageTitles = {

    dashboard:
        "Dashboard",

    pdf:
        "PDF Summarizer",

    chatbot:
        "Academic Chatbot",

    gpa:
        "GPA Calculator"

};


function showPage(
    pageId,
    button
) {

    const pages =
        document.querySelectorAll(
            ".page"
        );


    pages.forEach(
        page => {

            page.classList.remove(
                "active-page"
            );

        }
    );


    const selectedPage =
        document.getElementById(
            pageId
        );


    if (selectedPage) {

        selectedPage.classList.add(
            "active-page"
        );

    }


    const title =
        document.getElementById(
            "pageTitle"
        );


    if (title) {

        title.innerText =
            pageTitles[pageId];

    }


    const navItems =
        document.querySelectorAll(
            ".nav-item"
        );


    navItems.forEach(
        item => {

            item.classList.remove(
                "active"
            );

        }
    );


    if (button) {

        button.classList.add(
            "active"
        );

    }


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


function openFeature(
    pageId
) {

    const navItems =
        document.querySelectorAll(
            ".nav-item"
        );


    let targetButton =
        null;


    navItems.forEach(
        item => {

            const action =
                item.getAttribute(
                    "onclick"
                );


            if (
                action
                &&
                action.includes(
                    `'${pageId}'`
                )
            ) {

                targetButton =
                    item;

            }

        }
    );


    showPage(
        pageId,
        targetButton
    );

}


/* =========================
   THEME
========================= */

function toggleTheme() {

    const isDark =
        document.body
            .classList
            .contains(
                "dark-mode"
            );


    const newTheme =
        isDark
            ? "light"
            : "dark";


    applyTheme(
        newTheme
    );


    localStorage.setItem(
        "theme",
        newTheme
    );

}


function applyTheme(
    theme
) {

    const toggleButton =
        document.getElementById(
            "themeToggle"
        );


    if (
        theme === "dark"
    ) {

        document.body.classList.add(
            "dark-mode"
        );


        if (toggleButton) {

            toggleButton.innerText =
                "☀️";

        }

    }

    else {

        document.body.classList.remove(
            "dark-mode"
        );


        if (toggleButton) {

            toggleButton.innerText =
                "🌙";

        }

    }

}


/* =========================
   PDF SUMMARIZER
========================= */

async function summarizePDF() {

    const fileInput =
        document.getElementById(
            "pdfFile"
        );


    const resultBox =
        document.getElementById(
            "pdfResult"
        );


    if (
        !fileInput
        ||
        !fileInput.files.length
    ) {

        if (resultBox) {

            resultBox.innerText =
                "Please select a PDF file first.";

        }

        return;

    }


    const file =
        fileInput.files[0];


    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    if (resultBox) {

        resultBox.innerHTML = `
            <div class="loading-message">
                Reading PDF and generating AI summary...
            </div>
        `;

    }


    try {

        const response =
            await fetch(
                `${API_BASE}/api/pdf/summarize`,
                {
                    method:
                        "POST",

                    body:
                        formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            if (resultBox) {

                resultBox.innerText =
                    data.detail
                    ||
                    "Unable to summarize this PDF.";

            }

            return;

        }


        const summaryText =
            data.summary
            ||
            "No summary returned.";


        const isArabic =
            /[\u0600-\u06FF]/
                .test(
                    summaryText
                );


        if (!resultBox) {

            return;

        }


        resultBox.innerHTML = `

            <div class="result-meta">

                <div class="result-file">

                    <span class="result-label">
                        FILE
                    </span>

                    <strong>
                        ${
                            escapeHTML(
                                data.filename
                                ||
                                file.name
                            )
                        }
                    </strong>

                </div>


                <div class="result-stats">

                    <div>

                        <span class="result-label">
                            PAGES
                        </span>

                        <strong>
                            ${
                                data.pages
                                ??
                                "-"
                            }
                        </strong>

                    </div>


                    <div>

                        <span class="result-label">
                            LANGUAGE
                        </span>

                        <strong>
                            ${
                                escapeHTML(
                                    data.language
                                    ||
                                    (
                                        isArabic
                                            ? "Arabic"
                                            : "English"
                                    )
                                )
                            }
                        </strong>

                    </div>


                    <div>

                        <span class="result-label">
                            CHARACTERS
                        </span>

                        <strong>
                            ${
                                data.characters_extracted
                                ??
                                0
                            }
                        </strong>

                    </div>

                </div>

            </div>


            <div
                class="academic-summary ${
                    isArabic
                        ? "rtl-summary"
                        : "ltr-summary"
                }"
            >

                <div class="summary-heading">

                    <div class="summary-icon">
                        ♜
                    </div>

                    <div>

                        <span class="section-kicker">
                            AI GENERATED
                        </span>

                        <h3>
                            ${
                                isArabic
                                    ? "الملخص الأكاديمي"
                                    : "Academic Summary"
                            }
                        </h3>

                    </div>

                </div>


                <div class="summary-body">

                    ${
                        formatSummary(
                            summaryText
                        )
                    }

                </div>

            </div>
        `;

    }

    catch (error) {

        if (resultBox) {

            resultBox.innerText =
                "Could not connect to the AI server. Make sure FastAPI is running.";

        }


        console.error(
            "PDF summary error:",
            error
        );

    }

}


/* =========================
   SUMMARY FORMATTER
========================= */

function formatSummary(
    text
) {

    const lines =
        String(text)
            .replace(
                /\r\n/g,
                "\n"
            )
            .split(
                "\n"
            );


    let html =
        "";


    let inList =
        false;


    let paragraphBuffer =
        [];


    function flushParagraph() {

        if (
            !paragraphBuffer.length
        ) {

            return;

        }


        html += `
            <p>
                ${
                    paragraphBuffer.join(
                        "<br>"
                    )
                }
            </p>
        `;


        paragraphBuffer =
            [];

    }


    function closeList() {

        if (inList) {

            html +=
                "</ul>";


            inList =
                false;

        }

    }


    lines.forEach(
        rawLine => {

            const line =
                rawLine.trim();


            if (!line) {

                flushParagraph();

                closeList();

                return;

            }


            const h3Match =
                line.match(
                    /^###\s+(.+)$/
                );


            const h2Match =
                line.match(
                    /^##\s+(.+)$/
                );


            const h1Match =
                line.match(
                    /^#\s+(.+)$/
                );


            const bulletMatch =
                line.match(
                    /^(?:[-*•]\s+)(.+)$/
                );


            const numberedMatch =
                line.match(
                    /^\d+[.)]\s+(.+)$/
                );


            if (h3Match) {

                flushParagraph();

                closeList();


                html += `
                    <h3>
                        ${
                            formatInlineText(
                                h3Match[1]
                            )
                        }
                    </h3>
                `;


                return;

            }


            if (
                h2Match
                ||
                h1Match
            ) {

                flushParagraph();

                closeList();


                const heading =
                    h2Match
                        ? h2Match[1]
                        : h1Match[1];


                html += `
                    <h2>
                        ${
                            formatInlineText(
                                heading
                            )
                        }
                    </h2>
                `;


                return;

            }


            if (
                bulletMatch
                ||
                numberedMatch
            ) {

                flushParagraph();


                if (!inList) {

                    html +=
                        "<ul>";


                    inList =
                        true;

                }


                const itemText =
                    bulletMatch
                        ? bulletMatch[1]
                        : numberedMatch[1];


                html += `
                    <li>
                        ${
                            formatInlineText(
                                itemText
                            )
                        }
                    </li>
                `;


                return;

            }


            closeList();


            paragraphBuffer.push(
                formatInlineText(
                    line
                )
            );

        }
    );


    flushParagraph();

    closeList();


    return html;

}


function formatInlineText(
    text
) {

    let safe =
        escapeHTML(
            text
        );


    safe = safe.replace(
        /\*\*(.+?)\*\*/g,
        "<strong>$1</strong>"
    );


    safe = safe.replace(
        /`(.+?)`/g,
        "<code>$1</code>"
    );


    return safe;

}


/* =========================
   CREATE CHAT SESSION
========================= */

async function createChatSession() {

    const response =
        await fetch(
            `${API_BASE}/api/chatbot/session`,
            {
                method:
                    "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(
                        {
                            user_id:
                                getChatUserId()
                        }
                    )
            }
        );


    const data =
        await response.json();


    if (!response.ok) {

        throw new Error(
            data.detail
            ||
            "Could not create chat session."
        );

    }


    localStorage.setItem(
        CHAT_SESSION_STORAGE_KEY,
        data.session_id
    );


    return data.session_id;

}


/* =========================
   GET OR CREATE SESSION
========================= */

async function getOrCreateChatSession() {

    const existingSession =
        localStorage.getItem(
            CHAT_SESSION_STORAGE_KEY
        );


    if (existingSession) {

        return existingSession;

    }


    return await createChatSession();

}


/* =========================
   INITIALIZE CHAT
========================= */

async function initializeChatSession() {

    try {

        const sessionId =
            await getOrCreateChatSession();


        await loadChatHistory(
            sessionId
        );


        await refreshChatSessions(
            sessionId
        );

    }

    catch (error) {

        console.error(
            "Chat session initialization error:",
            error
        );

    }

}


/* =========================
   LOAD CHAT HISTORY
========================= */

async function loadChatHistory(
    sessionId
) {

    const messages =
        document.getElementById(
            "chatMessages"
        );


    if (!messages) {

        return;

    }


    try {

        const response =
            await fetch(
                `${API_BASE}/api/chatbot/history/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(getChatUserId())}`
            );


        if (!response.ok) {

            localStorage.removeItem(
                CHAT_SESSION_STORAGE_KEY
            );


            const newSessionId =
                await createChatSession();


            if (
                newSessionId
                !==
                sessionId
            ) {

                await loadChatHistory(
                    newSessionId
                );

            }


            return;

        }


        const data =
            await response.json();


        const history =
            data.messages
            ||
            [];


        /*
         * مهم:
         * نحمل ملفات الـPDF حتى لو
         * المحادثة لا تحتوي رسائل.
         */

        await loadChatDocuments(
            sessionId
        );


        if (!history.length) {

            showFreshChatGreeting(
                messages
            );


            return;

        }


        messages.innerHTML =
            "";


        history.forEach(
            item => {

                if (
                    item.role
                    ===
                    "user"
                ) {

                    addUserMessage(
                        messages,
                        item.content
                    );

                }

                else {

                    addBotMessage(
                        messages,
                        item.content
                    );

                }

            }
        );


        scrollChatToBottom(
            messages
        );

    }

    catch (error) {

        console.error(
            "Load chat history error:",
            error
        );

    }

}


/* =========================
   SAVED CHATS
========================= */

async function refreshChatSessions(
    activeSessionId = null
) {

    const select =
        document.getElementById(
            "chatSessionSelect"
        );


    if (!select) {

        return;

    }


    try {

        const response =
            await fetch(
                `${API_BASE}/api/chatbot/sessions?user_id=${encodeURIComponent(getChatUserId())}`
            );


        if (!response.ok) {

            return;

        }


        const data =
            await response.json();


        const sessions =
            data.sessions
            ||
            [];


        select.innerHTML = `
            <option value="">
                Saved Chats
            </option>
        `;


        sessions.forEach(
            session => {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    session.session_id;


                let title =
                    session.first_message
                    ||
                    "New conversation";


                if (
                    title.length
                    >
                    42
                ) {

                    title =
                        title.slice(
                            0,
                            42
                        )
                        +
                        "…";

                }


                option.textContent =
                    title;


                if (
                    session.session_id
                    ===
                    activeSessionId
                ) {

                    option.selected =
                        true;

                }


                select.appendChild(
                    option
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Load saved chats error:",
            error
        );

    }

}


/* =========================
   SWITCH SAVED CHAT
========================= */

async function switchChatSession(
    sessionId
) {

    if (!sessionId) {

        return;

    }


    localStorage.setItem(
        CHAT_SESSION_STORAGE_KEY,
        sessionId
    );


    await loadChatHistory(
        sessionId
    );


    await refreshChatSessions(
        sessionId
    );

}


/* =========================
   CHAT PDF DOCUMENTS
========================= */

async function loadChatDocuments(
    sessionId
) {

    const container =
        document.getElementById(
            "chatDocuments"
        );


    if (!container) {

        return;

    }


    if (!sessionId) {

        container.innerHTML =
            "";

        return;

    }


    try {

        const response =
            await fetch(
                `${API_BASE}/api/chatbot/documents/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(getChatUserId())}`
            );


        if (!response.ok) {

            container.innerHTML =
                "";

            return;

        }


        const data =
            await response.json();


        const documents =
            data.documents
            ||
            [];


        if (!documents.length) {

            container.innerHTML =
                "";

            return;

        }


        container.innerHTML =
            documents
                .map(
                    item => {

                        const filename =
                            escapeHTML(
                                item.filename
                                ||
                                "PDF"
                            );


                        const pages =
                            item.pages
                            ??
                            "-";


                        return `
                            <div class="chat-document-chip">

                                <span class="chat-document-icon">
                                    📄
                                </span>

                                <strong title="${filename}">
                                    ${filename}
                                </strong>

                                <small>
                                    ${pages} pages
                                </small>

                            </div>
                        `;

                    }
                )
                .join("");

    }

    catch (error) {

        console.error(
            "Load chat documents error:",
            error
        );


        container.innerHTML =
            "";

    }

}


/* =========================
   UPLOAD PDF TO CHAT
========================= */

async function uploadChatPDF() {

    const fileInput =
        document.getElementById(
            "chatPdfFile"
        );


    const messages =
        document.getElementById(
            "chatMessages"
        );


    if (
        !fileInput
        ||
        !fileInput.files.length
        ||
        !messages
    ) {

        return;

    }


    const file =
        fileInput.files[0];


    if (
        !file.name
            .toLowerCase()
            .endsWith(
                ".pdf"
            )
    ) {

        addBotMessage(
            messages,
            "Please select a PDF file."
        );


        fileInput.value =
            "";


        return;

    }


    /*
     * Frontend quick size check.
     * Backend هيعمل check برضه.
     */

    const MAX_CHAT_PDF_MB =
        20;


    const maxBytes =
        MAX_CHAT_PDF_MB
        *
        1024
        *
        1024;


    if (
        file.size
        >
        maxBytes
    ) {

        addBotMessage(
            messages,
            `The PDF is too large. Maximum size is ${MAX_CHAT_PDF_MB} MB.`
        );


        fileInput.value =
            "";


        return;

    }


    let uploadRow =
        null;


    try {

        const sessionId =
            await getOrCreateChatSession();


        uploadRow =
            addThinkingMessage(
                messages
            );


        const thinkingMessage =
            uploadRow.querySelector(
                ".thinking"
            );


        if (thinkingMessage) {

            thinkingMessage.innerText =
                `Reading ${file.name}...`;

        }


        scrollChatToBottom(
            messages
        );


        const formData =
            new FormData();


        formData.append(
            "file",
            file
        );


        formData.append(
            "session_id",
            sessionId
        );


        formData.append(
            "user_id",
            getChatUserId()
        );


        const response =
            await fetch(
                `${API_BASE}/api/chatbot/upload-pdf`,
                {
                    method:
                        "POST",

                    body:
                        formData
                }
            );


        let data =
            {};


        try {

            data =
                await response.json();

        }

        catch {

            data =
                {};

        }


        if (
            uploadRow
            &&
            uploadRow.parentNode
        ) {

            uploadRow.remove();

        }


        if (!response.ok) {

            addBotMessage(
                messages,
                data.detail
                ||
                "Could not attach this PDF."
            );


            return;

        }


        addBotMessage(
            messages,
            `📄 **${data.filename}** attached successfully.

Pages: ${data.pages}
Text chunks: ${data.chunks}

You can now ask me questions about this PDF.`
        );


        await loadChatDocuments(
            sessionId
        );


        await refreshChatSessions(
            sessionId
        );


        scrollChatToBottom(
            messages
        );

    }

    catch (error) {

        if (
            uploadRow
            &&
            uploadRow.parentNode
        ) {

            uploadRow.remove();

        }


        addBotMessage(
            messages,
            "Could not upload this PDF. Make sure the AI server is running."
        );


        console.error(
            "Chat PDF upload error:",
            error
        );

    }

    finally {

        fileInput.value =
            "";

    }

}


/* =========================
   FRESH CHAT GREETING
========================= */

function showFreshChatGreeting(
    messages
) {

    messages.innerHTML = `

        <div class="message-row bot-row">

            <div class="message-avatar">
                ♞
            </div>

            <div class="message bot-message">
                Hello! I'm your academic advisor.
                Ask me anything about studying,
                university topics or general knowledge.
                You can also attach a PDF and ask questions about it.
            </div>

        </div>
    `;

}


/* =========================
   ASK CHATBOT
========================= */

async function askChatbot() {

    const input =
        document.getElementById(
            "chatQuestion"
        );


    const messages =
        document.getElementById(
            "chatMessages"
        );


    if (
        !input
        ||
        !messages
    ) {

        return;

    }


    const question =
        input.value.trim();


    if (!question) {

        return;

    }


    addUserMessage(
        messages,
        question
    );


    input.value =
        "";


    input.disabled =
        true;


    const thinkingRow =
        addThinkingMessage(
            messages
        );


    scrollChatToBottom(
        messages
    );


    try {

        const sessionId =
            await getOrCreateChatSession();


        const response =
            await fetch(
                `${API_BASE}/api/chatbot/ask`,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                question:
                                    question,

                                session_id:
                                    sessionId,

                                user_id:
                                    getChatUserId()
                            }
                        )
                }
            );


        let data =
            {};


        try {

            data =
                await response.json();

        }

        catch {

            data =
                {};

        }


        if (
            thinkingRow
            &&
            thinkingRow.parentNode
        ) {

            thinkingRow.remove();

        }


        if (!response.ok) {

            addBotMessage(
                messages,
                data.detail
                ||
                "I could not answer that question."
            );


            return;

        }


        const finalSessionId =
            data.session_id
            ||
            sessionId;


        if (
            finalSessionId
            !==
            sessionId
        ) {

            localStorage.setItem(
                CHAT_SESSION_STORAGE_KEY,
                finalSessionId
            );

        }


        addBotMessage(
            messages,
            data.answer
            ||
            "I could not find an answer."
        );


        scrollChatToBottom(
            messages
        );


        await refreshChatSessions(
            finalSessionId
        );


        /*
         * مهم لو الرد مرتبط بملف PDF.
         * نخلي شريط الملفات متزامن.
         */

        await loadChatDocuments(
            finalSessionId
        );

    }

    catch (error) {

        if (
            thinkingRow
            &&
            thinkingRow.parentNode
        ) {

            thinkingRow.remove();

        }


        addBotMessage(
            messages,
            "Could not connect to the academic advisor server."
        );


        console.error(
            "Chat error:",
            error
        );

    }

    finally {

        input.disabled =
            false;


        input.focus();

    }

}


/* =========================
   NEW CHAT
========================= */

async function clearChat() {

    const messages =
        document.getElementById(
            "chatMessages"
        );


    const input =
        document.getElementById(
            "chatQuestion"
        );


    const documents =
        document.getElementById(
            "chatDocuments"
        );


    try {

        const newSessionId =
            await createChatSession();


        if (messages) {

            showFreshChatGreeting(
                messages
            );

        }


        if (documents) {

            documents.innerHTML =
                "";

        }


        const pdfInput =
            document.getElementById(
                "chatPdfFile"
            );


        if (pdfInput) {

            pdfInput.value =
                "";

        }


        if (input) {

            input.value =
                "";


            input.focus();

        }


        await refreshChatSessions(
            newSessionId
        );


        console.log(
            "New chat session:",
            newSessionId
        );

    }

    catch (error) {

        console.error(
            "New chat error:",
            error
        );


        if (messages) {

            addBotMessage(
                messages,
                "I could not start a new conversation right now."
            );

        }

    }

}


/* =========================
   USER MESSAGE
========================= */

function addUserMessage(
    container,
    text
) {

    const row =
        document.createElement(
            "div"
        );


    row.className =
        "message-row";


    const isArabic =
        /[\u0600-\u06FF]/
            .test(
                text
            );


    row.innerHTML = `

        <div
            class="message user-message ${
                isArabic
                    ? "chat-rtl"
                    : "chat-ltr"
            }"
        >

            ${
                escapeHTML(
                    text
                )
            }

        </div>
    `;


    container.appendChild(
        row
    );

}


/* =========================
   BOT MESSAGE
========================= */

function addBotMessage(
    container,
    text
) {

    const row =
        document.createElement(
            "div"
        );


    row.className =
        "message-row bot-row";


    const isArabic =
        /[\u0600-\u06FF]/
            .test(
                text
            );


    row.innerHTML = `

        <div class="message-avatar">
            ♞
        </div>

        <div
            class="message bot-message ${
                isArabic
                    ? "chat-rtl"
                    : "chat-ltr"
            }"
        >

            ${
                formatChatMessage(
                    text
                )
            }

        </div>
    `;


    container.appendChild(
        row
    );

}


/* =========================
   CHAT MARKDOWN
========================= */

function formatChatMessage(
    text
) {

    const lines =
        String(text)
            .replace(
                /\r\n/g,
                "\n"
            )
            .split(
                "\n"
            );


    let html =
        "";


    let listType =
        null;


    let paragraph =
        [];


    function flushParagraph() {

        if (
            !paragraph.length
        ) {

            return;

        }


        html += `
            <p>
                ${
                    paragraph.join(
                        "<br>"
                    )
                }
            </p>
        `;


        paragraph =
            [];

    }


    function closeList() {

        if (
            listType
            ===
            "ul"
        ) {

            html +=
                "</ul>";

        }


        if (
            listType
            ===
            "ol"
        ) {

            html +=
                "</ol>";

        }


        listType =
            null;

    }


    lines.forEach(
        rawLine => {

            const line =
                rawLine.trim();


            if (!line) {

                flushParagraph();

                closeList();

                return;

            }


            const heading =
                line.match(
                    /^#{1,3}\s+(.+)$/
                );


            const bullet =
                line.match(
                    /^(?:[-*•]\s+)(.+)$/
                );


            const numberedItem =
                line.match(
                    /^\d+[.)]\s+(.+)$/
                );


            if (heading) {

                flushParagraph();

                closeList();


                html += `
                    <strong class="chat-heading">
                        ${
                            formatChatInline(
                                heading[1]
                            )
                        }
                    </strong>
                `;


                return;

            }


            if (bullet) {

                flushParagraph();


                if (
                    listType
                    !==
                    "ul"
                ) {

                    closeList();

                    html +=
                        "<ul>";


                    listType =
                        "ul";

                }


                html += `
                    <li>
                        ${
                            formatChatInline(
                                bullet[1]
                            )
                        }
                    </li>
                `;


                return;

            }


            if (numberedItem) {

                flushParagraph();


                if (
                    listType
                    !==
                    "ol"
                ) {

                    closeList();

                    html +=
                        "<ol>";


                    listType =
                        "ol";

                }


                html += `
                    <li>
                        ${
                            formatChatInline(
                                numberedItem[1]
                            )
                        }
                    </li>
                `;


                return;

            }


            closeList();


            paragraph.push(
                formatChatInline(
                    line
                )
            );

        }
    );


    flushParagraph();

    closeList();


    return html;

}


function formatChatInline(
    text
) {

    let safe =
        escapeHTML(
            text
        );


    safe = safe.replace(
        /\*\*(.+?)\*\*/g,
        "<strong>$1</strong>"
    );


    safe = safe.replace(
        /`(.+?)`/g,
        "<code>$1</code>"
    );


    return safe;

}


/* =========================
   THINKING
========================= */

function addThinkingMessage(
    container
) {

    const row =
        document.createElement(
            "div"
        );


    row.className =
        "message-row bot-row";


    row.innerHTML = `

        <div class="message-avatar">
            ♞
        </div>

        <div class="message bot-message thinking">
            Thinking...
        </div>
    `;


    container.appendChild(
        row
    );


    return row;

}


function scrollChatToBottom(
    container
) {

    if (!container) {

        return;

    }


    container.scrollTop =
        container.scrollHeight;

}


/* =========================
   ENTER TO SEND
========================= */

document.addEventListener(
    "keydown",
    function (
        event
    ) {

        if (
            event.key === "Enter"
            &&
            !event.shiftKey
        ) {

            const activePage =
                document.querySelector(
                    "#chatbot.active-page"
                );


            if (!activePage) {

                return;

            }


            const input =
                document.getElementById(
                    "chatQuestion"
                );


            if (
                document.activeElement
                ===
                input
            ) {

                event.preventDefault();


                askChatbot();

            }

        }

    }
);


/* =========================
   GPA
========================= */

function addCourse() {

    const container =
        document.getElementById(
            "coursesContainer"
        );


    if (!container) {

        return;

    }


    const row =
        document.createElement(
            "div"
        );


    row.className =
        "course-row";


    row.innerHTML = `

        <input
            type="text"
            placeholder="Course Name"
            class="course-name"
        >

        <select class="course-grade">

            <option value="A+">A+</option>
            <option value="A">A</option>
            <option value="A-">A-</option>

            <option value="B+">B+</option>
            <option value="B">B</option>
            <option value="B-">B-</option>

            <option value="C+">C+</option>
            <option value="C">C</option>
            <option value="C-">C-</option>

            <option value="D+">D+</option>
            <option value="D">D</option>

            <option value="F">F</option>

        </select>

        <input
            type="number"
            placeholder="Credit Hours"
            class="course-hours"
            min="1"
        >
    `;


    container.appendChild(
        row
    );

}


async function calculateGPA() {

    const names =
        document.querySelectorAll(
            ".course-name"
        );


    const grades =
        document.querySelectorAll(
            ".course-grade"
        );


    const hours =
        document.querySelectorAll(
            ".course-hours"
        );


    const resultBox =
        document.getElementById(
            "gpaResult"
        );


    const courses =
        [];


    for (
        let i = 0;
        i < names.length;
        i++
    ) {

        const courseName =
            names[i]
                .value
                .trim();


        const creditHours =
            Number(
                hours[i]
                    .value
            );


        if (
            !courseName
            &&
            !creditHours
        ) {

            continue;

        }


        if (
            !courseName
            ||
            creditHours <= 0
        ) {

            showGPAResult(
                resultBox,
                "Please complete all course fields."
            );


            return;

        }


        courses.push(
            {
                course_name:
                    courseName,

                grade:
                    grades[i].value,

                credit_hours:
                    creditHours
            }
        );

    }


    if (
        courses.length
        ===
        0
    ) {

        showGPAResult(
            resultBox,
            "Please add at least one course."
        );


        return;

    }


    const previousCgpaElement =
        document.getElementById(
            "previousCgpa"
        );


    const previousHoursElement =
        document.getElementById(
            "previousHours"
        );


    const previousCgpaValue =
        previousCgpaElement
            ? previousCgpaElement.value
            : "";


    const previousHoursValue =
        previousHoursElement
            ? previousHoursElement.value
            : "";


    const payload = {

        courses:
            courses,

        previous_cgpa:
            previousCgpaValue
                ? Number(
                    previousCgpaValue
                )
                : null,

        previous_credit_hours:
            previousHoursValue
                ? Number(
                    previousHoursValue
                )
                : 0

    };


    showGPAResult(
        resultBox,
        "Calculating your GPA..."
    );


    try {

        const response =
            await fetch(
                `${API_BASE}/api/gpa/calculate`,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        const data =
            await response.json();


        if (
            !response.ok
            ||
            data.error
        ) {

            showGPAResult(
                resultBox,
                data.error
                ||
                "Unable to calculate GPA."
            );


            return;

        }


        let html = `

            <div class="gpa-results-grid">

                <div class="gpa-result-item">

                    <span>
                        Semester GPA
                    </span>

                    <strong>
                        ${
                            data.sgpa
                        }
                    </strong>

                </div>
        `;


        if (
            data.cgpa
            !==
            null
            &&
            data.cgpa
            !==
            undefined
        ) {

            html += `

                <div class="gpa-result-item">

                    <span>
                        Cumulative GPA
                    </span>

                    <strong>
                        ${
                            data.cgpa
                        }
                    </strong>

                </div>
            `;

        }


        html += `

                <div class="gpa-result-item">

                    <span>
                        Current Credits
                    </span>

                    <strong>
                        ${
                            data.current_credit_hours
                        }
                    </strong>

                </div>

            </div>
        `;


        if (resultBox) {

            resultBox.innerHTML =
                html;

        }

    }

    catch (error) {

        showGPAResult(
            resultBox,
            "Could not connect to the GPA server."
        );


        console.error(
            "GPA error:",
            error
        );

    }

}


function showGPAResult(
    element,
    message
) {

    if (!element) {

        return;

    }


    element.innerHTML = `

        <span>
            RESULT
        </span>

        <strong>
            ${
                escapeHTML(
                    message
                )
            }
        </strong>
    `;

}


/* =========================
   LOGOUT
========================= */

function logoutStudent() {

    localStorage.removeItem(
        "studentLoggedIn"
    );


    localStorage.removeItem(
        "studentName"
    );


    localStorage.removeItem(
        "studentEmail"
    );


    window.location.href =
        "login.html";

}


/* =========================
   SAFE HTML
========================= */

function escapeHTML(
    text
) {

    const element =
        document.createElement(
            "div"
        );


    element.innerText =
        String(
            text
        );


    return element.innerHTML;

}