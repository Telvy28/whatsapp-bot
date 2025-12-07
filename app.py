from flask import Flask, request
import os
import util
import whatsappservices
import logging

app = Flask(__name__)

# Configurar logging para que sea visible en Railway
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

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
    print("=" * 50)
    print("=== WEBHOOK RECIBIDO ===")
    print("=" * 50)
    
    try:
        # Asegurarnos de que recibimos JSON
        if not request.is_json:
            raw = request.get_data(as_text=True)
            print(f"ERROR: Body no es JSON. Raw body: {raw}")
            app.logger.warning("POST /whatsapp: body no JSON. Raw body: %s", raw)
            return "no event received - not json", 400

        body = request.get_json()
        print(f"Payload recibido: {body}")
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
                    
                    print(f"Procesando mensaje de {number}: '{text}'")
                    print(f"Phone ID: {phone_id}")
                    
                    GenerateMessage(text, number, phone_id)
                    
                    app.logger.info("Processed message from %s (phone_id=%s): %s", number, phone_id, text)
                    print(f"Mensaje procesado exitosamente")

        if found_message:
            print("✓ Evento procesado correctamente")
            return "EVENT_RECEIVED", 200

        print("No se encontraron mensajes en el payload")
        app.logger.info("POST /whatsapp: no messages found in payload")
        return "no event received", 200

    except Exception as e:
        print(f"ERROR en webhook: {str(e)}")
        app.logger.exception("Error procesando webhook /whatsapp")
        return "internal error", 500

def GenerateMessage(text, number, phone_id=None):
    print(f"→ GenerateMessage llamado con texto: '{text}'")
    
    # Respuesta por defecto - eco del mensaje del usuario
    data = util.TextMessage(f"Persona dijo: {text}", number)
    print(f"→ Mensaje por defecto creado: eco del texto")
    
    # Respuestas especiales por palabra clave
    if "format" in text.lower():
        data = util.TextFormatMessage(number)
        print("→ Mensaje tipo: FORMAT")
    elif "image" in text.lower():
        data = util.ImageMessage(number)
        print("→ Mensaje tipo: IMAGE")
    elif "audio" in text.lower():
        data = util.AudioMessage(number)
        print("→ Mensaje tipo: AUDIO")
    elif "video" in text.lower():
        data = util.VideoMessage(number)
        print("→ Mensaje tipo: VIDEO")
    elif "document" in text.lower():
        data = util.DocumentMessage(number)
        print("→ Mensaje tipo: DOCUMENT")
    elif "location" in text.lower():
        data = util.LocationMessage(number)
        print("→ Mensaje tipo: LOCATION")
    elif "button" in text.lower():
        data = util.ButtonsMessage(number)
        print("→ Mensaje tipo: BUTTON")
    elif "list" in text.lower():
        data = util.ListMessage(number)
        print("→ Mensaje tipo: LIST")

    print(f"→ Enviando mensaje a WhatsApp...")
    resultado = whatsappservices.SendMessageWhatsapp(data)
    
    if resultado:
        print("✓ Mensaje enviado exitosamente")
    else:
        print("✗ ERROR: Fallo al enviar mensaje")

if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))  # Render usa PORT
    app.run(host='0.0.0.0', port=port)