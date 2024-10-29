import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
from threading import Thread
from webserver import keep_alive
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
REMINDER_CHANNEL_ID = 800086279643463731
mocion_global = ""

@bot.event
async def on_ready():
    print(f'{bot.user} ha conectado a Discord!')
    recordatorio_puntajes.start()

@tasks.loop(hours=24)
async def recordatorio_puntajes():
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if channel:
        await channel.send(
            "@everyone 🚨 ¡Atención! 🚨\n"
            "Es hora de poner sus puntajes al día. 📝✨\n"
            "Corran a actualizar sus puntajes y asegúrense de que todos tengan el reconocimiento que merecen! 🎉🙌"
        )
    else:
        print("No se pudo encontrar el canal para enviar recordatorios.")

def update_scores(nombre_completo, nuevo_puntaje):
    """Actualizar o agregar el puntaje del jugador en el archivo JSON."""
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)
        scores[nombre_completo] = nuevo_puntaje
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
    """Crear emparejamientos de acuerdo a los puntajes registrados y seleccionar jueces con los puntajes más altos."""
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

        # Seleccionar jueces con los puntajes más altos entre los jugadores restantes
        remaining_players = [p for p in players_sorted if p[0] not in included_players]
        judges = sorted(remaining_players, key=lambda x: x[1], reverse=True)[:len(sessions)]
        
        # Asignar un juez a cada sesión según los puntajes más altos restantes
        for i, session in enumerate(sessions):
            if judges:
                judge = judges.pop(0)
                session["Juez"] = judge[0]
                included_players.add(judge[0])

        # Construir el mensaje de emparejamiento
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
async def actualizar_puntaje(ctx, *args):
    nombre_completo = " ".join(args[:-1])
    try:
        nuevo_puntaje = int(args[-1])
        update_scores(nombre_completo, nuevo_puntaje)
        await ctx.send(f"Puntaje de {nombre_completo} actualizado a {nuevo_puntaje}")
    except ValueError:
        await ctx.send("Por favor, proporciona un puntaje válido.")

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

@bot.command(name="asignar_juez")
async def asignar_juez(ctx, sesion_numero: int, *nombre_juez):
    nombre_juez_completo = " ".join(nombre_juez)
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if nombre_juez_completo not in scores:
            await ctx.send(f"El juez {nombre_juez_completo} no está registrado.")
            return

        existing_matchups = create_matchup()
        if isinstance(existing_matchups, str):
            await ctx.send(existing_matchups)
            return

        sessions = existing_matchups["sessions"]

        if 1 <= sesion_numero <= len(sessions):
            sessions[sesion_numero - 1]["Juez"] = nombre_juez_completo
            await ctx.send(f"👨‍⚖️ Juez {nombre_juez_completo} asignado a la **Sesión {sesion_numero}**.")
        else:
            await ctx.send("Número de sesión inválido.")

    except Exception as e:
        await ctx.send(f"Error al asignar juez: {str(e)}")

@bot.command(name="asignar_miembro")
async def asignar_miembro(ctx, sesion_numero: int, casa: str, *nombre_miembro):
    nombre_miembro_completo = " ".join(nombre_miembro)
    try:
        with open("data/scores.json", "r") as file:
            scores = json.load(file)

        if nombre_miembro_completo not in scores:
            await ctx.send(f"El miembro {nombre_miembro_completo} no está registrado.")
            return

        existing_matchups = create_matchup()
        if isinstance(existing_matchups, str):
            await ctx.send(existing_matchups)
            return

        sessions = existing_matchups["sessions"]

        if 1 <= sesion_numero <= len(sessions) and casa in sessions[sesion_numero - 1]:
            sessions[sesion_numero - 1][casa].append(nombre_miembro_completo)
            await ctx.send(f"🏠 Miembro {nombre_miembro_completo} asignado a **{casa}** en la **Sesión {sesion_numero}**.")
        else:
            await ctx.send("Número de sesión o casa inválido.")

    except Exception as e:
        await ctx.send(f"Error al asignar miembro: {str(e)}")
@bot.command(name="borrar_puntajes")
async def borrar_puntajes(ctx, *nombre_completo):
    nombre = " ".join(nombre_completo)
    try:
        # Cargar los puntajes existentes
        with open("data/scores.json", "r") as file:
            scores = json.load(file)
        
        # Verificar si el nombre existe en los puntajes
        if nombre in scores:
            del scores[nombre]
            # Guardar los puntajes actualizados
            with open("data/scores.json", "w") as file:
                json.dump(scores, file)
            await ctx.send(f"✅ Puntaje de {nombre} ha sido eliminado.")
        else:
            await ctx.send(f"❌ El participante {nombre} no está registrado.")
    except Exception as e:
        await ctx.send(f"Error al borrar puntaje: {str(e)}")


@bot.command(name="ayuda")
async def ayuda(ctx):
    """Comando para mostrar la ayuda disponible."""
    help_message = (
        "🎉 ¡Bienvenido a la Sociedad de Debate de la Universidad del Rosario! 🎉\n\n"
        "🌟 ¡Estamos emocionados de tenerte aquí! 🌟\n"
        "Aquí tienes una lista de los comandos disponibles para ayudarte a disfrutar de nuestra comunidad:\n\n"
        "🤝 **!emparejar**: Crea emparejamientos para los debates.\n"
        "📈 **!actualizar_puntaje <nombre> <nuevo_puntaje>**: Actualiza el puntaje de un jugador.\n"
        "📊 **!ver_puntajes**: Muestra los puntajes actuales de todos los jugadores.\n"
        "📊 **!estadisticas**: Muestra estadísticas de los jugadores.\n"
        "🗑️ **!borrar_puntajes**: Elimina todos los puntajes registrados.\n"
        "✅ **!modificar_mocion <nueva_mocion>**: Modifica la moción actual.\n"
        "❌ **!quitar_mocion**: Elimina la moción actual.\n"
        "👨‍⚖️ **!asignar_juez <sesion_numero> <nombre_juez>**: Asigna un juez a una sesión específica.\n"
        "👤 **!asignar_miembro <sesion_numero> <casa> <nombre_completo>**: Asigna un miembro a una casa en una sesión específica.\n"
        "❓ **!ayuda**: Muestra este mensaje de ayuda.\n\n"
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
