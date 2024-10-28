from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "El bot de Discord está en funcionamiento!"

def keep_alive():
    """Función para mantener el servidor web activo."""
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Ejecutar el servidor solo si se ejecuta directamente
if __name__ == "__main__":
    keep_alive()
