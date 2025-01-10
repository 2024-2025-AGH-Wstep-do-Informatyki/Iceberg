#KLIENT SERWERA DO WYSYLANIA LOGOW I INNYCH DANYCHś
import smtplib
from email.message import EmailMessage

def send_email():
    # Tworzenie wiadomości
    msg = EmailMessage()
    msg["From"] = "nadawca@example.com"
    msg["To"] = "odbiorca@example.com"
    msg["Subject"] = "Testowa Wiadomość"
    msg.set_content("To jest przykładowa treść wiadomości SMTP.")

    # Połączenie z serwerem SMTP uruchomionym lokalnie
    try:
        with smtplib.SMTP("localhost", 1025) as smtp:
            smtp.send_message(msg)
            print("Wiadomość wysłana")
    except ConnectionRefusedError:
        print("Nie można połączyć się z serwerem SMTP. Upewnij się, że serwer działa na localhost:1025.")

if __name__ == "__main__":
    send_email()
