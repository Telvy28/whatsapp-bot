from flask import Flask, request
import os
import util
import whatsappservices
import logging
from datetime import datetime
import pytz # Necesario para la hora de Perú, asegúrate de instalarlo o usar hora server

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- MEMORIA TEMPORAL (Diccionario) ---
# En producción real, esto debería ir a una Base de Datos (Supabase/Sheets)
# Estructura: { "519...": { "step": 0, "name": "Pepe", "category": "Camión" } }
users_state = {} 

@app.route('/welcome', methods=['GET'])
def index():
    return "Bot de Gabriela Paucar Activo"

@app.route('/whatsapp', methods=['GET'])
def Verifytoken():
    try:
        access_token = os.getenv("VERIFY_TOKEN")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token is not None and challenge is not None and token == access_token:
            return challenge
        return "Auth Failed", 403
    except Exception as e:
        return str(e), 500

@app.route('/whatsapp', methods=['POST'])
def RecivedMessage():
    try:
        body = request.get_json()
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" in value:
            message = value["messages"][0]
            number = message["from"]
            text_user = util.GetTextUser(message)
            
            # Inicializar usuario si no existe
            if number not in users_state:
                users_state[number] = {"step": "START"}

            process_conversation(text_user, number)

        return "EVENT_RECEIVED", 200
    except Exception as e:
        print(f"Error: {e}")
        return "EVENT_RECEIVED", 200

def get_time_greeting():
    # Obtener hora Perú
    tz_peru = pytz.timezone('America/Lima')
    hora_actual = datetime.now(tz_peru).hour
    
    if 5 <= hora_actual < 12:
        return "Buenos días"
    elif 12 <= hora_actual < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"

def process_conversation(text, number):
    state = users_state[number]
    step = state.get("step")
    
    # --- PASO 0: SALUDO INICIAL ---
    if step == "START":
        msg = "👋 Te saluda *Gabriela Paucar* - 👩🏻‍💼 Asesora Comercial de ISUZU CAMIONES AUTOMOTRIZ CISNE.\n📍 SEDE LIMA.\n\nPara atenderte mejor, por favor indícame: *¿Cuál es tu nombre y apellido?*"
        data = util.TextMessage(msg, number)
        whatsappservices.SendMessageWhatsapp(data)
        users_state[number]["step"] = "WAITING_NAME"
        
    # --- PASO 1: CAPTURAR NOMBRE Y PEDIR DNI ---
    elif step == "WAITING_NAME":
        name = text.title()
        users_state[number]["name"] = name
        
        saludo = get_time_greeting()
        msg = f"{saludo} estimado *{name}*. Un gusto saludarte.\n\nPara continuar, por favor bríndame tu *DNI o RUC* y desde qué *Departamento/Provincia* nos escribes (Ej: 1028937, Huancayo)."
        
        data = util.TextMessage(msg, number)
        whatsappservices.SendMessageWhatsapp(data)
        users_state[number]["step"] = "WAITING_DNI_LOC"

    # --- PASO 2: ELEGIR TIPO DE VEHICULO (AHORA CON BOTONES) ---
    elif step == "WAITING_DNI_LOC":
        users_state[number]["dni_loc"] = text
        
        # CAMBIO: Usamos Botones en vez de Lista para que se vean directo
        # Nota: El texto del botón no puede ser muy largo
        buttons = ["Camión Isuzu", "Camionetas"]
        
        msg_body = "🚘 *Tipo de unidad*\n\n¿En qué tipo de unidad estás interesado?"
        
        data = util.ButtonsMessage(number, msg_body, buttons)
        whatsappservices.SendMessageWhatsapp(data)
        users_state[number]["step"] = "WAITING_CATEGORY"

    # --- PASO 3: ELEGIR MODELO ESPECIFICO ---
    elif step == "WAITING_CATEGORY":
        category_choice = text.lower()
        users_state[number]["category"] = category_choice
        
        options = []
        msg_body = ""
        header_list = "Modelos Disponibles"

        # Lógica para detectar qué botón presionó
        if "camión" in category_choice or "isuzu" in category_choice:
            options = [
                {"id": "mod_1", "title": "FVR 10ton", "description": "Ideal para carga pesada"},
                {"id": "mod_2", "title": "NLR 3TON", "description": "Urbano y versátil"},
                {"id": "mod_3", "title": "NPS 4x4", "description": "Todo terreno"}
            ]
            msg_body = "Excelente elección. Isuzu es líder en camiones. ¿Qué modelo busca?"
            
        elif "camioneta" in category_choice:
            options = [
                {"id": "mod_4", "title": "Chevrolet Captiva", "description": "SUV Familiar"},
                {"id": "mod_5", "title": "Subaru XL", "description": "Aventura y confort"}
            ]
            msg_body = "¿Qué camioneta se ajusta a sus necesidades?"
            
        else:
            # Si el usuario escribió algo raro en vez de tocar el botón
            msg_body = "⚠️ No entendí su selección.\nPor favor seleccione una opción tocando los botones de arriba 👆"
            # Reenviamos los botones para que intente de nuevo
            buttons = ["Camión Isuzu", "Camionetas"]
            data = util.ButtonsMessage(number, msg_body, buttons)
            whatsappservices.SendMessageWhatsapp(data)
            return # Salimos para no cambiar de estado

        # Si detectó bien la categoría, mostramos la lista de modelos
        data = util.ListMessage(number, header_list, msg_body, options, "Ver Modelos")
        whatsappservices.SendMessageWhatsapp(data)
        users_state[number]["step"] = "WAITING_MODEL"

    # --- PASO 4: ELEGIR COLOR ---
    elif step == "WAITING_MODEL":
        # Guardamos el modelo seleccionado
        users_state[number]["model"] = text
        
        buttons = ["Blanco", "Rojo", "Azul"]
        msg = f"Perfecto, el *{text}* es una gran máquina.\n¿Tiene algún color de preferencia?"
        
        data = util.ButtonsMessage(number, msg, buttons)
        whatsappservices.SendMessageWhatsapp(data)
        users_state[number]["step"] = "WAITING_COLOR"

    # --- PASO 5: AGENDAR LLAMADA ---
    elif step == "WAITING_COLOR":
        users_state[number]["color"] = text
        
        nombre = users_state[number].get("name")
        modelo = users_state[number].get("model")
        
        msg = f"Gracias Don {nombre}. Tengo registrado su interés en un *{modelo}* color {text}.\n\n📞 *¿Está libre para una breve llamada con la asesora Gabriela?* \n\nPor favor indíqueme a qué hora prefiere que lo llamemos."
        
        data = util.TextMessage(msg, number)
        whatsappservices.SendMessageWhatsapp(data)
        users_state[number]["step"] = "FINISHED"
    
    # --- FINAL ---
    elif step == "FINISHED":
        msg = "¡Entendido! La asesora Gabriela Paucar se comunicará con usted en el horario indicado. Muchas gracias por contactar a Isuzu Automotriz Cisne."
        data = util.TextMessage(msg, number)
        whatsappservices.SendMessageWhatsapp(data)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)