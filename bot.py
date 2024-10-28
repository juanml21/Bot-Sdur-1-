import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
from threading import Thread
from webserver import keep_alive  # Importar la función keep_alive
import asyncio

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener el token desde la variable de entorno
TOKEN = os.getenv("DISCORD_TOKEN")

# Crear una instancia de Intents
intents = discord.Intents.default()  # Puedes usar .all() si necesitas todos los intents
intents.messages = True  # Habilita el intent para recibir mensajes
intents.message_content = True  # Habilita el intent para el contenido de los mensajes

# Inicializar el bot
bot = commands.Bot(command_prefix="!", intents=intents)

# ID del canal donde se enviarán los recordatorios
REMINDER_CHANNEL_ID = 800086279643463731  # Reemplaza con el ID de tu canal

# Variable global para almacenar la moción
mocion_global = ""

@bot.event
async def on_ready():
    print(f'{bot.user} ha conectado a Discord!')
    recordatorio_puntajes.start()  # Inicia la tarea al iniciar el bot

@tasks.loop(hours=24)  # Envía un recordatorio cada 24 horas
async def recordatorio_puntajes():
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if channel:
        await channel.send(
            "@everyone 🚨 ¡Atención! 🚨\n"
            "Es hora de poner sus puntajes al día. 📝✨\n"
            "Recuerden, no actualizarlos es como ir a una batalla sin armadura... ¡no lo hagan! 🛡️⚔️\n"
            "Así que, ¡corran a actualizar sus puntajes y asegúrense de que todos tengan el reconocimiento que merecen! 🎉🙌"
        )
    else:
        print("No se pudo encontrar el canal para enviar recordatorios.")

def update_scores(nombre, nuevo_puntaje):
    """Actualizar o agregar el puntaje del jugador en el archivo JSON."""
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        # Actualizar o agregar el puntaje del jugador
        scores[nombre] = nuevo_puntaje

        with open("data/scores.json", "w") as file:
            json.dump(scores, file)

    except Exception as e:
        print(f"Error al actualizar puntajes: {str(e)}")

def create_matchup():
    """Crear emparejamientos de acuerdo a los puntajes registrados."""
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if len(scores) < 8:
            raise ValueError("Se necesitan al menos 8 jugadores para crear un emparejamiento.")

        # Organizar jugadores en función de sus puntajes
        players_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        sessions = []
        included_players = set()

        while len(players_sorted) >= 8:
            session = {
                "Alta de Gobierno": [],
                "Baja de Gobierno": [],
                "Alta de Oposición": [],
                "Baja de Oposición": []
            }

            # Seleccionar jugadores para la sesión
            high_players = players_sorted[:4]
            low_players = players_sorted[-4:]

            session["Alta de Gobierno"].extend([high_players[0], high_players[1]])
            session["Baja de Gobierno"].extend([low_players[0], low_players[1]])
            session["Alta de Oposición"].extend([high_players[2], high_players[3]])
            session["Baja de Oposición"].extend([low_players[2], low_players[3]])

            included_players.update([p[0] for p in high_players + low_players])
            sessions.append(session)

            # Eliminar los jugadores ya incluidos
            players_sorted = players_sorted[4:-4]

        # Asignar jueces
        judges = players_sorted[:4]
        for i, session in enumerate(sessions):
            judge = judges[i % len(judges)][0]
            session["Juez"] = judge
            included_players.add(judge)

        # Generar el texto para el emparejamiento
        matchup_text = f"🌟 **Emparejamiento Realizado con la Moción: **{mocion_global}** 🌟\n\n"

        for i, session in enumerate(sessions, start=1):
            matchup_text += f"✨ **Sesión {i}** ✨\n"
            for key, value in session.items():
                matchup_text += f"🗳️ **{key}:** {', '.join([p[0] for p in value])}\n"
            matchup_text += f"👨‍⚖️ **Juez:** {session['Juez']}\n\n"

        # Participantes no incluidos
        excluded_players = set(scores.keys()) - included_players
        if excluded_players:
            matchup_text += f"🚫 **Participantes No Incluidos:** {', '.join(excluded_players)}"

        return matchup_text

    except Exception as e:
        print(f"Error al crear el emparejamiento: {str(e)}")
        return "Ocurrió un error al intentar crear el emparejamiento."

