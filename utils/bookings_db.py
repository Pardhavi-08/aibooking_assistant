# utils/bookings_db.py
from utils.database import get_connection

import sqlite3
import pandas as pd

DB_PATH = "data/clinic.db"


def get_all_bookings_df():
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        b.id AS booking_id,
        c.name AS customer_name,
        c.email,
        c.phone,
        b.clinic,
        b.service,
        b.date,
        b.time,
        b.created_at
    FROM bookings b
    JOIN customers c ON b.customer_id = c.id
    ORDER BY b.created_at DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_or_create_customer(name, email, phone):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM customers WHERE email = ?", (email,))
    row = cur.fetchone()

    if row:
        customer_id = row[0]
    else:
        cur.execute(
            "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
            (name, email, phone)
        )
        customer_id = cur.lastrowid

    conn.commit()
    conn.close()
    return customer_id


def save_booking_db(booking):
    customer_id = get_or_create_customer(
        booking["name"],
        booking["email"],
        booking["phone"]
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bookings (customer_id, clinic, service, date, time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        booking["clinic"],
        booking["service"],
        booking["date"],
        booking["time"]
    ))

    conn.commit()
    conn.close()
