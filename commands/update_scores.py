import json

def update_scores(name, new_score):
    with open("data/scores.json", "r") as file:
        scores = json.load(file)

    scores[name] = new_score

    with open("data/scores.json", "w") as file:
        json.dump(scores, file)
