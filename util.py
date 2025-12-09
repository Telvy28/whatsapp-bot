def GetTextUser(message):
    text = ""
    typeMessage = message["type"]

    if typeMessage == "text":
        text = (message["text"])["body"]
    elif typeMessage == "interactive":
        interactiveObject = message["interactive"]
        typeInteractive = interactiveObject["type"]
        if typeInteractive == "button_reply":
            text = (interactiveObject["button_reply"])["title"]
            # También podríamos devolver el ID si lo necesitas para lógica interna
        elif typeInteractive == "list_reply":
            text = (interactiveObject["list_reply"])["title"] # O description
        else:
            print("sin mensaje")
    else:
        print("sin mensaje")
    return text

# Mensajes Simples
def TextMessage(text, number):
    data = {
            "messaging_product": "whatsapp",    
            "to": number,
            "type": "text",
            "text": { "body": text }
            }
    return data

def TextFormatMessage(number):
    data = {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "body": "*Hola usuario* \n_Hola usaurio_\n ~Hola usaurio~"
                }
            }
    return data

def ImageMessage(number):
    data = {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "image",
                "image": {
                    "link": "https://kinsta.com/es/wp-content/uploads/sites/8/2019/09/jpg-vs-jpeg.jpg"
                }
            }
    return data

def AudioMessage(number):
    data = {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "audio",
                "audio": {
                    "link": "https://dl.dropboxusercontent.com/s/eyb9txkepv0azqx/Beethoven%20-%20Variations%20on%20Ein%20M%C3%A4dchen%20oder%20Weibchen.mp3"
                }
            }
    return data

def VideoMessage(number):
    data = {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "video",
                "video": {
                    "link": "https://jumpshare.com/s/B7syaRF6S30Am9cu76JM"
                }
            }
    return data

def DocumentMessage(number):
    data = {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "document",
                "document": {
                    "link": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ7Hu_8JjnqYrRr4CJBw5uH4YWnsTyT4Ax_hH2hvrcop8wHf-soFUU3Jbl6vc1tzg/pub?output=xlsx"
                }
            }
    return data


def LocationMessage(number):
    data = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "location",
                "location": {
                    "latitude": "-11.991441593959951",
                    "longitude": "-77.01168136574333",
                    "name": "Isuzu Gaby",
                    "address": "Av. Próceres de la Independencia 2399, San Juan de Lurigancho 15419"
                }
            }
    return data

# Mensaje de Botones (Máximo 3 opciones)
def ButtonsMessage(number, body_text, buttons_list):
    # buttons_list: ["Opción 1", "Opción 2"]
    buttons = []
    for i, btn_text in enumerate(buttons_list):
        buttons.append({
            "type": "reply",
            "reply": {
                "id": f"btn_{i}",
                "title": btn_text
            }
        })

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": { "text": body_text },
            "action": { "buttons": buttons }
        }
    }
    return data


# Mensaje de Lista (Menú desplegable)
def ListMessage(number, header_text, body_text, options_list, title_list="Opciones"):
    # options_list debe ser una lista de diccionarios: [{"id": "001", "title": "Opción 1", "description": "desc"}]
    rows = []
    for i, option in enumerate(options_list):
        rows.append({
            "id": option["id"],
            "title": option["title"],
            "description": option.get("description", "")[:70] # WhatsApp limita caracteres
        })

    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": header_text },
            "body": { "text": body_text },
            "footer": { "text": "Seleccione una opción" },
            "action": {
                "button": title_list,
                "sections": [
                    {
                        "title": "Catálogo",
                        "rows": rows
                    }
                ]
            }
        }
    }
    return data

