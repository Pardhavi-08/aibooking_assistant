import streamlit as st

import sys
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os
import json
import re
from utils.database import init_db
import streamlit as st
from utils.bookings_db import get_all_bookings_df

# Fix imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.llm import get_chatgroq_model
from utils.rag_pipeline import retrieve_context, build_vector_store

from utils.storage import load_bookings
from utils.chat_storage import load_chat, save_chat, clear_chat
from utils.storage import save_booking
from utils.storage import load_bookings, save_booking, save_bookings
from utils.clinic_parser import extract_clinic_data_from_pdfs
from utils.bookings_db import save_booking_db
from utils.validators import (
    is_not_empty,
    is_valid_email,
    is_valid_date,
    is_valid_time
)
from utils.emailer import send_confirmation_email
from utils.clinic_parser import extract_clinic_data_from_pdfs
from utils.rag_pipeline import build_vector_store



PDF_DIR = "data/uploaded_pdfs"
CLINICS_CACHE = "data/clinics.json"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)


# --------------------------------
# Booking Intent Detection
# --------------------------------


def is_service_list_query(text: str) -> bool:
    keywords = [
        "services",
        "available services",
        "what are the services",
        "list services",
        "services available"
    ]
    text = text.lower()
    return any(k in text for k in keywords)


def get_clinic_from_query(query: str):
    query_words = set(query.lower().split())

    for clinic in st.session_state.get("clinics", []):
        clinic_words = set(clinic["name"].lower().split())

        # If most clinic name words appear in query → match
        if len(query_words & clinic_words) >= max(1, len(clinic_words) - 1):
            return clinic

    return None



def format_services_response(clinics):
    lines = ["Here are the services available:\n"]

    for clinic in clinics:
        lines.append(f"📍 **{clinic['name']}**")
        for service in clinic.get("services", []):
            lines.append(f"- {service['name']} – ₹{service['price']}")
        lines.append("")

    return "\n".join(lines)


def looks_like_service_query(text: str) -> bool:
    keywords = [
        "service",
        "treatment",
        "consultation",
        "checkup",
        "therapy",
        "care",
        "appointment for",
    ]

    text = text.lower()
    return any(k in text for k in keywords)

def is_working_hours_query(query: str) -> bool:
    keywords = [
        "working hours",
        "opening hours",
        "timings",
        "open time",
        "close time"
    ]
    query = query.lower()
    return any(k in query for k in keywords)

def format_working_hours_response(clinics: list) -> str:
    lines = ["Here are the working hours:\n"]

    for clinic in clinics:
        open_time = clinic.get("open_time", "Not specified")
        close_time = clinic.get("close_time", "Not specified")
        closed_days = ", ".join(clinic.get("closed_days", []))

        lines.append(
            f"📍 **{clinic['name']}**\n"
            f"• Monday to Saturday: {open_time} – {close_time}\n"
            f"• Closed on {closed_days}\n"
        )

    return "\n".join(lines)



def detect_booking_intent(user_input: str) -> bool:
    keywords = [
        "book", "booking", "appointment", "schedule",
        "reserve", "slot", "consultation", "visit"
    ]
    user_input = user_input.lower()
    return any(k in user_input for k in keywords)


# --------------------------------
# Booking State
# --------------------------------
def init_booking_state():
    return {
    "started": False,
    "awaiting_field": None,
    "service": None,
    "clinic": None,
    "date": None,
    "time": None,
    "name": None,
    "email": None,
    "phone": None,
    "confirmed": False
}



# --------------------------------
# Booking Flow
# --------------------------------
from utils.validators import (
    is_not_empty,
    is_valid_email,
    is_valid_date,
    is_valid_time
)
from utils.storage import save_booking
from utils.emailer import send_confirmation_email


def get_clinics_for_service(service_name: str):
    service_name = service_name.lower()
    clinics = []

    for clinic in st.session_state.get("clinics", []):
        for service in clinic.get("services", []):
            if service_name in service["name"].lower():
                clinics.append(clinic)
                break

    return clinics

def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r"^[6-9]\d{9}$", phone))

from datetime import datetime, timedelta

