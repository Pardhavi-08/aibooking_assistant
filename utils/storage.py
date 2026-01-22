import json
import os

BOOKINGS_FILE = "data/bookings.json"


def load_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return []

    with open(BOOKINGS_FILE, "r") as f:
        return json.load(f)


def save_booking(booking: dict):
    bookings = load_bookings()
    bookings.append(booking)

    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=2)


def save_bookings(bookings: list):
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=2)
