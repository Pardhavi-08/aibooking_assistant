import re

def is_not_empty(value: str) -> bool:
    return bool(value and value.strip())


def is_valid_email(email: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


def is_valid_date(date_str: str) -> bool:
    """
    Accepts formats like:
    - 2025-01-21
    - 21-01-2025
    - tomorrow / today
    """
    date_str = date_str.lower().strip()

    if date_str in ["today", "tomorrow"]:
        return True

    return bool(re.match(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}", date_str))


def is_valid_time(time_str: str) -> bool:
    """
    Accepts formats like:
    - 10 AM
    - 11:30 AM
    - 14:00
    """
    time_str = time_str.lower().strip()

    return bool(
        re.match(r"\d{1,2}(:\d{2})?\s?(am|pm)", time_str)
        or re.match(r"\d{1,2}:\d{2}", time_str)
    )
def is_service_available(service_name: str) -> bool:
    service_name = service_name.lower()

    clinics = st.session_state.get("clinics", [])

    for clinic in clinics:
        for service in clinic.get("services", []):
            if service_name in service["name"].lower():
                return True

    return False
