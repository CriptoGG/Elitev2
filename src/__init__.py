# Source code for the Sci-Fi City Builder
# Inspired by Elite 1984

# This file makes the 'src' directory a package and can be used
# to make the package executable.

if __name__ == "__main__":
    # This allows running the game using `python -m src`
    from .main import game_loop
    print("Launching Sci-Fi City Builder via src package...")
    game_loop()
