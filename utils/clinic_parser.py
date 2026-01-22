import re
from langchain_community.document_loaders import PyPDFLoader


def extract_clinic_data_from_pdfs(pdf_paths: list):
    clinics = []

    for path in pdf_paths:
        loader = PyPDFLoader(path)
        pages = loader.load()

        full_text = "\n".join(p.page_content for p in pages)

        clinic = {
            "name": None,
            "open_time": None,
            "close_time": None,
            "closed_days": [],
            "services": []
        }

        # ---------------------------
        # Clinic Name
        # ---------------------------
        name_match = re.search(
            r"(Clinic Name|Clinic)\s*[:\-]\s*(.+)",
            full_text,
            re.IGNORECASE
        )
        if name_match:
            clinic["name"] = name_match.group(2).strip()

        # ---------------------------
        # Working Hours (ROBUST)
        # ---------------------------
        hours_match = re.search(
            r"Monday\s*to\s*Saturday\s*[:\-]?\s*"
            r"(\d{1,2}[:\.]\d{2}\s*(AM|PM))\s*[–\-]\s*"
            r"(\d{1,2}[:\.]\d{2}\s*(AM|PM))",
            full_text,
            re.IGNORECASE
        )

        if hours_match:
            clinic["open_time"] = hours_match.group(1)
            clinic["close_time"] = hours_match.group(3)

        # ---------------------------
        # Closed Days
        # ---------------------------
        if re.search(r"Closed\s+on\s+Sunday", full_text, re.IGNORECASE):
            clinic["closed_days"].append("Sunday")

        # ---------------------------
        # Services & Pricing
        # ---------------------------
        service_matches = re.findall(
            r"[-•\d]+\s*(.+?)\s*[–\-]\s*₹\s*(\d+)",
            full_text
        )

        for name, price in service_matches:
            clinic["services"].append({
                "name": name.strip(),
                "price": int(price)
            })

        clinics.append(clinic)

    return clinics
