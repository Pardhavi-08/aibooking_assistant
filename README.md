# 🏥 AI Clinic Booking Assistant

An AI-powered clinic booking assistant that uses **PDF-based knowledge**, **strict Retrieval-Augmented Generation (RAG)**, and **validated conversational workflows** to book appointments accurately and reliably.

This system ensures **zero hallucinations**, **structured validation**, and **persistent storage**, making it suitable for **real-world clinic operations**.

---

## 🚀 Key Features

### 📄 PDF-Based Knowledge Base
- Clinics upload their information as PDFs (services, timings, pricing).
- The system extracts and indexes content automatically.
- Knowledge persists across browser refreshes and app restarts.

---

### 🧠 Strict RAG (No Hallucinations)
- Answers are generated **only** from uploaded PDFs.
- If information is missing, the assistant explicitly responds:
  > *“I don’t have that information in the uploaded clinic documents.”*
- Prevents false services, timings, or clinic details.

---

### 📅 Smart Appointment Booking (Fully Validated)
The booking flow is **conversational and intelligent**:
- Detects booking intent automatically
- Asks for service first
- Validates service exists in PDFs
- Auto-selects clinic if service is available at only one clinic
- Prompts clinic selection when multiple clinics match

**Validations include:**
- Closed days (e.g., Sundays)
- Clinic working hours
- Date and time formats
- Email and phone number formats
- Final confirmation before saving

---

### 🗄️ Persistent SQLite Database

#### Customers Table
- Name
- Email
- Phone

#### Bookings Table
- Clinic
- Service
- Date & Time
- Timestamp

**Ensures:**
- No duplicate customers
- Bookings persist across app restarts

---

### ✉️ Email Confirmation
- Automatic confirmation email after successful booking
- Includes:
  - Clinic name
  - Service
  - Date & time
- Uses secure SMTP with environment variables

---

### 🧑‍💼 Admin Dashboard
- View all bookings
- View customer records
- Search and filter bookings
- Designed for admin use  
  *(Authentication can be added if required)*

---

## 🧱 System Architecture

```
PDF Upload
   ↓
PDF Parsing
   ↓
FAISS Vector Store (Persistent)
   ↓
Strict RAG Querying
   ↓
Validated Booking Flow
   ↓
SQLite Database
   ↓
Email Confirmation
```

---

## 🛠️ Tech Stack
- **Frontend:** Streamlit
- **LLM Orchestration:** LangChain
- **Vector Database:** FAISS (Persistent)
- **Database:** SQLite
- **Backend:** Python
- **Email:** SMTP (Gmail App Password)

---

## ▶️ How to Run the Application

### 1️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Set Environment Variables
```bash
setx EMAIL_SENDER "your_email@gmail.com"
setx EMAIL_PASSWORD "your_app_password"
```

### 4️⃣ Run the App
```bash
streamlit run app.py
```

---

## 📌 Notes & Design Decisions
- PDFs persist across refresh and are reusable
- FAISS index is saved to disk and reused (no rebuild on restart)
- Booking is blocked if PDFs are not uploaded
- Strict validation avoids incorrect bookings
- Admin authentication intentionally kept simple due to time constraints

---

## 🧪 Tested Scenarios
- Booking without PDFs → ❌ Blocked
- Asking services not in PDFs → ✅ Graceful rejection
- Booking on Sunday → ❌ Rejected
- Booking outside clinic hours → ❌ Rejected
- Duplicate customer → ❌ Prevented
- Email delivery → ✅ Verified

---

## 🔮 Future Enhancements
- Admin authentication (role-based access)
- Doctor-level scheduling
- SMS notifications
- Cloud deployment (AWS / GCP)
- Analytics dashboard

---

## 👤 Author
**Pardhavi Mallampati**  
*AI Engineer – Use Case Project*
