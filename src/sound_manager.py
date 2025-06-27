# Manages sound effects and music for Sci-Fi City Builder

import pygame

class SoundManager:
    def __init__(self, config):
        self.config = config
        self.sounds = {}
        self.music_volume = 0.5  # Default volume (0.0 to 1.0)
        self.sfx_volume = 0.7    # Default SFX volume
        self.is_music_playing = False
        self.current_track = None

        try:
            pygame.mixer.init()
            print("Pygame mixer initialized successfully.")
        except pygame.error as e:
            print(f"Error initializing pygame.mixer: {e}. Sound will be disabled.")
            pygame.mixer.quit() # Ensure it's truly off if init failed partially

        self.load_default_sounds()
        # self.load_music(config.MUSIC_DIR + "ambient_theme.ogg") # Example

    def load_sound(self, name, filepath):
        if not pygame.mixer.get_init(): # Check if mixer is initialized
            return
        try:
            sound = pygame.mixer.Sound(filepath)
            sound.set_volume(self.sfx_volume)
            self.sounds[name] = sound
            print(f"Sound '{name}' loaded from {filepath}")
        except pygame.error as e:
            print(f"Error loading sound {name} from {filepath}: {e}")

    def play_sound(self, name):
        if not pygame.mixer.get_init():
            return
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error as e:
                 print(f"Error playing sound {name}: {e}")
        else:
            print(f"Sound effect '{name}' not found.")

    def load_default_sounds(self):
        # Placeholder paths - these files won't exist in the environment
        # but the code handles their absence.
        self.load_sound("ui_click", self.config.SOUND_DIR + "ui_click.wav")
        self.load_sound("building_place", self.config.SOUND_DIR + "building_placed.wav")
        self.load_sound("alert_info", self.config.SOUND_DIR + "alert_info.wav")
        self.load_sound("alert_warning", self.config.SOUND_DIR + "alert_warning.wav")
        self.load_sound("insufficient_credits", self.config.SOUND_DIR + "error_credits.wav")


    def load_music(self, filepath):
        if not pygame.mixer.get_init():
            return
        try:
            pygame.mixer.music.load(filepath)
            self.current_track = filepath
            print(f"Music loaded from {filepath}")
        except pygame.error as e:
            print(f"Error loading music from {filepath}: {e}")
            self.current_track = None

    def play_music(self, loops=-1): # Loop indefinitely by default
        if not pygame.mixer.get_init() or not self.current_track:
            return
        try:
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            self.is_music_playing = True
            print(f"Playing music: {self.current_track}")
        except pygame.error as e:
            print(f"Error playing music: {e}")
            self.is_music_playing = False

    def stop_music(self):
        if not pygame.mixer.get_init():
            return
        try:
            pygame.mixer.music.stop()
            self.is_music_playing = False
            print("Music stopped.")
        except pygame.error as e:
            print(f"Error stopping music: {e}")

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
        print(f"SFX Volume set to {self.sfx_volume}")

    def set_music_volume(self, volume):
        if not pygame.mixer.get_init():
            return
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
            print(f"Music Volume set to {self.music_volume}")
        except pygame.error as e:
            print(f"Error setting music volume: {e}")


print("SoundManager module loaded.")
