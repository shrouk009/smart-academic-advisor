import sqlite3
import uuid

from pathlib import Path
from datetime import (
    datetime,
    timezone
)


# =========================================================
# DATABASE
# =========================================================

# قاعدة البيانات خارج مجلد المشروع
# حتى Live Server لا يعمل Reload كلما تم حفظ رسالة.

DATABASE_FILE = (
    Path.home()
    / ".smart_academic_advisor"
    / "smart_advisor.db"
)


def utc_now():

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def get_connection():

    DATABASE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    connection = sqlite3.connect(
        DATABASE_FILE,
        check_same_thread=False
    )


    connection.row_factory = (
        sqlite3.Row
    )


    connection.execute(
        "PRAGMA foreign_keys = ON"
    )


    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_database():

    connection = (
        get_connection()
    )


    cursor = (
        connection.cursor()
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (

            session_id TEXT PRIMARY KEY,

            user_id TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            session_id TEXT NOT NULL,

            role TEXT NOT NULL
                CHECK(
                    role IN (
                        'user',
                        'assistant'
                    )
                ),

            content TEXT NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY(session_id)
                REFERENCES chat_sessions(session_id)
                ON DELETE CASCADE

        )
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chat_sessions_user

        ON chat_sessions(
            user_id,
            updated_at
        )
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_session

        ON chat_messages(
            session_id,
            id
        )
        """
    )


    connection.commit()

    connection.close()


initialize_database()


print(
    "Chat database:",
    DATABASE_FILE
)


# =========================================================
# NORMALIZE USER ID
# =========================================================

def normalize_user_id(
    user_id
):

    return (
        user_id
        or
        "anonymous"
    ).strip() or "anonymous"


# =========================================================
# CREATE SESSION
# =========================================================

def create_session(
    user_id
):

    user_id = (
        normalize_user_id(
            user_id
        )
    )


    session_id = str(
        uuid.uuid4()
    )


    now = (
        utc_now()
    )


    connection = (
        get_connection()
    )


    connection.execute(
        """
        INSERT INTO chat_sessions (

            session_id,

            user_id,

            created_at,

            updated_at

        )

        VALUES (?, ?, ?, ?)
        """,

        (
            session_id,
            user_id,
            now,
            now
        )
    )


    connection.commit()

    connection.close()


    return session_id


# =========================================================
# SESSION BELONGS TO USER
# =========================================================

def session_belongs_to_user(
    session_id,
    user_id
):

    if not session_id:

        return False


    user_id = (
        normalize_user_id(
            user_id
        )
    )


    connection = (
        get_connection()
    )


    row = (
        connection.execute(
            """
            SELECT session_id

            FROM chat_sessions

            WHERE
                session_id = ?
                AND user_id = ?
            """,

            (
                session_id,
                user_id
            )
        )
        .fetchone()
    )


    connection.close()


    return (
        row is not None
    )


# =========================================================
# ENSURE SESSION
# =========================================================

def ensure_session(
    session_id=None,
    user_id=None
):

    user_id = (
        normalize_user_id(
            user_id
        )
    )


    if (
        session_id
        and
        session_belongs_to_user(
            session_id,
            user_id
        )
    ):

        return session_id


    return create_session(
        user_id
    )


# =========================================================
# SAVE MESSAGE
# =========================================================

def save_message(
    session_id,
    user_id,
    role,
    content
):

    session_id = (
        ensure_session(
            session_id,
            user_id
        )
    )


    now = (
        utc_now()
    )


    connection = (
        get_connection()
    )


    connection.execute(
        """
        INSERT INTO chat_messages (

            session_id,

            role,

            content,

            created_at

        )

        VALUES (?, ?, ?, ?)
        """,

        (
            session_id,
            role,
            str(content),
            now
        )
    )


    connection.execute(
        """
        UPDATE chat_sessions

        SET updated_at = ?

        WHERE session_id = ?
        """,

        (
            now,
            session_id
        )
    )


    connection.commit()

    connection.close()


    return session_id


# =========================================================
# GET RECENT HISTORY
# =========================================================

def get_history(
    session_id,
    user_id,
    limit=8
):

    if not session_belongs_to_user(
        session_id,
        user_id
    ):

        return []


    connection = (
        get_connection()
    )


    rows = (
        connection.execute(
            """
            SELECT
                role,
                content,
                created_at

            FROM (

                SELECT
                    id,
                    role,
                    content,
                    created_at

                FROM chat_messages

                WHERE session_id = ?

                ORDER BY id DESC

                LIMIT ?

            )

            ORDER BY id ASC
            """,

            (
                session_id,

                max(
                    1,
                    int(limit)
                )
            )
        )
        .fetchall()
    )


    connection.close()


    return [

        {
            "role":
                row["role"],

            "content":
                row["content"],

            "created_at":
                row["created_at"]
        }

        for row
        in rows

    ]


# =========================================================
# GET FULL HISTORY
# =========================================================

def get_full_history(
    session_id,
    user_id
):

    if not session_belongs_to_user(
        session_id,
        user_id
    ):

        return []


    connection = (
        get_connection()
    )


    rows = (
        connection.execute(
            """
            SELECT

                id,

                role,

                content,

                created_at

            FROM chat_messages

            WHERE session_id = ?

            ORDER BY id ASC
            """,

            (
                session_id,
            )
        )
        .fetchall()
    )


    connection.close()


    return [

        {
            "id":
                row["id"],

            "role":
                row["role"],

            "content":
                row["content"],

            "created_at":
                row["created_at"]
        }

        for row
        in rows

    ]


# =========================================================
# LIST SAVED SESSIONS
# =========================================================

def list_sessions(
    user_id,
    limit=20
):

    user_id = (
        normalize_user_id(
            user_id
        )
    )


    connection = (
        get_connection()
    )


    rows = (
        connection.execute(
            """
            SELECT

                s.session_id,

                s.created_at,

                s.updated_at,

                (

                    SELECT content

                    FROM chat_messages m

                    WHERE

                        m.session_id =
                            s.session_id

                        AND

                        m.role =
                            'user'

                    ORDER BY
                        m.id ASC

                    LIMIT 1

                ) AS first_message

            FROM chat_sessions s

            WHERE
                s.user_id = ?

            ORDER BY
                s.updated_at DESC

            LIMIT ?
            """,

            (
                user_id,

                max(
                    1,
                    int(limit)
                )
            )
        )
        .fetchall()
    )


    connection.close()


    return [

        dict(row)

        for row
        in rows

    ]


# =========================================================
# CLEAR SESSION HISTORY
# =========================================================

def clear_session_history(
    session_id,
    user_id
):

    if not session_belongs_to_user(
        session_id,
        user_id
    ):

        return False


    connection = (
        get_connection()
    )


    connection.execute(
        """
        DELETE FROM chat_messages

        WHERE session_id = ?
        """,

        (
            session_id,
        )
    )


    connection.execute(
        """
        UPDATE chat_sessions

        SET updated_at = ?

        WHERE session_id = ?
        """,

        (
            utc_now(),
            session_id
        )
    )


    connection.commit()

    connection.close()


    return True