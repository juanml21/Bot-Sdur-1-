import json

def create_matchup():
    # Cargar puntajes
    with open("data/scores.json", "r") as file:
        scores = json.load(file)

    # Asegurarse de tener al menos 8 jugadores
    if len(scores) < 8:
        raise ValueError("Se necesitan al menos 8 jugadores para crear un emparejamiento.")

    # Organizar jugadores en función de sus puntajes
    players_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Crear los equipos según el formato BP
    teams = {
        "Alta de Gobierno": [players_sorted[0], players_sorted[7]],
        "Baja de Gobierno": [players_sorted[1], players_sorted[6]],
        "Alta de Oposición": [players_sorted[2], players_sorted[5]],
        "Baja de Oposición": [players_sorted[3], players_sorted[4]],
    }

    # Organizar jueces con validación de la cantidad de jugadores
    judges = []
    if len(players_sorted) > 8:
        judges.append(players_sorted[8])  # Juez principal
    if len(players_sorted) > 9:
        judges.append(players_sorted[9])  # Panel adicional si está disponible
    
    # Generar el texto para el emparejamiento
    matchup_text = "\n".join(f"{key}: {', '.join([p[0] for p in value])}" for key, value in teams.items())
    judges_text = "Jueces: " + ", ".join([judge[0] for judge in judges])

    return f"{matchup_text}\n\n{judges_text}"
