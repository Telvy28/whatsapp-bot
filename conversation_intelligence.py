import re
from typing import Optional, Dict, Tuple

class ConversationIntelligence:
    """
    Maneja extracción de datos, detección de intenciones y validaciones
    """
    
    # Patrones de saludos comunes en Perú
    GREETING_PATTERNS = [
        r'^\s*hola\s*,?\s*',
        r'^\s*buenos?\s+(d[ií]as?|tardes?|noches?)\s*,?\s*',
        r'^\s*que\s+tal\s*,?\s*',
        r'^\s*soy\s+',
        r'^\s*me\s+llamo\s+',
        r'^\s*mi\s+nombre\s+es\s+'
    ]
    
    # Palabras clave para detección de intenciones
    INTENT_KEYWORDS = {
        'ubicacion': [
            'ubicación', 'ubicacion', 'dirección', 'direccion',
            'donde están', 'donde esta', 'como llegar', 'donde queda',
            'local', 'tienda', 'sede', 'oficina', 'showroom'
        ],
        'ayuda': [
            'ayuda', 'no entiendo', 'explicar', 'como funciona',
            'que hago', 'confundido', 'explicame'
        ],
        'hablar_humano': [
            'hablar con', 'persona', 'asesor', 'asesora', 'humano',
            'gabriela', 'alguien', 'operador', 'atencion'
        ],
        'salir': [
            'salir', 'cancelar', 'no quiero', 'chau', 'adios',
            'terminar', 'ya no'
        ]
    }
    
    # Opciones válidas por categoría
    VALID_OPTIONS = {
        'category': ['camión', 'camion', 'isuzu', 'camioneta', 'camionetas'],
        'color': ['blanco', 'rojo', 'azul', 'negro', 'gris', 'plata']
    }
    
    @staticmethod
    def extract_name(text: str) -> str:
        """
        Extrae nombre limpio de respuestas ambiguas
        
        Ejemplos:
        - "Hola soy Juan Perez" → "Juan Perez"
        - "Buenos días, me llamo María López" → "María López"
        - "Mi nombre es Carlos" → "Carlos"
        """
        # Remover saludos y frases introductorias
        cleaned = text
        for pattern in ConversationIntelligence.GREETING_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Limpiar caracteres especiales pero mantener tildes y ñ
        cleaned = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', cleaned)
        
        # Remover espacios extras
        cleaned = ' '.join(cleaned.split())
        
        # Title case
        return cleaned.strip().title()
    
    @staticmethod
    def extract_dni_location(text: str) -> Dict[str, Optional[str]]:
        """
        Extrae DNI/RUC y ubicación de texto combinado
        
        Ejemplos:
        - "10283749, Lima" → {"dni": "10283749", "location": "Lima"}
        - "20512345678 Huancayo" → {"dni": "20512345678", "location": "Huancayo"}
        """
        result = {"dni": None, "location": None}
        
        # Buscar DNI (8 dígitos) o RUC (11 dígitos)
        dni_match = re.search(r'\b(\d{8}|\d{11})\b', text)
        if dni_match:
            result["dni"] = dni_match.group(1)
            # Remover DNI del texto para extraer ubicación
            text = text.replace(dni_match.group(1), '')
        
        # Limpiar y extraer ubicación
        location = re.sub(r'[,\s]+', ' ', text).strip().title()
        if location:
            result["location"] = location
        
        return result
    
    @staticmethod
    def detect_intent(text: str) -> Optional[str]:
        """
        Detecta intención del usuario basado en keywords
        
        Returns: 'ubicacion', 'ayuda', 'hablar_humano', 'salir', o None
        """
        text_lower = text.lower()
        
        for intent, keywords in ConversationIntelligence.INTENT_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        
        return None
    
    @staticmethod
    def validate_category(text: str) -> Optional[str]:
        """
        Valida y normaliza selección de categoría de vehículo
        
        Returns: "camión" o "camioneta", o None si no es válido
        """
        text_lower = text.lower()
        
        if any(opt in text_lower for opt in ['camión', 'camion', 'isuzu']):
            return "Camión Isuzu"
        elif any(opt in text_lower for opt in ['camioneta', 'camionetas']):
            return "Camionetas"
        
        return None
    
    @staticmethod
    def validate_color(text: str) -> Optional[str]:
        """
        Valida y normaliza selección de color
        """
        text_lower = text.lower()
        
        for color in ConversationIntelligence.VALID_OPTIONS['color']:
            if color in text_lower:
                return color.capitalize()
        
        return None
    
    @staticmethod
    def is_valid_phone_peru(phone: str) -> bool:
        """
        Valida formato de teléfono peruano
        Formato esperado: 51XXXXXXXXX (código país + 9 dígitos)
        """
        return bool(re.match(r'^51\d{9}$', phone))
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Limpia texto de caracteres especiales y normaliza espacios
        """
        # Remover emojis y caracteres especiales
        text = re.sub(r'[^\w\s,.]', '', text, flags=re.UNICODE)
        # Normalizar espacios
        return ' '.join(text.split())


class ResponseBuilder:
    """
    Construye respuestas dinámicas con personalización
    """
    
    @staticmethod
    def typing_delay() -> float:
        """
        Retorna delay aleatorio para simular typing humano
        """
        import random
        return random.uniform(1.5, 3.0)
    
    @staticmethod
    def format_error_retry(step: str, retry_count: int) -> str:
        """
        Genera mensajes de error progresivamente más claros
        """
        messages = {
            'WAITING_NAME': {
                1: "⚠️ Por favor, escribe tu nombre completo (nombre y apellido).",
                2: "Por ejemplo: *Juan Pérez* o *María González*",
                3: "Necesito tu nombre para continuar. Si tienes problemas, escribe 'ayuda'."
            },
            'WAITING_DNI_LOC': {
                1: "⚠️ Por favor, escribe tu DNI (8 dígitos) o RUC (11 dígitos) seguido de tu ciudad.\n\nEjemplo: 10283749, Lima",
                2: "Formato correcto:\n*DNI ciudad*\n\nEjemplo: 45678912 Arequipa",
                3: "Si necesitas ayuda, escribe 'ayuda' o te comunico con un asesor."
            },
            'WAITING_CATEGORY': {
                1: "⚠️ Por favor, selecciona una opción tocando los botones de arriba 👆",
                2: "Debes presionar uno de los botones para continuar.",
                3: "¿Necesitas ayuda? Escribe 'ayuda' para asistencia."
            }
        }
        
        step_messages = messages.get(step, {})
        return step_messages.get(retry_count, step_messages.get(3, "Por favor intenta nuevamente."))
    
    @staticmethod
    def format_summary_telegram(data: Dict) -> str:
        """
        Formatea resumen de conversación para notificación Telegram
        """
        return f"""
🔔 *NUEVO LEAD - ISUZU CISNE*

👤 *Cliente:* {data.get('name', 'N/A')}
📱 *Teléfono:* +{data.get('phone_number', 'N/A')}
🆔 *DNI/RUC:* {data.get('dni_ruc', 'N/A')}
📍 *Ubicación:* {data.get('location', 'N/A')}

🚗 *Interés:*
• Categoría: {data.get('category', 'N/A')}
• Modelo: {data.get('model', 'N/A')}
• Color: {data.get('color', 'N/A')}

📞 *Llamar:* {data.get('preferred_call_time', 'A coordinar')}

⏰ *Registrado:* {data.get('created_at', '')}

_Estado: {data.get('status', 'Pendiente')}_
"""

# Instancias globales
intelligence = ConversationIntelligence()
response_builder = ResponseBuilder()