@bot.command(name="emparejar")
async def emparejar(ctx):
    """Comando para crear emparejamientos y enviarlos al canal."""
    matchup_result = create_matchup()
    await ctx.send(matchup_result)

@bot.command(name="actualizar_puntaje")
async def actualizar_puntaje(ctx, nombre: str, nuevo_puntaje: int):
    """Comando para actualizar el puntaje de un jugador."""
    update_scores(nombre, nuevo_puntaje)
    await ctx.send(f"Puntaje de {nombre} actualizado a {nuevo_puntaje}")

@bot.command(name="ver_puntajes")
async def ver_puntajes(ctx):
    """Comando para ver los puntajes actuales de todos los jugadores."""
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if not scores:
            await ctx.send("No hay puntajes registrados.")
            return

        puntajes_lista = "\n".join([f"{nombre}: {punto}" for nombre, punto in scores.items()])
        await ctx.send(f"Puntajes actuales:\n{puntajes_lista}")

    except Exception as e:
        await ctx.send(f"Error al leer los puntajes: {str(e)}")

@bot.command(name="estadisticas")
async def estadisticas(ctx):
    """Comando para mostrar estadísticas de los jugadores."""
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if not scores:
            await ctx.send("No hay puntajes registrados.")
            return

        max_score = max(scores.values())
        top_players = [nombre for nombre, puntaje in scores.items() if puntaje == max_score]

        participaciones = {nombre: scores.get(nombre, 0) for nombre in scores.keys()}
        jugadores_con_mas_participaciones = sorted(participaciones.items(), key=lambda x: x[1], reverse=True)

        stats_message = f"🏆 Jugador(es) con mayor puntaje: {', '.join(top_players)} con {max_score} puntos.\n\n"
        stats_message += "👥 Jugadores con más participaciones:\n"
        stats_message += "\n".join([f"{nombre}: {parti}" for nombre, parti in jugadores_con_mas_participaciones])

        await ctx.send(stats_message)

    except Exception as e:
        await ctx.send(f"Error al obtener estadísticas: {str(e)}")

@bot.command(name="borrar_puntajes")
async def borrar_puntajes(ctx):
    """Comando para borrar todos los puntajes registrados."""
    try:
        with open("data/scores.json", "w") as file:
            json.dump({}, file)
        await ctx.send("Todos los puntajes han sido borrados.")
    except Exception as e:
        await ctx.send(f"Error al borrar los puntajes: {str(e)}")

@bot.command(name="ayuda")
async def ayuda(ctx):
    """Comando para mostrar la ayuda disponible."""
    help_message = (
        "🎉 ¡Bienvenido a la Sociedad de Debate de la Universidad del Rosario! 🎉\n\n"
        "🌟 ¡Estamos emocionados de tenerte aquí! 🌟\n"
        "Aquí tienes una lista de los comandos disponibles para ayudarte a disfrutar de nuestra comunidad:\n\n"
        "🤝 **`!emparejar`**: Crea emparejamientos para los debates.\n"
        "📈 **`!actualizar_puntaje <nombre> <nuevo_puntaje>`**: Actualiza el puntaje de un jugador.\n"
        "📊 **`!ver_puntajes`**: Muestra los puntajes actuales de todos los jugadores.\n"
        "📊 **`!estadisticas`**: Muestra estadísticas de los jugadores.\n"
        "🗑️ **`!borrar_puntajes`**: Elimina todos los puntajes registrados.\n"
        "❓ **`!ayuda`**: Muestra este mensaje de ayuda.\n\n"
        "✨ ¡Usa los comandos como se indica y disfruta del debate! 🗣️💬\n"
        "Si tienes alguna pregunta, no dudes en preguntar. ¡Estamos aquí para ayudarte! 🤗"
    )
    await ctx.send(help_message)

def run_bot():
    """Función para ejecutar el bot."""
    bot.run(TOKEN)

# Ejecutar el servidor y el bot
Thread(target=keep_alive).start()  # Inicia el servidor en un hilo separado
run_bot()  # Ejecuta el bot
