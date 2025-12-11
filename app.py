from flask import Flask, request
import os
import util
import whatsappservices
import logging
from datetime import datetime
import pytz
import time

# Importar nuevos módulos
from neon_db import db
from conversation_intelligence import intelligence, response_builder
from telegram_notifier import telegram_notifier

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.route('/welcome', methods=['GET'])
def index():
    return "Bot ISUZU Gabriela Paucar - FASE 1 Activo ✅"

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
            
            # Log mensaje entrante
            db.log_message(number, 'incoming', text_user, 
                          content_type=message.get('type', 'text'))
            
            # Procesar conversación
            process_conversation(text_user, number)

        return "EVENT_RECEIVED", 200
    except Exception as e:
        logging.error(f"Error en webhook: {e}")
        return "EVENT_RECEIVED", 200

def get_time_greeting():
    """Obtiene saludo según hora en Perú"""
    tz_peru = pytz.timezone('America/Lima')
    hora_actual = datetime.now(tz_peru).hour
    
    if 5 <= hora_actual < 12:
        return "Buenos días"
    elif 12 <= hora_actual < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"

def send_with_delay(data, number):
    """Envía mensaje con delay humanizado"""
    whatsappservices.SendTypingIndicator(number)
    time.sleep(response_builder.typing_delay())
    result = whatsappservices.SendMessageWhatsapp(data)
    
    # Log mensaje saliente
    if result:
        content = data.get('text', {}).get('body', '') or str(data.get('interactive', ''))
        db.log_message(number, 'outgoing', content, 
                      content_type=data.get('type', 'text'))
    
    return result

