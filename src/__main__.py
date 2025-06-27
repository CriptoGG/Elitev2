# This file allows the src package to be run as a script
# using `python -m src`

if __name__ == "__main__":
    # Prefer relative import if __main__.py is considered part of the package
    # If this causes issues, `from src.main import game_loop` is an alternative
    # but `.main` should work when `src` is correctly identified as the package.
    try:
        from .main import game_loop
    except ImportError:
        # Fallback or error if the context is unexpected
        print("Error: Could not perform relative import of .main in src/__main__.py.")
        print("This might indicate an issue with how Python is interpreting the package structure.")
        # For robustness, could try absolute if the path is set up for it
        # from src.main import game_loop
        raise

    print("Launching Sci-Fi City Builder via src.__main__ ...")
    game_loop()
