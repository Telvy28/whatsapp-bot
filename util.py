def GetTextUser(message):
    text = ""
    typemessage = message["type"]

    if typemessage == "text":
        text = (message["text"])["body"]
    elif typemessage == "interactive":
        interactiveObject = message["interactive"]
        typeinteractive = interactiveObject["type"]
        if typeinteractive == "button_reply":
            text = (interactiveObject["button_reply"])["title"]
        elif typeinteractive == "list_reply":
            text = (interactiveObject["list_reply"])["title"]
        else:
            print("Tipo interactivo no soportado:")
    else:
        print("Tipo de mensaje no soportado:", typemessage)
    return text


def TextMessage(text, number):
    data = {
            "messaging_product": "whatsapp",    
            "to": number,
            "text": {
                "body": text
            },
            "type": "text",
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

def ButtonsMessage(number):
    data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {
                        "type": "text",
                        "text": "identifiacion de usuario",
                    },
                    "body": {
                        "text": "¿Confirmas tu registro?"
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "001",
                                    "title": "Si confirmo 👍"
                                }
                            },
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "002",
                                    "title": "No joven 🤕"
                                }
                            }
                        ]
                    }
                }
            }
    return data


def ListMessage(number):
    data = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {
                        "text": "✅ I have these options"
                    },
                    "footer": {
                        "text": "Select an option"
                    },
                    "action": {
                        "button": "See options",
                        "sections": [
                            {
                                "title": "Buy and sell products",
                                "rows": [
                                    {
                                        "id": "main-buy",
                                        "title": "Buy",
                                        "description": "Buy the best product your home"
                                    },
                                    {
                                        "id": "main-sell",
                                        "title": "Sell",
                                        "description": "Sell your products"
                                    }
                                ]
                            },
                            {
                                "title": "📍center of attention",
                                "rows": [
                                    {
                                        "id": "main-agency",
                                        "title": "Agency",
                                        "description": "Your can visit our agency"
                                    },
                                    {
                                        "id": "main-contact",
                                        "title": "Contact center",
                                        "description": "One of our agents will assist you"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
    return data

