
"""
sound.py — Procedural audio system.
 
Generates all sounds and music using pygame's synthesizer —
no audio files required. Everything is built from sine waves and noise.
"""
 
import pygame
import numpy as np
import threading
 
 
SAMPLE_RATE = 44100
CHANNELS    = 2
 
 
def _make_tone(freq: float, duration: float, volume: float = 0.3,
               wave: str = "sine", fade_out: bool = True) -> object:
    """Generate a tone as a pygame Sound object."""
    frames = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, frames, endpoint=False)
 
    if wave == "sine":
        data = np.sin(2 * np.pi * freq * t)
    elif wave == "square":
        data = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "sawtooth":
        data = 2 * (t * freq - np.floor(t * freq + 0.5))
    else:
        data = np.sin(2 * np.pi * freq * t)
 
    if fade_out:
        fade = np.linspace(1.0, 0.0, frames)
        data = data * fade
 
    data = (data * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)
 
 
def _make_chord(freqs: list, duration: float, volume: float = 0.2,
                fade_out: bool = True) -> object:
    """Layer multiple tones into a chord."""
    frames = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, frames, endpoint=False)
    combined = np.zeros(frames)
    for freq in freqs:
        combined += np.sin(2 * np.pi * freq * t)
    combined /= len(freqs)
    if fade_out:
        combined *= np.linspace(1.0, 0.0, frames)
    data = (combined * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)
 
 
def _make_noise_burst(duration: float, volume: float = 0.1,
                      lowpass: float = 0.3) -> object:
    """Generate filtered noise for ambient texture."""
    frames = int(SAMPLE_RATE * duration)
    noise = np.random.uniform(-1, 1, frames)
    # Simple lowpass by averaging neighbours
    kernel = int(SAMPLE_RATE * lowpass / 1000)
    if kernel > 1:
        noise = np.convolve(noise, np.ones(kernel) / kernel, mode="same")
    noise *= np.linspace(1.0, 0.0, frames)
    data = (noise * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)
 
 
class SoundSystem:
    """
    Central sound manager. Call .init() once after pygame.init().
    """
 
    def __init__(self):
        self.enabled = False
        self._ambient_channel = None
        self._music_channel = None
        self._sfx_channels = []
 
        # Pre-built sound cache
        self._sounds: dict = {}
 
    def init(self) -> bool:
        """Initialise audio. Returns False if audio unavailable."""
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, CHANNELS, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self._ambient_channel = pygame.mixer.Channel(0)
            self._music_channel   = pygame.mixer.Channel(1)
            self._sfx_channels    = [pygame.mixer.Channel(i) for i in range(2, 8)]
            self._build_sounds()
            self.enabled = True
            return True
        except Exception as e:
            print(f"[Sound] Audio unavailable: {e}")
            return False
 
    def _build_sounds(self) -> None:
        """Pre-generate all game sounds."""
 
        # ── Ambient drones (looping) ──────────────────────────────────────────
        # Deep gothic organ drone — A minor chord, very slow
        self._sounds["ambient_explore"] = _make_chord(
            [55.0, 65.4, 82.4, 110.0],   # A1, C2, E2, A2
            duration=4.0, volume=0.12, fade_out=False
        )

        self._sounds["ambient_explore"] = _make_chord(
            [55.0, 65.4, 82.4, 110.0],
            duration=6.0, volume=0.04, fade_out=False
        )

        self._sounds["ambient_tense"] = _make_chord(
            [55.0, 69.3, 87.3],
            duration=6.0, volume=0.05, fade_out=False
        )
        # Read thoughts — eerie high sine sweep
        self._sounds["power_read"] = _make_tone(
            880.0, duration=0.6, volume=0.2, wave="sine"
        )
 
        # Intimidate — low growl (sawtooth burst)
        self._sounds["power_intimidate"] = _make_tone(
            80.0, duration=0.5, volume=0.35, wave="sawtooth"
        )
 
        # Enthrall — deep resonant chord
        self._sounds["power_enthrall"] = _make_chord(
            [110.0, 138.6, 164.8, 220.0],
            duration=1.2, volume=0.3
        )
 
        # ── Result sounds ─────────────────────────────────────────────────────
        # Success — bright ascending notes
        self._sounds["success"] = _make_chord(
            [523.3, 659.3, 783.9],       # C5, E5, G5
            duration=0.6, volume=0.28
        )
 
        # Partial — ambiguous chord
        self._sounds["partial"] = _make_chord(
            [440.0, 554.4, 622.3],       # A4, C#5, Eb5
            duration=0.5, volume=0.22
        )
 
        # Failure — descending minor
        self._sounds["fail"] = _make_chord(
            [220.0, 261.6, 311.1],       # A3, C4, Eb4
            duration=0.7, volume=0.28
        )
 
        # Critical fail — harsh dissonance
        self._sounds["critical_fail"] = _make_chord(
            [110.0, 116.5, 164.8],       # A2, Bb2, E3 — tritone cluster
            duration=1.0, volume=0.35
        )
 
        # ── UI / ambient SFX ──────────────────────────────────────────────────
        # Room transition — soft whoosh
        self._sounds["room_enter"] = _make_noise_burst(0.4, volume=0.12, lowpass=0.5)
 
        # Suspicion spike — rising alarm tone
        self._sounds["suspicion_spike"] = _make_tone(
            300.0, duration=0.4, volume=0.3, wave="square"
        )
 
        # Game over — descending doom
        self._sounds["game_over"] = _make_chord(
            [110.0, 130.8, 155.6, 185.0],  # A2, C3, Eb3, F#3 — diminished
            duration=3.0, volume=0.4
        )
 
        # Level up — triumphant fanfare
        self._sounds["level_up"] = _make_chord(
            [523.3, 659.3, 783.9, 1046.5],
            duration=1.0, volume=0.3
        )
 
        # NPC joins court
        self._sounds["court_join"] = _make_chord(
            [392.0, 493.9, 587.3],       # G4, B4, D5
            duration=0.8, volume=0.25
        )
 
    # ── Public interface ──────────────────────────────────────────────────────
 
    def play_ambient(self, key: str) -> None:
        if not self.enabled:
            return
        snd = self._sounds.get(key)
        if snd and self._ambient_channel:
            self._ambient_channel.play(snd, loops=-1, fade_ms=2000)
 
    def stop_ambient(self) -> None:
        if self._ambient_channel:
            self._ambient_channel.fadeout(1500)
 
    def play_sfx(self, key: str) -> None:
        if not self.enabled:
            return
        snd = self._sounds.get(key)
        if not snd:
            return
        # Find a free SFX channel
        for ch in self._sfx_channels:
            if not ch.get_busy():
                ch.play(snd)
                return
        # All busy — use the first one anyway
        self._sfx_channels[0].play(snd)
 
    def set_ambient_volume(self, vol: float) -> None:
        if self._ambient_channel:
            self._ambient_channel.set_volume(vol)
 
    def transition_ambient(self, new_key: str) -> None:
        """Crossfade to a different ambient track."""
        if not self.enabled:
            return
        self.stop_ambient()
        # Small delay then start new
        def _delayed():
            import time
            time.sleep(1.5)
            self.play_ambient(new_key)
        t = threading.Thread(target=_delayed, daemon=True)
        t.start()
