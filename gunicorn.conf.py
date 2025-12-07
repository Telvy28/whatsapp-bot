import os

# Leer el puerto de la variable de entorno PORT
port = os.getenv("PORT", "8080")

# Configuración de gunicorn
bind = f"0.0.0.0:{port}"
workers = 2
worker_class = "sync"
accesslog = "-"
errorlog = "-"
loglevel = "info"

print(f"Gunicorn configurado para escuchar en: {bind}")