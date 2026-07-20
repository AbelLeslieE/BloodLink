import smtplib

HOST = "smtp.gmail.com"
PORT = 587

try:
    print("Connecting...")
    server = smtplib.SMTP(HOST, PORT, timeout=15)
    server.ehlo()
    server.starttls()
    server.ehlo()
    print("✅ SMTP connection successful")
    server.quit()

except Exception as e:
    print("❌ ERROR:")
    print(type(e).__name__)
    print(e)