def is_sunday(date_input: str) -> bool:
    date_input = date_input.lower().strip()

    # Handle natural language
    if date_input == "today":
        date_obj = datetime.today()
    elif date_input == "tomorrow":
        date_obj = datetime.today() + timedelta(days=1)
    else:
        # Try common date formats
        for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                date_obj = datetime.strptime(date_input, fmt)
                break
            except ValueError:
                continue
        else:
            # Invalid date format → let validation handle it elsewhere
            return False

    # Sunday = 6
    return date_obj.weekday() == 6

def get_clinics_for_service(service_name: str):
    service_name = service_name.lower().strip()
    matched_clinics = []

    for clinic in st.session_state.get("clinics", []):
        for service in clinic.get("services", []):
            if service_name in service["name"].lower():
                matched_clinics.append(clinic)
                break

    return matched_clinics

def is_service_available(service_name: str) -> bool:
    return len(get_clinics_for_service(service_name)) > 0

from datetime import datetime
from typing import Optional


def normalize_time(t: str) -> Optional[datetime.time]:
    """
    Converts '8.30 AM', '8:30 AM', '11 AM', '5 PM' → datetime.time
    """
    if not t:
        return None

    t = t.upper().replace(".", ":").strip()

    formats = [
        "%I:%M %p",
        "%I %p"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(t, fmt).time()
        except ValueError:
            continue

    return None


def is_time_within_clinic_hours(time_input: str, clinic: dict) -> bool:
    user_time = normalize_time(time_input)
    open_time = normalize_time(clinic.get("open_time", ""))
    close_time = normalize_time(clinic.get("close_time", ""))

    if not user_time or not open_time or not close_time:
        return False

    return open_time <= user_time <= close_time

def find_clinic_by_name(name: str):
    for clinic in st.session_state.get("clinics", []):
        if clinic["name"].lower() == name.lower():
            return clinic
    return None

def is_clinic_open_on_date(date_input: str, clinic: dict) -> bool:
    if is_sunday(date_input) and "Sunday" in clinic.get("closed_days", []):
        return False
    return True
def handle_booking_flow(user_input: str):
    booking = st.session_state.booking
    user_input = user_input.strip()

    # ==================================================
    # SERVICE
    # ==================================================
    if booking["awaiting_field"] == "service":
        matches = []

        for clinic in st.session_state.clinics:
            for s in clinic.get("services", []):
                if user_input.lower() in s["name"].lower():
                    matches.append(clinic)
                    break

        if not matches:
            return "❌ This service is currently unavailable."

        booking["service"] = user_input

        # Only ONE clinic → auto-select
        if len(matches) == 1:
            booking["clinic"] = matches[0]  # store clinic dict
            booking["awaiting_field"] = "date"
            return (
                f"✅ **{user_input}** is available at **{matches[0]['name']}**.\n\n"
                "What **date** would you prefer?"
            )

        # Multiple clinics → ask user
        booking["possible_clinics"] = matches
        booking["awaiting_field"] = "clinic"

        clinic_names = "\n".join(f"- {c['name']}" for c in matches)
        return (
            "This service is available at multiple clinics:\n\n"
            f"{clinic_names}\n\n"
            "Please choose a **clinic name**."
        )

    # ==================================================
    # CLINIC (only when multiple)
    # ==================================================
    if booking["awaiting_field"] == "clinic":
        for clinic in booking.get("possible_clinics", []):
            if clinic["name"].lower() == user_input.lower():
                booking["clinic"] = clinic
                booking.pop("possible_clinics", None)
                booking["awaiting_field"] = "date"
                return "Great 👍 What **date** would you prefer?"

        return "❌ Please choose a valid clinic from the list."

    # ==================================================
    # DATE
    # ==================================================
    if booking["awaiting_field"] == "date":
        if not is_valid_date(user_input):
            return "❌ Please enter a valid date (DD-MM-YYYY / today / tomorrow)."

        if is_sunday(user_input):
            return "❌ Clinics are closed on Sundays. Please choose another date."

        booking["date"] = user_input
        booking["awaiting_field"] = "time"
        return "What **time** works best for you?"

    # ==================================================
    # TIME
    # ==================================================
    if booking["awaiting_field"] == "time":
        if not is_valid_time(user_input):
            return "❌ Please enter a valid time (e.g., 10 AM, 11:30 AM, 14:00)."

        clinic = booking["clinic"]  # clinic dict

        if not is_time_within_clinic_hours(user_input, clinic):
            return (
                f"❌ Selected time is outside working hours "
                f"({clinic.get('open_time')} – {clinic.get('close_time')})."
            )

        booking["time"] = user_input
        booking["awaiting_field"] = "name"
        return "May I know your **full name**?"

    # ==================================================
    # NAME
    # ==================================================
    if booking["awaiting_field"] == "name":
        if not is_not_empty(user_input) or user_input.isdigit():
            return "❌ Please enter a valid full name."

        booking["name"] = user_input
        booking["awaiting_field"] = "email"
        return "Please share your **email address**."

    # ==================================================
    # EMAIL
    # ==================================================
    if booking["awaiting_field"] == "email":
        if not is_valid_email(user_input):
            return "❌ Please enter a valid email address."

        booking["email"] = user_input
        booking["awaiting_field"] = "phone"
        return "Please share your **phone number**."

    # ==================================================
    # PHONE
    # ==================================================
    if booking["awaiting_field"] == "phone":
        if not is_valid_phone(user_input):
            return "❌ Please enter a valid 10-digit phone number."

        booking["phone"] = user_input
        booking["awaiting_field"] = "confirm"

        return f"""
✅ **Please confirm your booking details:**

- **Service:** {booking['service']}
- **Clinic:** {booking['clinic']['name']}
- **Date:** {booking['date']}
- **Time:** {booking['time']}
- **Name:** {booking['name']}
- **Email:** {booking['email']}
- **Phone:** {booking['phone']}

Reply **YES** to confirm or **NO** to cancel.
"""

    # ==================================================
    # CONFIRM
    # ==================================================
    if booking["awaiting_field"] == "confirm":
        if user_input.lower() == "yes":

            booking_data = {
                "service": booking["service"],
                "clinic": booking["clinic"]["name"],  # convert dict → string
                "date": booking["date"],
                "time": booking["time"],
                "name": booking["name"],
                "email": booking["email"],
                "phone": booking["phone"]
            }

            save_booking_db(booking_data)


            try:
                send_confirmation_email(booking_data)
            except Exception as e:
                print("❌ Email failed:", e)
                st.session_state.booking = init_booking_state()
                return "⚠️ Appointment booked, but email could not be sent."

            st.session_state.booking = init_booking_state()
            return "🎉 **Your appointment is confirmed!** A confirmation email has been sent."

        st.session_state.booking = init_booking_state()
        return "❌ Booking cancelled."

    # ==================================================
    # FALLBACK (safety)
    # ==================================================
    return "⚠️ Something went wrong. Let’s start again."



# --------------------------------
# LLM Response
# --------------------------------
def get_chat_response(chat_model, messages, system_prompt):
    formatted = [SystemMessage(content=system_prompt)]
    for m in messages:
        if m["role"] == "user":
            formatted.append(HumanMessage(content=m["content"]))
        else:
            formatted.append(AIMessage(content=m["content"]))
    response = chat_model.invoke(formatted)
    return response.content


# --------------------------------
# Pages
# --------------------------------
def instructions_page():
    st.title("📘 Instructions")
    st.markdown("""
    ### How to use
    - Ask clinic-related questions
    - Book appointments conversationally
    - View all bookings in the Bookings tab
    """)
import streamlit as st
from utils.bookings_db import get_all_bookings_df


def bookings_page():
    st.title("📋 Admin Dashboard — Bookings")

    df = get_all_bookings_df()

    if df.empty:
        st.info("No bookings yet.")
        return

    # ---------------------------
    # Filters
    # ---------------------------
    col1, col2 = st.columns(2)

    with col1:
        clinic_filter = st.selectbox(
            "Filter by Clinic",
            ["All"] + sorted(df["clinic"].unique().tolist())
        )

    with col2:
        date_filter = st.selectbox(
            "Filter by Date",
            ["All"] + sorted(df["date"].unique().tolist())
        )

    if clinic_filter != "All":
        df = df[df["clinic"] == clinic_filter]

    if date_filter != "All":
        df = df[df["date"] == date_filter]

    st.caption(f"Total bookings: {len(df)}")

    # ---------------------------
    # Table
    # ---------------------------
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # ---------------------------
    # Export
    # ---------------------------
    st.download_button(
        "📤 Download CSV",
        data=df.to_csv(index=False),
        file_name="bookings.csv",
        mime="text/csv"
    )

                    
def is_service_available(service_name: str) -> bool:
    if not service_name:
        return False

    clinics = st.session_state.get("clinics", [])
    if not clinics:
        return False

    service_name = service_name.lower()

    for clinic in clinics:
        for service in clinic.get("services", []):
            if service_name == service["name"].lower():
                return True

    return False

def chat_page():
    st.title("🤖 AI Booking Assistant")

    chat_model = get_chatgroq_model()

    # -------------------------
    # State Initialization
    # -------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat()

    if "booking" not in st.session_state:
        st.session_state.booking = init_booking_state()

    if "bookings" not in st.session_state:
        st.session_state.bookings = load_bookings()

    # -------------------------
    # Display Chat History
    # -------------------------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -------------------------
    # User Input
    # -------------------------
    if prompt := st.chat_input("Type your message here..."):
        prompt_clean = prompt.strip().lower()

        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        save_chat(st.session_state.messages)

        with st.chat_message("user"):
            st.markdown(prompt)

        # ==================================================
        # 1️⃣ GREETING
        # ==================================================
        if prompt_clean in ["hi", "hello", "hey", "good morning", "good evening"]:
            response = "Hello 👋 How can I assist you today?"

        # ==================================================
        # 2️⃣ BOOKING INTENT (PDF REQUIRED)
        # ==================================================
        elif detect_booking_intent(prompt):
            if "clinics" not in st.session_state or not st.session_state.clinics:
                response = (
                    "📄 Please upload clinic PDF(s) first so I can verify "
                    "available clinics, services, and timings."
                )
            else:
                st.session_state.booking["started"] = True
                st.session_state.booking["awaiting_field"] = "service"
                response = (
                    "Sure 🙂 I can help you book an appointment.\n\n"
                    "What **service** do you need?"
                )

        # ==================================================
        # 3️⃣ BOOKING FLOW CONTINUATION
        # ==================================================
        elif st.session_state.booking["started"]:
            response = handle_booking_flow(prompt)

        # ==================================================
        # 4️⃣ WORKING HOURS (ONE OR ALL CLINICS)
        # ==================================================
        elif is_working_hours_query(prompt_clean):
            if "clinics" not in st.session_state or not st.session_state.clinics:
                response = (
                    "📄 Please upload clinic PDF(s) first so I can "
                    "check working hours."
                )
            else:
                clinic = get_clinic_from_query(prompt_clean)
                if clinic:
                    response = format_working_hours_response([clinic])
                else:
                    response = format_working_hours_response(
                        st.session_state.clinics
                    )

        # ==================================================
        # 5️⃣ SERVICE LISTING (ONE OR ALL CLINICS)
        # ==================================================
        elif is_service_list_query(prompt_clean):
            if "clinics" not in st.session_state or not st.session_state.clinics:
                response = (
                    "📄 Please upload clinic PDF(s) first so I can show "
                    "available services."
                )
            else:
                clinic = get_clinic_from_query(prompt_clean)
                if clinic:
                    response = format_services_response([clinic])
                else:
                    response = format_services_response(
                        st.session_state.clinics
                    )

        # ==================================================
        # 6️⃣ INVALID SERVICE CHECK (ONLY WHEN SERVICE MENTIONED)
        # ==================================================
        elif looks_like_service_query(prompt_clean) and not is_service_available(prompt):
            response = "❌ Sorry, this service is not available at the clinic."

        # ==================================================
        # 7️⃣ STRICT RAG (PDF ONLY)
        # ==================================================
        else:
            if "vector_store" not in st.session_state:
                response = (
                    "📄 Please upload clinic PDF(s) from the sidebar "
                    "so I can answer your questions accurately."
                )
            else:
                context = retrieve_context(prompt)

                system_prompt = f"""
You are a STRICT clinic information assistant.

RULES:
- Answer ONLY using the CONTEXT.
- DO NOT add services, timings, prices, doctors, or assumptions.
- If the answer is NOT present, reply EXACTLY:
  "I’m sorry, I don’t have that information in the uploaded clinic documents."

CONTEXT:
{context}
"""
                response = get_chat_response(
                    chat_model,
                    [{"role": "user", "content": prompt}],
                    system_prompt
                )

        # -------------------------
        # Save + Display Assistant
        # -------------------------
        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )
        save_chat(st.session_state.messages)

        with st.chat_message("assistant"):
            st.markdown(response)

    # -------------------------
    # DEBUG
    # -------------------------



