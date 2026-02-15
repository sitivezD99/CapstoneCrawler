import sys
import os

# Add 'src' to the python path so imports work correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from main import Game

if __name__ == "__main__":
    game = Game()
    game.run()