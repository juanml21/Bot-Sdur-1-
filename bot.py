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

@bot.command(name="modificar_mocion")
async def modificar_mocion(ctx, *, nueva_mocion: str):
    global mocion_global
    mocion_global = nueva_mocion
    await ctx.send(f"Moción modificada: **{mocion_global}**")

@bot.command(name="quitar_mocion")
async def quitar_mocion(ctx):
    global mocion_global
    mocion_global = ""
    await ctx.send("✅ La moción ha sido eliminada.")

def create_matchup():
    """Crear emparejamientos de acuerdo a los puntajes registrados."""
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if len(scores) < 8:
            raise ValueError("Se necesitan al menos 8 jugadores para crear un emparejamiento.")

        players_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        sessions = []
        included_players = set()

        while len(players_sorted) >= 8:
            session = {
                "Alta de Gobierno": [players_sorted[0], players_sorted[-2]],
                "Baja de Gobierno": [players_sorted[1], players_sorted[-1]],
                "Alta de Oposición": [players_sorted[2], players_sorted[-3]],
                "Baja de Oposición": [players_sorted[3], players_sorted[-4]]
            }

            included_players.update([p[0] for team in session.values() for p in team])
            sessions.append(session)
            players_sorted = players_sorted[4:-4]

        judges = [judge[0] for judge in players_sorted[:len(sessions)]]
        for i, session in enumerate(sessions):
            if judges:
                judge = judges.pop(0)
                session["Juez"] = judge
                included_players.add(judge)

        matchup_text = f"🌟 **Emparejamiento Realizado con la Moción: **{mocion_global}** 🌟\n\n"

        for i, session in enumerate(sessions, start=1):
            matchup_text += f"✨ **Sesión {i}** ✨\n"
            for key, value in session.items():
                if key != "Juez":
                    matchup_text += f"🗳️ **{key}:** {', '.join([p[0] for p in value])}\n"
            if "Juez" in session:
                matchup_text += f"👨‍⚖️ **Juez:** {session['Juez']}\n\n"

        excluded_players = set(scores.keys()) - included_players
        if excluded_players:
            matchup_text += f"🚫 **Participantes No Incluidos:** {', '.join(excluded_players)}"

        return matchup_text

    except Exception as e:
        print(f"Error al crear el emparejamiento: {str(e)}")
        return "Ocurrió un error al intentar crear el emparejamiento."

@bot.command(name="emparejar")
async def emparejar(ctx):
    matchup_result = create_matchup()
    await ctx.send(matchup_result)

@bot.command(name="actualizar_puntaje")
async def actualizar_puntaje(ctx, nombre: str, nuevo_puntaje: int):
    update_scores(nombre, nuevo_puntaje)
    await ctx.send(f"Puntaje de {nombre} actualizado a {nuevo_puntaje}")

@bot.command(name="ver_puntajes")
async def ver_puntajes(ctx):
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
    try:
        with open("data/scores.json", "w") as file:
            json.dump({}, file)
        await ctx.send("Todos los puntajes han sido borrados.")
    except Exception as e:
        await ctx.send(f"Error al borrar los puntajes: {str(e)}")

@bot.command(name="asignar_juez")
async def asignar_juez(ctx, sesion_numero: int, nombre_juez: str):
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if nombre_juez not in scores:
            await ctx.send(f"El juez {nombre_juez} no está registrado.")
            return

        existing_matchups = create_matchup()
        if isinstance(existing_matchups, str):
            await ctx.send(existing_matchups)
            return

        sessions = existing_matchups["sessions"]

        if 1 <= sesion_numero <= len(sessions):
            sessions[sesion_numero - 1]["Juez"] = nombre_juez
            await ctx.send(f"👨‍⚖️ Juez {nombre_juez} asignado a la **Sesión {sesion_numero}**.")
        else:
            await ctx.send("Número de sesión inválido.")

    except Exception as e:
        await ctx.send(f"Error al asignar juez: {str(e)}")

@bot.command(name="asignar_miembro")
async def asignar_miembro(ctx, sesion_numero: int, casa: str, nombre_completo: str):
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if nombre_completo not in scores:
            await ctx.send(f"El miembro {nombre_completo} no está registrado.")
            return

        existing_matchups = create_matchup()
        if isinstance(existing_matchups, str):
            await ctx.send(existing_matchups)
            return

        sessions = existing_matchups["sessions"]
        casas_validas = ["Alta de Gobierno", "Baja de Gobierno", "Alta de Oposición", "Baja de Oposición"]

        if 1 <= sesion_numero <= len(sessions) and casa in casas_validas:
            sessions[sesion_numero - 1][casa][0] = nombre_completo
            await ctx.send(f"👤 Miembro {nombre_completo} asignado a **{casa}** en la Sesión {sesion_numero}.")
        else:
            await ctx.send("Número de sesión o nombre de casa inválidos.")

    except Exception as e:
        await ctx.send(f"Error al asignar miembro: {str(e)}")

# Función para mantener vivo el servidor (si usas un archivo de keep_alive)
keep_alive()

bot.run(TOKEN)
