# ==========================================================
# EDUCATION PDF SELL PROJECT
# database.py - COMPLETE FIXED VERSION
# ==========================================================

import sqlite3
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

DATABASE = "education.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    # Foreign keys enable
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ==========================================================
# CREATE ALL TABLES
# ==========================================================

def create_tables():

    conn = get_db()

    cursor = conn.cursor()

    # ======================================================
    # USERS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            mobile TEXT,

            password TEXT NOT NULL,

            role TEXT DEFAULT 'user',

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================================
    # PDF PRODUCTS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdfs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            description TEXT,

            category TEXT,

            price REAL DEFAULT 0,

            thumbnail TEXT,

            pdf_file TEXT NOT NULL,

            is_active INTEGER DEFAULT 1,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================================
    # ORDERS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            pdf_id INTEGER NOT NULL,

            amount REAL NOT NULL,

            payment_method TEXT
                DEFAULT 'demo',

            payment_status TEXT
                DEFAULT 'pending',

            transaction_id TEXT,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(pdf_id)
                REFERENCES pdfs(id)
                ON DELETE CASCADE
        )
    """)

    # ======================================================
    # PURCHASES
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            pdf_id INTEGER NOT NULL,

            order_id INTEGER NOT NULL,

            purchased_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, pdf_id),

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(pdf_id)
                REFERENCES pdfs(id)
                ON DELETE CASCADE,

            FOREIGN KEY(order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE
        )
    """)

    # ======================================================
    # ADMISSIONS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admissions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_name TEXT NOT NULL,

            father_name TEXT NOT NULL,

            mother_name TEXT,

            dob TEXT,

            gender TEXT,

            mobile TEXT NOT NULL,

            course TEXT NOT NULL,

            batch TEXT NOT NULL,

            previous_class TEXT,

            session TEXT,

            address TEXT,

            city TEXT,

            district TEXT,

            pincode TEXT,

            photo TEXT,

            admission_fee REAL DEFAULT 0,

            payment_status TEXT
                DEFAULT 'Pending',

            admission_date
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================================
    # DEFAULT ADMIN
    # ======================================================

    admin_email = "hemanta.g0304@gmail.com"

    admin_password = "Admin123"

    admin = cursor.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, (
        admin_email,
    )).fetchone()

    if not admin:

        hashed_password = generate_password_hash(
            admin_password
        )

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                mobile,
                password,
                role
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Administrator",
            admin_email,
            "8280897689",
            hashed_password,
            "admin"
        ))

        print()
        print("======================================")
        print(" DEFAULT ADMIN CREATED")
        print("======================================")
        print("Email    :", admin_email)
        print("Password :", admin_password)
        print("======================================")
        print()

    conn.commit()

    conn.close()


# ==========================================================
# USER FUNCTIONS
# ==========================================================

def create_user(
    name,
    email,
    mobile,
    password
):

    conn = get_db()

    try:

        hashed_password = generate_password_hash(
            password
        )

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                mobile,
                password,
                role
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email,
            mobile,
            hashed_password,
            "user"
        ))

        user_id = cursor.lastrowid

        conn.commit()

        return user_id

    except sqlite3.IntegrityError:

        return None

    finally:

        conn.close()


# ==========================================================
# GET USER BY EMAIL
# ==========================================================

def get_user_by_email(email):

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    conn.close()

    return user


# ==========================================================
# CHECK PASSWORD
# ==========================================================

def check_user_password(
    user,
    password
):

    if not user:

        return False

    try:

        return check_password_hash(
            user["password"],
            password
        )

    except Exception:

        return False


# ==========================================================
# PDF FUNCTIONS
# ==========================================================

def get_all_pdfs():

    conn = get_db()

    pdfs = conn.execute("""
        SELECT *
        FROM pdfs
        WHERE is_active = 1
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return pdfs


# ==========================================================
# GET SINGLE PDF
# ==========================================================

def get_pdf(pdf_id):

    conn = get_db()

    pdf = conn.execute("""
        SELECT *
        FROM pdfs
        WHERE id = ?
    """, (
        pdf_id,
    )).fetchone()

    conn.close()

    return pdf


# ==========================================================
# GET ADMIN PDF LIST
# ==========================================================

def get_all_pdfs_admin():

    conn = get_db()

    pdfs = conn.execute("""
        SELECT *
        FROM pdfs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return pdfs


# ==========================================================
# ADD PDF
# ==========================================================

def add_pdf(
    title,
    description,
    category,
    price,
    thumbnail,
    pdf_file
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pdfs
        (
            title,
            description,
            category,
            price,
            thumbnail,
            pdf_file
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        category,
        price,
        thumbnail,
        pdf_file
    ))

    pdf_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return pdf_id


# ==========================================================
# UPDATE PDF
# ==========================================================

def update_pdf(
    pdf_id,
    title,
    description,
    category,
    price,
    thumbnail,
    pdf_file
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE pdfs
        SET
            title = ?,
            description = ?,
            category = ?,
            price = ?,
            thumbnail = ?,
            pdf_file = ?
        WHERE id = ?
    """, (
        title,
        description,
        category,
        price,
        thumbnail,
        pdf_file,
        pdf_id
    ))

    affected = cursor.rowcount

    conn.commit()

    conn.close()

    return affected > 0


# ==========================================================
# DELETE PDF
# ==========================================================

def delete_pdf(pdf_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM pdfs
        WHERE id = ?
    """, (
        pdf_id,
    ))

    deleted = cursor.rowcount

    conn.commit()

    conn.close()

    return deleted > 0


# ==========================================================
# PURCHASE CHECK
# ==========================================================

def is_pdf_purchased(
    user_id,
    pdf_id
):

    conn = get_db()

    purchase = conn.execute("""
        SELECT id
        FROM purchases
        WHERE user_id = ?
        AND pdf_id = ?
    """, (
        user_id,
        pdf_id
    )).fetchone()

    conn.close()

    return purchase is not None


# ==========================================================
# USER PURCHASES
# ==========================================================

def get_user_purchases(user_id):

    conn = get_db()

    purchases = conn.execute("""
        SELECT
            purchases.*,

            pdfs.title,
            pdfs.description,
            pdfs.category,
            pdfs.price,
            pdfs.thumbnail,
            pdfs.pdf_file

        FROM purchases

        JOIN pdfs
        ON purchases.pdf_id = pdfs.id

        WHERE purchases.user_id = ?

        ORDER BY purchases.id DESC
    """, (
        user_id,
    )).fetchall()

    conn.close()

    return purchases


# ==========================================================
# CREATE ORDER
# ==========================================================

def create_order(
    user_id,
    pdf_id,
    amount,
    payment_method="demo"
):

    conn = get_db()

    try:

        cursor = conn.cursor()

        # --------------------------------------------------
        # CREATE ORDER
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO orders
            (
                user_id,
                pdf_id,
                amount,
                payment_method,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            pdf_id,
            amount,
            payment_method,
            "paid"
        ))

        order_id = cursor.lastrowid

        # --------------------------------------------------
        # CREATE PURCHASE
        # --------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO purchases
            (
                user_id,
                pdf_id,
                order_id
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            pdf_id,
            order_id
        ))

        conn.commit()

        return order_id

    except Exception as e:

        conn.rollback()

        print(
            "Order error:",
            e
        )

        return None

    finally:

        conn.close()