# --------------------------------
# Main
# --------------------------------

PDF_DIR = "data/uploaded_pdfs"
FAISS_DIR = "data/faiss_index"
CLINICS_CACHE = "data/clinics.json"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)


# -------------------------
# Helper: rebuild KB
# -------------------------
def rebuild_knowledge_base(pdf_paths):
    # Remove FAISS index
    if os.path.exists(FAISS_DIR):
        import shutil
        shutil.rmtree(FAISS_DIR)

    # Rebuild only if PDFs exist
    if pdf_paths:
        st.session_state.vector_store = build_vector_store(pdf_paths)

        clinics = extract_clinic_data_from_pdfs(pdf_paths)
        with open(CLINICS_CACHE, "w") as f:
            json.dump(clinics, f, indent=2)

        st.session_state.clinics = clinics
    else:
        st.session_state.pop("vector_store", None)
        st.session_state.pop("clinics", None)

        if os.path.exists(CLINICS_CACHE):
            os.remove(CLINICS_CACHE)

# -------------------------
# Main
# -------------------------
def main():
    # ----------------------------
    # Initialize DB (SAFE)
    # ----------------------------
    init_db()

    st.set_page_config(
        page_title="AI Booking Assistant",
        page_icon="🤖",
        layout="wide"
    )

    # ================================
    # SIDEBAR
    # ================================
    with st.sidebar:
        st.title("📄 Knowledge Base")

        # Ensure directories exist
        os.makedirs(PDF_DIR, exist_ok=True)
        os.makedirs(FAISS_DIR, exist_ok=True)

        # ----------------------------
        # Upload PDFs
        # ----------------------------
        uploaded_files = st.file_uploader(
            "Upload clinic PDFs",
            type=["pdf"],
            accept_multiple_files=True
        )

        if uploaded_files:
            for file in uploaded_files:
                save_path = os.path.join(PDF_DIR, file.name)
                if not os.path.exists(save_path):
                    with open(save_path, "wb") as f:
                        f.write(file.read())

            st.success(f"{len(uploaded_files)} PDF(s) uploaded")

            # 🔥 ALWAYS rebuild KB after upload
            pdf_paths = [
                os.path.join(PDF_DIR, f)
                for f in os.listdir(PDF_DIR)
                if f.lower().endswith(".pdf")
            ]

            if pdf_paths:
                rebuild_knowledge_base(pdf_paths)

        # ----------------------------
        # Existing PDFs (UI + Delete)
        # ----------------------------
        existing_pdfs = [
            os.path.join(PDF_DIR, f)
            for f in os.listdir(PDF_DIR)
            if f.lower().endswith(".pdf")
        ]

        if existing_pdfs:
            st.markdown("### 📚 PDFs loaded")

            for pdf_path in existing_pdfs:
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(
                        f"<div style='padding-top:6px'>• {os.path.basename(pdf_path)}</div>",
                        unsafe_allow_html=True
                    )

                with col2:
                    if st.button("✖", key=f"del_{pdf_path}", help="Remove PDF"):
                        os.remove(pdf_path)

                        remaining = [
                            os.path.join(PDF_DIR, f)
                            for f in os.listdir(PDF_DIR)
                            if f.lower().endswith(".pdf")
                        ]

                        rebuild_knowledge_base(remaining)
                        st.rerun()
        else:
            st.info("No PDFs uploaded yet.")

        # ----------------------------
        # Load FAISS + Clinics on refresh (SAFE)
        # ----------------------------
        if "vector_store" not in st.session_state:
            if os.path.exists(os.path.join(FAISS_DIR, "index.faiss")):
                st.session_state.vector_store = build_vector_store([])
            else:
                st.session_state.vector_store = None

        if "clinics" not in st.session_state:
            if os.path.exists(CLINICS_CACHE):
                with open(CLINICS_CACHE, "r") as f:
                    st.session_state.clinics = json.load(f)
            else:
                st.session_state.clinics = []

        st.divider()

        # ----------------------------
        # Navigation
        # ----------------------------
        st.title("Navigation")
        page = st.radio(
            "Go to:",
            ["Chat", "Bookings", "Instructions"]
        )

        if page == "Chat":
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                save_chat([])
                st.rerun()

    # ================================
    # PAGE ROUTING
    # ================================
    if page == "Chat":
        chat_page()
    elif page == "Bookings":
        bookings_page()
    else:
        instructions_page()



if __name__ == "__main__":
    main()

