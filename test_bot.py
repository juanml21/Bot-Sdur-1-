import unittest
import json  # Importa el módulo json
from commands.matchmaking import create_matchup
from commands.update_scores import update_scores

class TestBotFunctions(unittest.TestCase):
    
    def test_create_matchup(self):
        # Test de emparejamientos
        matchup = create_matchup()
        self.assertIn("Alta de Gobierno", matchup)
    
    def test_update_scores(self):
        # Test de actualización de puntajes
        update_scores("TestUser", 100)
        with open("data/scores.json", "r") as file:
            scores = json.load(file)
        self.assertEqual(scores["TestUser"], 100)

if __name__ == "__main__":
    unittest.main()
