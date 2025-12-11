import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from datetime import datetime
import logging

class NeonDB:
    """
    Maneja todas las operaciones con Neon PostgreSQL
    Usa connection pooling para mejor performance
    """
    
    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Crea pool de conexiones a Neon"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # min=1, max=10 conexiones
                host=os.getenv("NEON_HOST"),
                database=os.getenv("NEON_DATABASE"),
                user=os.getenv("NEON_USER"),
                password=os.getenv("NEON_PASSWORD"),
                port=os.getenv("NEON_PORT", "5432"),
                sslmode='require'
            )
            logging.info("✅ Neon DB pool inicializado")
        except Exception as e:
            logging.error(f"❌ Error conectando a Neon: {e}")
            raise
    
    def get_connection(self):
        """Obtiene conexión del pool"""
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Devuelve conexión al pool"""
        self.connection_pool.putconn(conn)
    
    # ==================== CONVERSACIONES ====================
    
    def get_or_create_conversation(self, phone_number):
        """
        Obtiene conversación existente o crea una nueva
        Returns: dict con datos de la conversación
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Intentar obtener conversación existente
                cursor.execute("""
                    SELECT * FROM conversations 
                    WHERE phone_number = %s 
                    AND status != 'COMPLETED'
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (phone_number,))
                
                conversation = cursor.fetchone()
                
                if conversation:
                    return dict(conversation)
                
                # Crear nueva conversación
                cursor.execute("""
                    INSERT INTO conversations (phone_number, current_step, status)
                    VALUES (%s, 'START', 'IN_PROGRESS')
                    RETURNING *
                """, (phone_number,))
                
                conn.commit()
                new_conv = cursor.fetchone()
                return dict(new_conv)
                
        except Exception as e:
            conn.rollback()
            logging.error(f"Error en get_or_create_conversation: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def update_conversation_step(self, phone_number, step, **kwargs):
        """
        Actualiza el paso actual y opcionalmente otros campos
        kwargs puede incluir: name, dni_ruc, location, category, model, color, etc.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # Construir query dinámicamente
                fields = ["current_step = %s"]
                values = [step]
                
                for key, value in kwargs.items():
                    if value is not None:
                        fields.append(f"{key} = %s")
                        values.append(value)
                
                values.append(phone_number)
                
                query = f"""
                    UPDATE conversations 
                    SET {', '.join(fields)}
                    WHERE phone_number = %s
                """
                
                cursor.execute(query, values)
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logging.error(f"Error en update_conversation_step: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def complete_conversation(self, phone_number):
        """Marca conversación como completada"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE conversations 
                    SET status = 'COMPLETED', 
                        current_step = 'FINISHED',
                        completed_at = NOW()
                    WHERE phone_number = %s
                """, (phone_number,))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    def handoff_to_human(self, phone_number, reason="Cliente solicitó hablar con humano"):
        """Marca conversación para atención humana"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE conversations 
                    SET status = 'HUMAN_HANDOFF',
                        current_step = 'EN_ATENCION_HUMANA',
                        notes = %s
                    WHERE phone_number = %s
                """, (reason, phone_number))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    # ==================== MENSAJES ====================
    
    def log_message(self, phone_number, message_type, content, content_type='text', intent=None):
        """
        Registra cada mensaje enviado/recibido
        message_type: 'incoming' o 'outgoing'
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # Obtener conversation_id
                cursor.execute(
                    "SELECT id FROM conversations WHERE phone_number = %s ORDER BY created_at DESC LIMIT 1",
                    (phone_number,)
                )
                result = cursor.fetchone()
                conversation_id = result[0] if result else None
                
                cursor.execute("""
                    INSERT INTO messages 
                    (conversation_id, phone_number, message_type, content_type, content, intent)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (conversation_id, phone_number, message_type, content_type, content, intent))
                
                conn.commit()
        except Exception as e:
            logging.error(f"Error logging message: {e}")
            # No lanzar excepción para no romper flujo principal
        finally:
            self.return_connection(conn)
    
    def get_conversation_history(self, phone_number, limit=50):
        """Obtiene historial de mensajes de una conversación"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT m.* 
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.phone_number = %s
                    ORDER BY m.timestamp DESC
                    LIMIT %s
                """, (phone_number, limit))
                
                return [dict(row) for row in cursor.fetchall()]
        finally:
            self.return_connection(conn)
    
    # ==================== VALIDACIONES ====================
    
    def log_failed_validation(self, phone_number, step, user_input, expected_format):
        """Registra intentos fallidos para análisis"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # Verificar si ya existe un registro reciente
                cursor.execute("""
                    SELECT retry_count FROM failed_validations
                    WHERE phone_number = %s 
                    AND step = %s
                    AND timestamp > NOW() - INTERVAL '5 minutes'
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (phone_number, step))
                
                result = cursor.fetchone()
                retry_count = (result[0] + 1) if result else 1
                
                cursor.execute("""
                    INSERT INTO failed_validations 
                    (phone_number, step, user_input, expected_format, retry_count)
                    VALUES (%s, %s, %s, %s, %s)
                """, (phone_number, step, user_input, expected_format, retry_count))
                
                conn.commit()
                return retry_count
        finally:
            self.return_connection(conn)
    
    # ==================== REPORTES ====================
    
    def get_conversation_summary(self, phone_number):
        """Obtiene resumen completo para notificación a Gabriela"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        phone_number,
                        name,
                        dni_ruc,
                        location,
                        category,
                        model,
                        color,
                        preferred_call_time,
                        status,
                        created_at,
                        updated_at
                    FROM conversations
                    WHERE phone_number = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (phone_number,))
                
                return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
        finally:
            self.return_connection(conn)

# Instancia global
db = NeonDB()
