from flask import Flask, request
import os
import util
import whatsappservices

app = Flask(__name__)
@app.route('/welcome', methods=['GET'])
def index():
    return "Welcome to the Flask App!"

@app.route('/whatsapp', methods=['GET'])
def Verifytoken():

    try:
        access_token = os.getenv("VERIFY_TOKEN")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        # Caso 1: petición de verificación correcta (ambos parámetros presentes)
        if token is not None and challenge is not None:
            if token == access_token:
                return challenge
            # token presente pero no coincide
            return "Invalid verify token", 403

        # Caso 2: GET sin parámetros -> devolver información útil (200)
        if token is None and challenge is None:
            return (
                "Webhook endpoint: usar '?hub.verify_token=...&hub.challenge=...' "
                "para verificación de webhook."), 200

        # Caso 3: parámetros incompletos -> bad request
        return "Missing parameters", 400
    except Exception as e:
        return str(e), 500
    
@app.route('/whatsapp', methods=['POST'])


def RecivedMessage():

    try:
        # Asegurarnos de que recibimos JSON
        if not request.is_json:
            raw = request.get_data(as_text=True)
            app.logger.warning("POST /whatsapp: body no JSON. Raw body: %s", raw)
            return "no event received - not json", 400

        body = request.get_json()
        app.logger.info("POST /whatsapp payload: %s", body)

        entries = body.get("entry", []) or []
        found_message = False

        for entry in entries:
            for change in entry.get("changes", []) or []:
                value = change.get("value", {})
                phone_id = (value.get("metadata") or {}).get("phone_number_id")
                messages = value.get("messages") or []
                for message in messages:
                    found_message = True
                    number = message.get("from")
                    text = util.GetTextUser(message)
                    GenerateMessage(text, number, phone_id)
                    app.logger.info("Processed message from %s (phone_id=%s): %s", number, phone_id, text)

        if found_message:
            return "EVENT_RECEIVED", 200

        app.logger.info("POST /whatsapp: no messages found in payload")
        return "no event received", 200

    except Exception:
        app.logger.exception("Error procesando webhook /whatsapp")
        return "internal error", 500

def GenerateMessage(text, number, phone_id=None):
    # Respuesta por defecto - eco del mensaje del usuario
    data = util.TextMessage(f"Persona dijo: {text}", number)
    
    # Respuestas especiales por palabra clave
    if "format" in text.lower():
        data = util.TextFormatMessage(number)
    elif "image" in text.lower():
        data = util.ImageMessage(number)
    elif "audio" in text.lower():
        data = util.AudioMessage(number)
    elif "video" in text.lower():
        data = util.VideoMessage(number)
    elif "document" in text.lower():
        data = util.DocumentMessage(number)
    elif "location" in text.lower():
        data = util.LocationMessage(number)
    elif "button" in text.lower():
        data = util.ButtonsMessage(number)
    elif "list" in text.lower():
        data = util.ListMessage(number)

    whatsappservices.SendMessageWhatsapp(data)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))  # Render usa PORT
    app.run(host='0.0.0.0', port=port)