# ==========================================================
# STATISTICS
# ==========================================================

def get_statistics():

    conn = get_db()

    users = conn.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'user'
    """).fetchone()["total"]

    pdfs = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pdfs
    """).fetchone()["total"]

    orders = conn.execute("""
        SELECT COUNT(*) AS total
        FROM orders
    """).fetchone()["total"]

    revenue = conn.execute("""
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total

        FROM orders

        WHERE payment_status = 'paid'
    """).fetchone()["total"]

    conn.close()

    return {
        "users": users,
        "pdfs": pdfs,
        "orders": orders,
        "revenue": revenue
    }


# ==========================================================
# ADMIN ORDERS
# ==========================================================

def get_all_orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT

            orders.*,

            users.name AS user_name,
            users.email AS user_email,

            pdfs.title AS pdf_title

        FROM orders

        JOIN users
        ON orders.user_id = users.id

        JOIN pdfs
        ON orders.pdf_id = pdfs.id

        ORDER BY orders.id DESC
    """).fetchall()

    conn.close()

    return orders


# ==========================================================
# ADMISSION FUNCTIONS
# ==========================================================

def add_admission(data):

    conn = get_db()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO admissions
            (
                student_name,
                father_name,
                mother_name,
                dob,
                gender,
                mobile,
                course,
                batch,
                previous_class,
                session,
                address,
                city,
                district,
                pincode,
                photo,
                admission_fee,
                payment_status
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (

            data.get("student_name", ""),

            data.get("father_name", ""),

            data.get("mother_name", ""),

            data.get("dob", ""),

            data.get("gender", ""),

            data.get("mobile", ""),

            data.get("course", ""),

            data.get("batch", ""),

            data.get("previous_class", ""),

            data.get("session", ""),

            data.get("address", ""),

            data.get("city", ""),

            data.get("district", ""),

            data.get("pincode", ""),

            data.get("photo", ""),

            data.get("admission_fee", 0),

            data.get(
                "payment_status",
                "Pending"
            )
        ))

        admission_id = cursor.lastrowid

        conn.commit()

        return admission_id

    except Exception as e:

        conn.rollback()

        print(
            "Admission error:",
            e
        )

        return None

    finally:

        conn.close()


# ==========================================================
# GET ALL ADMISSIONS
# ==========================================================

def get_all_admissions():

    conn = get_db()

    admissions = conn.execute("""
        SELECT *
        FROM admissions
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return admissions


# ==========================================================
# GET SINGLE ADMISSION
# ==========================================================

def get_admission(admission_id):

    conn = get_db()

    admission = conn.execute("""
        SELECT *
        FROM admissions
        WHERE id = ?
    """, (
        admission_id,
    )).fetchone()

    conn.close()

    return admission


# ==========================================================
# UPDATE ADMISSION PAYMENT
# ==========================================================

def update_admission_payment(
    admission_id,
    status
):

    if status not in [
        "Paid",
        "Pending"
    ]:

        return False

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE admissions
        SET payment_status = ?
        WHERE id = ?
    """, (
        status,
        admission_id
    ))

    updated = cursor.rowcount

    conn.commit()

    conn.close()

    return updated > 0


# ==========================================================
# DELETE ADMISSION
# ==========================================================

def delete_admission(
    admission_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM admissions
        WHERE id = ?
    """, (
        admission_id,
    ))

    deleted = cursor.rowcount

    conn.commit()

    conn.close()

    return deleted > 0


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

if __name__ == "__main__":

    create_tables()

    print()
    print("======================================")
    print(" EDUCATION PDF SELL DATABASE READY")
    print("======================================")
    print(
        "Database:",
        DATABASE
    )
    print("======================================")