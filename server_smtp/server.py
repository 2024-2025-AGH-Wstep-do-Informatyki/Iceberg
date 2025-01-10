#Prosty modul serwera SMTP, który zapisuje otrzymane emaile do plików tekstowych.

import os
from datetime import datetime
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage

class CustomMessageHandler(AsyncMessage):
    def __init__(self, storage_path):
        super().__init__()
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    async def handle_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"email_{timestamp}.txt"
        file_path = os.path.join(self.storage_path, filename)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"From: {message['from']}\n")
            file.write(f"To: {message['to']}\n")
            file.write(f"Subject: {message['subject']}\n\n")
            file.write(f"{message.get_payload()}\n")

        print(f"Email zapisany do {file_path}")

class CustomSMTPServer:
    def __init__(self, host="0.0.0.0", port=1025):
        self.host = host
        self.port = port
        self.storage_path = "emails"

    def start(self):
        handler = CustomMessageHandler(self.storage_path)
        controller = Controller(handler, hostname=self.host, port=self.port)
        controller.start()
        print(f"Serwer SMTP uruchomiony na {self.host}:{self.port}")
        try:
            input("Naciśnij Enter, aby zatrzymać serwer...\n")
        except KeyboardInterrupt:
            pass
        finally:
            controller.stop()

if __name__ == "__main__":
    server = CustomSMTPServer()
    server.start()
