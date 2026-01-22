from utils.emailer import send_confirmation_email

send_confirmation_email({
    "name": "Test User",
    "email": "YOUR_EMAIL@gmail.com",
    "service": "Test Consultation",
    "date": "Tomorrow",
    "time": "10 AM"
})