def process_conversation(text, number):
    """Máquina de estados principal con validaciones"""
    
    # Obtener o crear conversación
    conversation = db.get_or_create_conversation(number)
    step = conversation.get("current_step")
    
    # ====== DETECCIÓN DE INTENCIONES GLOBALES ======
    intent = intelligence.detect_intent(text)
    
    if intent == 'ubicacion':
        msg = "📍 Nuestra sede está en:\n\n*ISUZU CAMIONES AUTOMOTRIZ CISNE*"
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
        
        # Enviar ubicación
        location_data = util.LocationMessage(number)
        send_with_delay(location_data, number)
        
        msg_continue = "¿Deseas continuar con la cotización? Responde *SI* para continuar."
        data = util.TextMessage(msg_continue, number)
        send_with_delay(data, number)
        return
    
    elif intent == 'hablar_humano':
        db.handoff_to_human(number, "Cliente solicitó atención humana")
        
        msg = "🙋‍♀️ Entendido. En un momento la asesora *Gabriela Paucar* se comunicará contigo personalmente.\n\n📞 También puedes llamarnos directamente al *01-XXX-XXXX*"
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
        
        # Notificar a Gabriela por Telegram
        telegram_notifier.send_handoff_alert(
            number, 
            conversation.get('name', 'Cliente'), 
            "Solicitud de atención humana"
        )
        return
    
    elif intent == 'salir':
        db.complete_conversation(number)
        msg = "Entendido. Si cambias de opinión, escríbenos cuando quieras. ¡Hasta pronto! 👋"
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
        return
    
    # ====== FLUJO CONVERSACIONAL ======
    
    # --- PASO 0: SALUDO INICIAL ---
    if step == "START":
        msg = "👋 Te saluda el *Asistente Virtual* de *Gabriela Paucar* - 👩🏻‍💼 Asesora Comercial de ISUZU CAMIONES AUTOMOTRIZ CISNE.\n📍 SEDE LIMA.\n\nPara atenderte mejor, por favor indícame: *¿Cuál es tu nombre y apellido?*"
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
        
        db.update_conversation_step(number, "WAITING_NAME")
    
    # --- PASO 1: CAPTURAR NOMBRE ---
    elif step == "WAITING_NAME":
        # Extraer nombre limpio
        name = intelligence.extract_name(text)
        
        if len(name.split()) < 2:
            # Nombre muy corto, validación fallida
            retry_count = db.log_failed_validation(number, step, text, "Nombre y Apellido")
            error_msg = response_builder.format_error_retry(step, retry_count)
            data = util.TextMessage(error_msg, number)
            send_with_delay(data, number)
            return
        
        # Nombre válido
        db.update_conversation_step(number, "WAITING_DNI_LOC", name=name)
        
        saludo = get_time_greeting()
        msg = f"{saludo} estimado *{name}*. Un gusto saludarte.\n\nPara continuar, por favor brÃ­ndame tu *DNI o RUC* y desde qué *Departamento/Provincia* nos escribes.\n\n_Ejemplo: 10283749, Huancayo_"
        
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
    
    # --- PASO 2: CAPTURAR DNI Y UBICACIÓN ---
    elif step == "WAITING_DNI_LOC":
        # Extraer DNI y ubicación
        extracted = intelligence.extract_dni_location(text)
        
        if not extracted['dni'] or not extracted['location']:
            retry_count = db.log_failed_validation(number, step, text, "DNI/RUC + Ciudad")
            error_msg = response_builder.format_error_retry(step, retry_count)
            data = util.TextMessage(error_msg, number)
            send_with_delay(data, number)
            return
        
        # Datos válidos
        db.update_conversation_step(
            number, 
            "WAITING_CATEGORY",
            dni_ruc=extracted['dni'],
            location=extracted['location']
        )
        
        # Enviar botones de categoría
        buttons = ["Camión Isuzu", "Camionetas"]
        msg_body = "🚘 *Tipo de unidad*\n\n¿En qué tipo de unidad estás interesado?"
        
        data = util.ButtonsMessage(number, msg_body, buttons)
        send_with_delay(data, number)
    
    # --- PASO 3: ELEGIR CATEGORÍA ---
    elif step == "WAITING_CATEGORY":
        # Validar categoría
        category = intelligence.validate_category(text)
        
        if not category:
            retry_count = db.log_failed_validation(number, step, text, "Camión o Camioneta")
            error_msg = response_builder.format_error_retry(step, retry_count)
            
            # Reenviar botones
            buttons = ["Camión Isuzu", "Camionetas"]
            msg_body = f"{error_msg}\n\n🚘 *Tipo de unidad*\n\n¿En qué tipo de unidad estás interesado?"
            data = util.ButtonsMessage(number, msg_body, buttons)
            send_with_delay(data, number)
            return
        
        # Categoría válida
        db.update_conversation_step(number, "WAITING_MODEL", category=category)
        
        # Preparar lista de modelos
        options = []
        msg_body = ""
        header_list = "Modelos Disponibles"

        if "Camión" in category:
            options = [
                {"id": "mod_1", "title": "FVR 10ton", "description": "Ideal para carga pesada"},
                {"id": "mod_2", "title": "NLR 3TON", "description": "Urbano y versátil"},
                {"id": "mod_3", "title": "NPS 4x4", "description": "Todo terreno"}
            ]
            msg_body = "Excelente elección. Isuzu es líder en camiones. ¿Qué modelo buscas?"
            
        else:  # Camionetas
            options = [
                {"id": "mod_4", "title": "Chevrolet Captiva", "description": "SUV Familiar"},
                {"id": "mod_5", "title": "Subaru XL", "description": "Aventura y confort"}
            ]
            msg_body = "¿Qué camioneta se ajusta a tus necesidades?"

        data = util.ListMessage(number, header_list, msg_body, options, "Ver Modelos")
        send_with_delay(data, number)
    
    # --- PASO 4: ELEGIR MODELO ---
    elif step == "WAITING_MODEL":
        # Guardar modelo seleccionado
        db.update_conversation_step(number, "WAITING_COLOR", model=text)
        
        buttons = ["Blanco", "Rojo", "Azul"]
        msg = f"Perfecto, el *{text}* es una gran máquina.\n¿Tienes algún color de preferencia?"
        
        data = util.ButtonsMessage(number, msg, buttons)
        send_with_delay(data, number)
    
    # --- PASO 5: ELEGIR COLOR ---
    elif step == "WAITING_COLOR":
        # Validar color
        color = intelligence.validate_color(text)
        
        if not color:
            color = text.capitalize()  # Aceptar cualquier texto como color
        
        db.update_conversation_step(number, "WAITING_CALL_TIME", color=color)
        
        conv = db.get_or_create_conversation(number)
        nombre = conv.get("name", "")
        modelo = conv.get("model", "")
        
        msg = f"Gracias *{nombre}*. Tengo registrado tu interés en un *{modelo}* color {color}.\n\n📞 *¿A qué hora prefieres que la asesora Gabriela te llame?*\n\n_Ejemplo: Mañana 10am, Hoy 3pm, etc._"
        
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
    
    # --- PASO 6: AGENDAR LLAMADA ---
    elif step == "WAITING_CALL_TIME":
        db.update_conversation_step(number, "FINISHED", preferred_call_time=text)
        
        # Marcar como completada
        db.complete_conversation(number)
        
        msg = "✅ ¡Perfecto! La asesora *Gabriela Paucar* se comunicará contigo en el horario indicado.\n\n🙏 Muchas gracias por contactar a *Isuzu Automotriz Cisne*.\n\n_Si necesitas algo más, escríbeme cuando quieras._"
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
        
        # Enviar notificación a Gabriela por Telegram
        summary = db.get_conversation_summary(number)
        if summary:
            telegram_notifier.send_lead_notification(summary)
    
    # --- CONVERSACIÓN TERMINADA ---
    elif step == "FINISHED":
        msg = "Tu solicitud ya fue registrada. La asesora Gabriela se comunicará contigo pronto.\n\n¿Deseas hacer *otra cotización*? Responde *SI* para comenzar de nuevo."
        data = util.TextMessage(msg, number)
        send_with_delay(data, number)
        
        # Si dice "si", reiniciar conversación
        if text.lower() in ['si', 'sí', 'yes', 'ok']:
            db.update_conversation_step(number, "START")
            process_conversation("", number)  # Trigger START

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)