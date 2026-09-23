"""
Quantum Matrix — v2.0
Cross-platform number-cracking game (Windows + Android)
Kivy 2.x  |  Python 3.9+
"""

import random
import time
import json
import os
import sys

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.audio import SoundLoader

# ── Platform-aware window size ─────────────────────────────────────
if platform not in ('android', 'ios'):
    Window.size = (420, 780)

# ══════════════════════════════════════════════════════════════════
#  PALETTE  — Soft Dark / Easy on Eyes
#  Warm dark background, muted mid-tone accents, nothing above 78%
#  brightness. Inspired by VS Code dark+ / Linear dark.
# ══════════════════════════════════════════════════════════════════

# ── Backgrounds (warm dark, not cold black) ───────────────────────
C_BG      = (0.10, 0.10, 0.13, 1)   # warm charcoal — not harsh black
C_SURFACE = (0.14, 0.15, 0.20, 1)   # card surface
C_SURFACE2= (0.18, 0.19, 0.26, 1)   # elevated badge / button bg
C_BORDER  = (0.26, 0.28, 0.38, 1)   # subtle separator

# ── Soft accents (muted, mid-brightness — easy on eyes) ──────────
C_CYAN    = (0.40, 0.78, 0.90, 1)   # dusty sky blue — titles
C_GREEN   = (0.35, 0.78, 0.55, 1)   # sage green — Apprentice / WIN
C_ORANGE  = (0.88, 0.62, 0.30, 1)   # warm amber — Grandmaster
C_RED     = (0.85, 0.38, 0.40, 1)   # muted rose — Cyber Legend / LOSE
C_PURPLE  = (0.60, 0.48, 0.82, 1)   # soft lavender — primary CTA
C_PINK    = (0.80, 0.50, 0.72, 1)   # dusty rose — TAP TO START
C_YELLOW  = (0.85, 0.76, 0.38, 1)   # warm gold — scores / records
C_TEAL    = (0.32, 0.72, 0.68, 1)   # muted teal — range badges / cool hint

# ── Neutrals ─────────────────────────────────────────────────────
C_WHITE   = (0.88, 0.89, 0.92, 1)   # off-white — primary text
C_MUTED   = (0.50, 0.53, 0.62, 1)   # secondary / hint text
C_DARK    = (0.16, 0.17, 0.24, 1)   # back buttons / dark CTA

Window.clearcolor = C_BG

# ── Resource path (works in .py, PyInstaller .exe, and Android APK) ──
def _res(relative_path):
    """
    Resolve a path to a bundled resource.
    - PyInstaller one-file EXE: files are extracted to sys._MEIPASS at runtime
    - Android APK / plain .py:  relative to the directory of this file
    """
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


# ── Persistent Storage ────────────────────────────────────────────
def _store():
    """
    Return the save-file path.
    - Android: app's private user_data_dir  (writable, survives reinstall)
    - Windows / desktop: same folder as python.py
    """
    app = App.get_running_app()
    if app and platform == 'android':
        return os.path.join(app.user_data_dir, "qm_save.json")
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "qm_save.json")


def load_state():
    path = _store()
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(data: dict):
    try:
        with open(_store(), "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ── Global Game State ─────────────────────────────────────────────
class GS:
    high_scores  = {"Apprentice": None, "Grandmaster": None, "Cyber Legend": None}
    streak       = 0
    total_wins   = 0
    total_score  = 0
    sfx_on       = True
    music_on     = True
    history      = []          # list of dict records for leaderboard
    _bg_music    = None

    @classmethod
    def load(cls):
        d = load_state()
        cls.high_scores  = d.get("high_scores",  cls.high_scores)
        cls.streak       = d.get("streak",        0)
        cls.total_wins   = d.get("total_wins",    0)
        cls.total_score  = d.get("total_score",   0)
        cls.sfx_on       = d.get("sfx_on",        True)
        cls.music_on     = d.get("music_on",      True)
        cls.history      = d.get("history",       [])

    @classmethod
    def save(cls):
        save_state({
            "high_scores": cls.high_scores,
            "streak":      cls.streak,
            "total_wins":  cls.total_wins,
            "total_score": cls.total_score,
            "sfx_on":      cls.sfx_on,
            "music_on":    cls.music_on,
            "history":     cls.history[-50:],   # keep last 50 runs
        })

    @classmethod
    def play_sfx(cls, name):
        """Play a bundled sound by logical name (no crash if missing)."""
        if not cls.sfx_on:
            return
        paths = {
            "win":   _res("assets/win.wav"),
            "lose":  _res("assets/lose.wav"),
            "tick":  _res("assets/tick.wav"),
            "hint":  _res("assets/hint.wav"),
            "wrong": _res("assets/wrong.wav"),
        }
        path = paths.get(name, "")
        if path and os.path.exists(path):
            s = SoundLoader.load(path)
            if s:
                s.play()


# ── Helpers ───────────────────────────────────────────────────────
class Card(BoxLayout):
    def __init__(self, bg=None, radius=14, **kw):
        super().__init__(**kw)
        self._bg = bg if bg else list(C_SURFACE)
        self._r  = radius
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._r])


class NeonBtn(Button):
    def __init__(self, accent=None, **kw):
        kw.setdefault('background_normal', '')
        kw.setdefault('background_color', (0, 0, 0, 0))
        kw.setdefault('color', C_WHITE)
        kw.setdefault('bold', True)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(50))
        super().__init__(**kw)
        self._accent = accent if accent else list(C_PURPLE)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._accent)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

    def on_press(self):
        orig = self.height
        a = Animation(height=orig - dp(5), duration=0.06)
        a += Animation(height=orig,        duration=0.06)
        a.start(self)


class Sep(Widget):
    def __init__(self, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(1))
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*C_BORDER)
            Rectangle(pos=self.pos, size=self.size)


class TogBtn(ToggleButton):
    """Styled toggle button for settings."""
    def __init__(self, accent_on=None, **kw):
        kw.setdefault('background_normal', '')
        kw.setdefault('background_color', (0, 0, 0, 0))
        kw.setdefault('color', C_WHITE)
        kw.setdefault('bold', True)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(40))
        super().__init__(**kw)
        self._on_col  = accent_on if accent_on else list(C_GREEN)
        self._off_col = list(C_DARK)
        self.bind(pos=self._draw, size=self._draw, state=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            col = self._on_col if self.state == 'down' else self._off_col
            Color(*col)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])


# ══════════════════════════════════════════════════════════════════
#  PARTICLE BACKGROUND  (lightweight, mobile-safe)
# ══════════════════════════════════════════════════════════════════
class ParticleBG(Widget):
    """Drifting star-field drawn on canvas — 30 particles, no GPU extras."""
    _N = 30

    def __init__(self, **kw):
        super().__init__(**kw)
        self._pts = [self._new_pt() for _ in range(self._N)]
        self._ev  = Clock.schedule_interval(self._tick, 1 / 30)
        self.bind(size=self._redraw, pos=self._redraw)

    def _new_pt(self):
        return {
            "x": random.random(),
            "y": random.random(),
            "r": random.uniform(0.8, 2.2),
            "vx": random.uniform(-0.00015, 0.00015),
            "vy": random.uniform(-0.00010, 0.00010),
            "a": random.uniform(0.2, 0.6),
        }

    def _tick(self, dt):
        for p in self._pts:
            p["x"] = (p["x"] + p["vx"]) % 1.0
            p["y"] = (p["y"] + p["vy"]) % 1.0
        self._redraw()

    def _redraw(self, *_):
        self.canvas.before.clear()
        w, h = self.size
        # soft, muted star colours — easy on eyes
        star_cols = [
            (0.40, 0.78, 0.90),   # dusty blue
            (0.60, 0.48, 0.82),   # soft lavender
            (0.32, 0.72, 0.68),   # muted teal
            (0.85, 0.76, 0.38),   # warm gold
        ]
        with self.canvas.before:
            for i, p in enumerate(self._pts):
                r, g, b = star_cols[i % len(star_cols)]
                Color(r, g, b, p["a"])
                r2 = dp(p["r"])
                Ellipse(
                    pos=(self.x + p["x"] * w - r2,
                         self.y + p["y"] * h - r2),
                    size=(r2 * 2, r2 * 2),
                )

    def on_parent(self, widget, parent):
        if parent is None and self._ev:
            self._ev.cancel()


# ══════════════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ══════════════════════════════════════════════════════════════════
class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        fl = FloatLayout()
        fl.add_widget(ParticleBG(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}))

        box = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20),
                        size_hint=(1, 1))
        box.add_widget(Widget())

        self.title_lbl = Label(
            text="◈ QUANTUM\nMATRIX ◈",
            font_size=sp(40), bold=True, color=C_CYAN,
            halign='center', valign='middle', opacity=0,
        )
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        box.add_widget(self.title_lbl)

        self.sub_lbl = Label(
            text="— The Ultimate Number Cracking Challenge —",
            font_size=sp(12), color=C_MUTED,
            halign='center', opacity=0,
        )
        box.add_widget(self.sub_lbl)

        box.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.version_lbl = Label(
            text="v 2.0", font_size=sp(10), color=C_BORDER,
            halign='center', opacity=0,
        )
        box.add_widget(self.version_lbl)

        box.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.tap_lbl = Label(
            text="[ TAP ANYWHERE TO START ]",
            font_size=sp(14), bold=True, color=C_PINK,
            halign='center', opacity=0,
        )
        box.add_widget(self.tap_lbl)
        box.add_widget(Widget())

        fl.add_widget(box)
        self.add_widget(fl)
        self.bind(on_touch_down=self._go)

        # Android back button
        Window.bind(on_keyboard=self._on_kb)

    def on_enter(self):
        Animation(opacity=1, duration=1.0).start(self.title_lbl)
        Clock.schedule_once(
            lambda *_: Animation(opacity=1, duration=0.8).start(self.sub_lbl), 0.8)
        Clock.schedule_once(
            lambda *_: Animation(opacity=1, duration=0.6).start(self.version_lbl), 1.2)
        Clock.schedule_once(
            lambda *_: Animation(opacity=1, duration=0.6).start(self.tap_lbl), 1.5)
        Clock.schedule_once(self._pulse, 2.2)

    def _pulse(self, *_):
        if self.manager and self.manager.current == 'splash':
            a = Animation(opacity=0.3, duration=0.7) + Animation(opacity=1, duration=0.7)
            a.bind(on_complete=self._pulse)
            a.start(self.tap_lbl)

    def _go(self, *_):
        if self.manager:
            self.manager.transition = FadeTransition(duration=0.5)
            self.manager.current = 'levels'

    def _on_kb(self, window, key, *args):
        return False   # don't consume — fall through


# ══════════════════════════════════════════════════════════════════
#  LEVEL SELECT SCREEN
# ══════════════════════════════════════════════════════════════════
class LevelScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()
        Window.bind(on_keyboard=self._on_kb)

    def _build(self):
        fl = FloatLayout()
        fl.add_widget(ParticleBG(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}))

        root = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10),
                         size_hint=(1, 1))
        root.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # ── Header
        hdr = Card(orientation='vertical', padding=dp(14), spacing=dp(4),
                   size_hint_y=None, height=dp(88))

        title_row = BoxLayout(size_hint_y=None, height=dp(32))
        title_row.add_widget(Label(
            text="◈ QUANTUM MATRIX", font_size=sp(18),
            bold=True, color=C_CYAN, halign='left'))
        settings_btn = NeonBtn(
            text="✦", accent=list(C_DARK),
            size_hint_x=None, width=dp(40), height=dp(32), font_size=sp(16))
        settings_btn.bind(on_press=self._open_settings)
        title_row.add_widget(settings_btn)
        hdr.add_widget(title_row)

        self.stats_lbl = Label(
            text="", font_size=sp(11), color=C_YELLOW, halign='center',
            size_hint_y=None, height=dp(20))
        hdr.add_widget(self.stats_lbl)

        self.rank_lbl = Label(
            text="", font_size=sp(10), color=C_MUTED, halign='center',
            size_hint_y=None, height=dp(18))
        hdr.add_widget(self.rank_lbl)

        root.add_widget(hdr)
        root.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # ── Difficulty cards
        modes = [
            ("APPRENTICE",   "Range  1 – 50",  "6 lives  ·  Easy",   C_GREEN,  "Apprentice"),
            ("GRANDMASTER",  "Range  1 – 100", "5 lives  ·  Medium", C_ORANGE, "Grandmaster"),
            ("CYBER LEGEND", "Range  1 – 200", "4 lives  ·  Hard",   C_RED,    "Cyber Legend"),
        ]
        for title, rng_txt, sub_txt, color, key in modes:
            card = Card(orientation='vertical', padding=(dp(14), dp(10)),
                        spacing=dp(6), size_hint_y=None, height=dp(116))

            card.add_widget(Label(
                text=title, font_size=sp(15), bold=True,
                color=color, halign='left', valign='middle',
                size_hint_y=None, height=dp(28)))

            range_card = Card(bg=list(C_SURFACE2), radius=8,
                              size_hint_y=None, height=dp(26),
                              padding=(dp(8), dp(2)))
            range_card.add_widget(Label(
                text=rng_txt, font_size=sp(12),
                bold=True, color=C_TEAL, halign='center'))
            card.add_widget(range_card)

            info_row = BoxLayout(size_hint_y=None, height=dp(18))
            info_row.add_widget(Label(
                text=sub_txt, font_size=sp(10), color=C_MUTED, halign='left'))
            hs = GS.high_scores.get(key)
            hs_lbl = Label(
                text=f"★ Best: {hs} tries" if hs else "No record yet",
                font_size=sp(10), color=C_YELLOW, halign='right')
            info_row.add_widget(hs_lbl)
            card.add_widget(info_row)

            btn = NeonBtn(text="PLAY  »", accent=list(color),
                          size_hint_y=None, height=dp(32), font_size=sp(12))
            btn.mode_key = key
            btn.bind(on_press=self._select)
            card.add_widget(btn)
            root.add_widget(card)

        root.add_widget(Sep())

        # ── Bottom bar
        bot = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        lb_btn = NeonBtn(text="★  Leaderboard", accent=list(C_SURFACE2),
                         height=dp(36), font_size=sp(11))
        lb_btn.bind(on_press=self._open_leaderboard)
        bot.add_widget(lb_btn)
        root.add_widget(bot)

        root.add_widget(Label(
            text="◆ Guess smart  ·  Hints  ·  Streaks  ·  Points ◆",
            font_size=sp(10), color=C_MUTED, halign='center',
            size_hint_y=None, height=dp(24)))
        root.add_widget(Widget())

        fl.add_widget(root)
        self.add_widget(fl)

    def on_pre_enter(self):
        s, w, sc = GS.streak, GS.total_wins, GS.total_score
        parts = []
        if s > 0:  parts.append(f"🔥 Streak {s}")
        if w > 0:  parts.append(f"🏆 Wins {w}")
        if sc > 0: parts.append(f"⭐ Score {sc}")
        self.stats_lbl.text = "   ".join(parts) if parts else "Ready to play!"
        self.rank_lbl.text  = self._rank_text(sc)

    @staticmethod
    def _rank_text(score):
        if score == 0:     return "[ RANK ]  Rookie"
        elif score < 500:  return "[ RANK ]  Initiate"
        elif score < 1500: return "[ RANK ]  Hacker"
        elif score < 3000: return "[ RANK ]  Architect"
        elif score < 6000: return "[ RANK ]  Ghost"
        else:              return "[ RANK ]  ◈ Quantum God ◈"

    def _select(self, btn):
        gs = self.manager.get_screen('game')
        gs.start_game(btn.mode_key)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'game'

    def _open_settings(self, *_):
        self.manager.transition = SlideTransition(direction='up')
        self.manager.current = 'settings'

    def _open_leaderboard(self, *_):
        self.manager.get_screen('leaderboard').refresh()
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'leaderboard'

    def _on_kb(self, window, key, *args):
        if key == 27 and self.manager and self.manager.current == 'levels':
            App.get_running_app().stop()
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  SETTINGS SCREEN
# ══════════════════════════════════════════════════════════════════
class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()
        Window.bind(on_keyboard=self._on_kb)

    def _build(self):
        root = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        root.add_widget(Widget(size_hint_y=None, height=dp(10)))
        root.add_widget(Label(
            text="✦  SETTINGS", font_size=sp(22), bold=True,
            color=C_CYAN, halign='center', size_hint_y=None, height=dp(40)))
        root.add_widget(Sep())

        # SFX toggle
        sfx_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        sfx_row.add_widget(Label(
            text="Sound Effects", font_size=sp(14), color=C_WHITE, halign='left'))
        self.sfx_btn = TogBtn(
            text="ON" if GS.sfx_on else "OFF",
            state='down' if GS.sfx_on else 'normal',
            accent_on=list(C_GREEN),
            size_hint_x=None, width=dp(80))
        self.sfx_btn.bind(state=self._toggle_sfx)
        sfx_row.add_widget(self.sfx_btn)
        root.add_widget(sfx_row)

        # Music toggle (placeholder — wire to background music asset)
        music_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        music_row.add_widget(Label(
            text="Background Music", font_size=sp(14), color=C_WHITE, halign='left'))
        self.music_btn = TogBtn(
            text="ON" if GS.music_on else "OFF",
            state='down' if GS.music_on else 'normal',
            accent_on=list(C_GREEN),
            size_hint_x=None, width=dp(80))
        self.music_btn.bind(state=self._toggle_music)
        music_row.add_widget(self.music_btn)
        root.add_widget(music_row)

        root.add_widget(Sep())

        # Reset scores
        reset_btn = NeonBtn(
            text="✕  Reset All Progress",
            accent=[0.55, 0.10, 0.10, 1], height=dp(44), font_size=sp(13))
        reset_btn.bind(on_press=self._confirm_reset)
        root.add_widget(reset_btn)

        root.add_widget(Widget())

        back_btn = NeonBtn(
            text="«  Back", accent=list(C_DARK), height=dp(44), font_size=sp(13))
        back_btn.bind(on_press=self._back)
        root.add_widget(back_btn)

        self.add_widget(root)

    def _toggle_sfx(self, btn, state):
        GS.sfx_on = (state == 'down')
        btn.text  = "ON" if GS.sfx_on else "OFF"
        GS.save()

    def _toggle_music(self, btn, state):
        GS.music_on = (state == 'down')
        btn.text    = "ON" if GS.music_on else "OFF"
        GS.save()

    def _confirm_reset(self, *_):
        box = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        box.add_widget(Label(
            text="Reset ALL scores, wins, and history?\nThis cannot be undone.",
            halign='center', color=C_WHITE, font_size=sp(13)))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        yes = NeonBtn(text="YES — Reset", accent=[0.65, 0.10, 0.10, 1],
                      height=dp(44), font_size=sp(12))
        no  = NeonBtn(text="Cancel", accent=list(C_DARK),
                      height=dp(44), font_size=sp(12))
        row.add_widget(yes); row.add_widget(no)
        box.add_widget(row)
        popup = Popup(title="Confirm Reset",
                      title_color=C_RED, separator_color=C_RED,
                      content=box,
                      size_hint=(0.82, 0.38),
                      background_color=(0.08, 0.09, 0.14, 0.97))
        yes.bind(on_press=lambda *_: (self._do_reset(), popup.dismiss()))
        no.bind( on_press=lambda *_: popup.dismiss())
        popup.open()

    def _do_reset(self):
        GS.high_scores  = {"Apprentice": None, "Grandmaster": None, "Cyber Legend": None}
        GS.streak       = 0
        GS.total_wins   = 0
        GS.total_score  = 0
        GS.history      = []
        GS.save()

    def _back(self, *_):
        self.manager.transition = SlideTransition(direction='down')
        self.manager.current = 'levels'

    def _on_kb(self, window, key, *args):
        if key == 27 and self.manager and self.manager.current == 'settings':
            self._back()
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  LEADERBOARD SCREEN
# ══════════════════════════════════════════════════════════════════
class LeaderboardScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()
        Window.bind(on_keyboard=self._on_kb)

    def _build(self):
        # Outer layout — header + bests are fixed height, scroll fills middle,
        # back button is always pinned at the bottom.
        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))

        # ── Fixed top section
        root.add_widget(Widget(size_hint_y=None, height=dp(8)))
        root.add_widget(Label(
            text="★  LEADERBOARD",
            font_size=sp(20), bold=True, color=C_YELLOW,
            halign='center', size_hint_y=None, height=dp(36)))
        root.add_widget(Sep())

        # Best-per-mode summary (fixed height)
        self.bests_card = Card(
            orientation='vertical', padding=dp(12), spacing=dp(4),
            size_hint_y=None, height=dp(90))
        root.add_widget(self.bests_card)
        root.add_widget(Sep())

        root.add_widget(Label(
            text="— Recent Runs —", font_size=sp(11), color=C_MUTED,
            halign='center', size_hint_y=None, height=dp(20)))

        # ── Scrollable history — takes all remaining space
        self.hist_box = BoxLayout(
            orientation='vertical', spacing=dp(4), size_hint_y=None)
        self.hist_box.bind(minimum_height=self.hist_box.setter('height'))
        sv = ScrollView(size_hint_y=1)   # flex — fills whatever is left
        sv.add_widget(self.hist_box)
        root.add_widget(sv)

        # ── Back button — always visible, pinned below the scroll
        root.add_widget(Sep())
        back_btn = NeonBtn(
            text="«  Back", accent=list(C_DARK),
            size_hint_y=None, height=dp(48), font_size=sp(13))
        back_btn.bind(on_press=self._back)
        root.add_widget(back_btn)
        root.add_widget(Widget(size_hint_y=None, height=dp(6)))

        self.add_widget(root)

    def refresh(self):
        # Best scores per mode
        self.bests_card.clear_widgets()
        mode_colors = {
            "Apprentice":   C_GREEN,
            "Grandmaster":  C_ORANGE,
            "Cyber Legend": C_RED,
        }
        for mode, color in mode_colors.items():
            hs = GS.high_scores.get(mode)
            val = f"{hs} tries" if hs else "—"
            row = BoxLayout(size_hint_y=None, height=dp(22))
            row.add_widget(Label(text=mode, font_size=sp(11), color=color, halign='left'))
            row.add_widget(Label(text=f"Best: {val}", font_size=sp(11),
                                 color=C_YELLOW, halign='right'))
            self.bests_card.add_widget(row)

        # History list
        self.hist_box.clear_widgets()
        records = list(reversed(GS.history[-30:]))
        if not records:
            self.hist_box.add_widget(Label(
                text="No games played yet.", font_size=sp(12), color=C_MUTED,
                size_hint_y=None, height=dp(32), halign='center'))
            return

        # Column header
        hdr = BoxLayout(size_hint_y=None, height=dp(20))
        for t, a in [("Mode", 'left'), ("Result", 'center'),
                     ("Tries", 'center'), ("Score", 'right')]:
            hdr.add_widget(Label(text=t, font_size=sp(9), color=C_BORDER,
                                 halign=a, bold=True))
        self.hist_box.add_widget(hdr)

        for r in records:
            won    = r.get("won", False)
            mode   = r.get("mode", "?")
            tries  = r.get("tries", "?")
            score  = r.get("score", 0)
            result = "✅ WIN" if won else "❌ LOSE"
            color  = C_GREEN if won else C_RED
            row = BoxLayout(size_hint_y=None, height=dp(22))
            row.add_widget(Label(text=mode,   font_size=sp(10), color=C_MUTED,   halign='left'))
            row.add_widget(Label(text=result, font_size=sp(10), color=color,     halign='center'))
            row.add_widget(Label(text=str(tries), font_size=sp(10), color=C_CYAN, halign='center'))
            row.add_widget(Label(text=f"+{score}", font_size=sp(10),
                                 color=C_YELLOW, halign='right'))
            self.hist_box.add_widget(row)

    def _back(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'levels'

    def _on_kb(self, window, key, *args):
        if key == 27 and self.manager and self.manager.current == 'leaderboard':
            self._back()
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  RESULT SCREEN
# ══════════════════════════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._mode = "Apprentice"
        self._build()
        Window.bind(on_keyboard=self._on_kb)

    def _build(self):
        fl = FloatLayout()
        fl.add_widget(ParticleBG(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}))

        self.root_box = BoxLayout(
            orientation='vertical', padding=dp(24), spacing=dp(12),
            size_hint=(1, 1))

        self.emoji_lbl = Label(
            text="", font_size=sp(52), halign='center',
            size_hint_y=None, height=dp(68))
        self.title_lbl = Label(
            text="", font_size=sp(22), bold=True,
            halign='center', size_hint_y=None, height=dp(38))
        self.subtitle_lbl = Label(
            text="", font_size=sp(12), color=C_MUTED,
            halign='center', size_hint_y=None, height=dp(28))

        self.root_box.add_widget(Widget(size_hint_y=None, height=dp(16)))
        self.root_box.add_widget(self.emoji_lbl)
        self.root_box.add_widget(self.title_lbl)
        self.root_box.add_widget(self.subtitle_lbl)
        self.root_box.add_widget(Sep())

        # Stats card
        self.stats_card = Card(
            orientation='vertical', padding=dp(14), spacing=dp(6),
            size_hint_y=None, height=dp(150))
        self.stat_answer = Label(text="", font_size=sp(13), color=C_WHITE,  halign='center')
        self.stat_tries  = Label(text="", font_size=sp(12), color=C_CYAN,   halign='center')
        self.stat_time   = Label(text="", font_size=sp(12), color=C_CYAN,   halign='center')
        self.stat_score  = Label(text="", font_size=sp(15), bold=True,
                                 color=C_YELLOW, halign='center')
        self.stat_rating = Label(text="", font_size=sp(12), color=C_MUTED,  halign='center')
        for w in [self.stat_answer, self.stat_tries, self.stat_time,
                  self.stat_score, self.stat_rating]:
            self.stats_card.add_widget(w)
        self.root_box.add_widget(self.stats_card)

        self.record_lbl = Label(
            text="", font_size=sp(12), bold=True, color=C_YELLOW,
            halign='center', size_hint_y=None, height=dp(26))
        self.root_box.add_widget(self.record_lbl)

        self.play_again_btn = NeonBtn(
            text="»  PLAY AGAIN", accent=list(C_PURPLE),
            height=dp(50), font_size=sp(14))
        self.menu_btn = NeonBtn(
            text="«  MAIN MENU", accent=list(C_DARK),
            height=dp(40), font_size=sp(12))
        self.play_again_btn.bind(on_press=self._play_again)
        self.menu_btn.bind(on_press=self._menu)
        self.root_box.add_widget(self.play_again_btn)
        self.root_box.add_widget(self.menu_btn)
        self.root_box.add_widget(Widget())

        fl.add_widget(self.root_box)
        self.add_widget(fl)

    def load(self, won, mode, secret, tries, elapsed, score):
        self._mode = mode
        if won:
            self.emoji_lbl.text   = "🎉"
            self.title_lbl.text   = "ACCESS GRANTED!"
            self.title_lbl.color  = C_GREEN
            self.subtitle_lbl.text = random.choice([
                "Outstanding! You cracked the code.",
                "Brilliant! The matrix bows to you.",
                "Flawless execution, agent!",
                "You are the Quantum Master!",
                "The firewall couldn't stop you!",
            ])
            max_lives = {"Apprentice": 6, "Grandmaster": 5, "Cyber Legend": 4}[mode]
            perf = (max_lives - tries + 1) / max_lives
            if   perf >= 0.85: rating = "◆◆◆  PERFECT"
            elif perf >= 0.60: rating = "◆◆    GREAT"
            elif perf >= 0.35: rating = "◆      GOOD"
            else:              rating = "▲      COMPLETED"
            GS.play_sfx("win")
        else:
            self.emoji_lbl.text   = "💥"
            self.title_lbl.text   = "CORE CRASHED!"
            self.title_lbl.color  = C_RED
            self.subtitle_lbl.text = random.choice([
                "The matrix was too strong this time.",
                "Don't give up — legends never quit!",
                "So close! Try again, agent.",
                "Every failure is a lesson. Rise again!",
            ])
            rating = "✕  GAME OVER"
            GS.play_sfx("lose")

        self.stat_answer.text  = f"Secret number  ›  {secret}"
        self.stat_tries.text   = f"◆  Guesses used  ·  {tries}"
        self.stat_time.text    = f"◆  Time taken    ·  {elapsed}s"
        self.stat_score.text   = f"★  Points earned  +{score}"
        self.stat_rating.text  = rating

        hs = GS.high_scores.get(mode)
        if won and (hs is None or tries < hs):
            self.record_lbl.text = "[ NEW PERSONAL RECORD ]"
        elif won and tries == hs:
            self.record_lbl.text = "[ MATCHED YOUR BEST ]"
        else:
            self.record_lbl.text = f"Personal best  ·  {hs} tries" if hs else ""

        Animation(opacity=0, duration=0).start(self.emoji_lbl)
        Clock.schedule_once(
            lambda *_: Animation(opacity=1, duration=0.45).start(self.emoji_lbl), 0.1)

    def _play_again(self, *_):
        gs = self.manager.get_screen('game')
        gs.start_game(self._mode)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'game'

    def _menu(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'levels'

    def _on_kb(self, window, key, *args):
        if key == 27 and self.manager and self.manager.current == 'result':
            self._menu()
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  GAME SCREEN
# ══════════════════════════════════════════════════════════════════
class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.game_active  = False
        self._timer_ev    = None
        self.current_mode = "Apprentice"
        self.modes_config = {
            "Apprentice":   {"range": (1,  50), "lives": 6, "pts": 100},
            "Grandmaster":  {"range": (1, 100), "lives": 5, "pts": 200},
            "Cyber Legend": {"range": (1, 200), "lives": 4, "pts": 350},
        }
        self._build()
        Window.bind(on_keyboard=self._on_kb)

    def _build(self):
        root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(7))

        # ── Top bar
        top = BoxLayout(size_hint_y=None, height=dp(36))
        self.mode_lbl  = Label(text="", font_size=sp(12), bold=True,
                               color=C_CYAN, halign='left')
        self.timer_lbl = Label(text="⏱ 0s", font_size=sp(12),
                               color=C_MUTED, halign='right')
        top.add_widget(self.mode_lbl)
        top.add_widget(self.timer_lbl)
        root.add_widget(top)

        # ── Lives + streak
        lr = BoxLayout(size_hint_y=None, height=dp(28))
        self.lives_lbl  = Label(text="", font_size=sp(11), bold=True,
                                color=C_GREEN, halign='left')
        self.streak_lbl = Label(text="", font_size=sp(11),
                                color=C_YELLOW, halign='right')
        lr.add_widget(self.lives_lbl)
        lr.add_widget(self.streak_lbl)
        root.add_widget(lr)

        # ── Score multiplier bar
        score_row = BoxLayout(size_hint_y=None, height=dp(22))
        self.score_lbl = Label(text="", font_size=sp(11), color=C_YELLOW, halign='left')
        self.multi_lbl = Label(text="", font_size=sp(11), color=C_PURPLE, halign='right')
        score_row.add_widget(self.score_lbl)
        score_row.add_widget(self.multi_lbl)
        root.add_widget(score_row)

        # ── HUD
        hud = Card(padding=dp(12), orientation='vertical',
                   size_hint_y=None, height=dp(96))
        self.hud_lbl = Label(text="", font_size=sp(14), color=C_WHITE,
                              halign='center', valign='middle')
        self.hud_lbl.bind(size=self.hud_lbl.setter('text_size'))
        hud.add_widget(self.hud_lbl)
        root.add_widget(hud)

        # ── Proximity hint
        self.hint_lbl = Label(text="", font_size=sp(12), color=C_MUTED,
                              size_hint_y=None, height=dp(24), halign='center')
        root.add_widget(self.hint_lbl)

        # ── Range reminder
        self.range_lbl = Label(text="", font_size=sp(10), color=C_MUTED,
                               size_hint_y=None, height=dp(18), halign='center')
        root.add_widget(self.range_lbl)

        # ── Input row
        ir = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        self.entry = TextInput(
            font_size=sp(24), multiline=False, input_filter='int',
            halign='center', background_color=(0.14, 0.15, 0.20, 1),
            foreground_color=C_WHITE, cursor_color=C_CYAN,
            hint_text="Enter number…", hint_text_color=C_MUTED,
            size_hint_x=0.72)
        self.entry.bind(on_text_validate=self.process_guess)
        lucky = NeonBtn(text="?", accent=list(C_SURFACE2),
                        size_hint_x=0.28, height=dp(54), font_size=sp(22), bold=True)
        lucky.bind(on_press=self._lucky)
        ir.add_widget(self.entry)
        ir.add_widget(lucky)
        root.add_widget(ir)

        # ── Hint button
        self.hint_btn = NeonBtn(
            text="◆  Reveal Hint  ( −10 pts )",
            accent=list(C_SURFACE2),
            height=dp(34), font_size=sp(11))
        self.hint_btn.bind(on_press=self._give_hint)
        root.add_widget(self.hint_btn)

        # ── Submit
        self.submit_btn = NeonBtn(
            text="SUBMIT  »", accent=list(C_PURPLE),
            height=dp(50), font_size=sp(15), bold=True)
        self.submit_btn.bind(on_press=self.process_guess)
        root.add_widget(self.submit_btn)

        # ── Guess log
        root.add_widget(Sep())
        root.add_widget(Label(
            text="— Guess Log —", font_size=sp(9), color=C_MUTED,
            size_hint_y=None, height=dp(16), halign='center'))
        self.hist_box = BoxLayout(
            orientation='vertical', spacing=dp(2), size_hint_y=None)
        self.hist_box.bind(minimum_height=self.hist_box.setter('height'))
        sv = ScrollView(size_hint_y=0.15)
        sv.add_widget(self.hist_box)
        root.add_widget(sv)

        # ── Back
        root.add_widget(Sep())
        back = NeonBtn(text="«  Menu", accent=list(C_DARK),
                       height=dp(34), font_size=sp(11))
        back.bind(on_press=self._back)
        root.add_widget(back)

        self.add_widget(root)

    def on_enter(self):
        Clock.schedule_once(lambda *_: setattr(self.entry, 'focus', True), 0.3)

    def _tick(self, dt):
        self.elapsed = int(time.time() - self._t0)
        self.timer_lbl.text = f"⏱ {self.elapsed}s"

    def start_game(self, mode):
        cfg = self.modes_config[mode]
        self.current_mode  = mode
        self.secret        = random.randint(*cfg["range"])
        self.lives         = cfg["lives"]
        self.used          = 0
        self.game_active   = True
        self._t0           = time.time()
        self.elapsed       = 0
        self._hints_used   = 0
        self._round_score  = cfg["pts"]

        self.hist_box.clear_widgets()
        self.mode_lbl.text   = f"⚡ {mode.upper()}"
        self.timer_lbl.text  = "⏱ 0s"
        self.lives_lbl.text  = self._hrt()
        self.lives_lbl.color = C_GREEN
        self.streak_lbl.text = f"🔥 x{GS.streak}" if GS.streak > 1 else ""
        self.hint_lbl.text   = ""
        self.range_lbl.text  = f"Range: {cfg['range'][0]} – {cfg['range'][1]}"
        self.hud_lbl.text    = (f"Crack the code!\n"
                                f"Pick {cfg['range'][0]} – {cfg['range'][1]}")
        self.hud_lbl.color   = C_WHITE
        self.entry.text      = ""
        self.submit_btn.disabled = False
        self.hint_btn.disabled   = False
        self._update_score_bar()

        if self._timer_ev:
            self._timer_ev.cancel()
        self._timer_ev = Clock.schedule_interval(self._tick, 1)
        Clock.schedule_once(lambda *_: setattr(self.entry, 'focus', True), 0.4)

    def _update_score_bar(self):
        multiplier = 1 + (GS.streak * 0.1)
        self.score_lbl.text = f"Pts pool: {self._round_score}"
        self.multi_lbl.text = f"×{multiplier:.1f} streak" if GS.streak > 0 else ""

    def _hrt(self):
        cfg = self.modes_config[self.current_mode]
        return "❤️ " * self.lives + "🖤 " * (cfg["lives"] - self.lives)

    def _prox(self, diff, rng):
        pct = diff / (rng[1] - rng[0])
        if   pct < 0.05: return "▲ BURNING HOT!",    C_RED
        elif pct < 0.15: return "▲ Very warm",        C_ORANGE
        elif pct < 0.30: return "◆ Getting warmer",   C_YELLOW
        elif pct < 0.50: return "◆ Cool",             C_TEAL
        else:            return "◆ Ice cold",         C_CYAN

    def _lucky(self, *_):
        cfg = self.modes_config[self.current_mode]
        self.entry.text = str(random.randint(*cfg["range"]))
        Clock.schedule_once(lambda *_: setattr(self.entry, 'focus', True), 0.1)

    def _give_hint(self, *_):
        if not self.game_active:
            return
        cfg = self.modes_config[self.current_mode]
        lo, hi = cfg["range"]
        mid = (lo + hi) // 2
        self._hints_used += 1
        self._round_score = max(0, self._round_score - 10)
        self._update_score_bar()
        GS.play_sfx("hint")
        if self.secret <= mid:
            msg = f"◆ Hint  ›  Lower half  [ {lo} – {mid} ]"
        else:
            msg = f"◆ Hint  ›  Upper half  [ {mid+1} – {hi} ]"
        self.hint_lbl.text  = msg
        self.hint_lbl.color = C_YELLOW
        if self._hints_used >= 2:
            self.hint_btn.disabled = True
            self.hint_lbl.text += "  (no more hints)"

    def process_guess(self, *_):
        if not self.game_active:
            return
        raw = self.entry.text.strip()
        if not raw:
            self._flash("!  Type a number first", C_ORANGE)
            return
        try:
            guess = int(raw)
        except ValueError:
            self._flash("!  Numbers only", C_ORANGE)
            return
        cfg = self.modes_config[self.current_mode]
        if not (cfg["range"][0] <= guess <= cfg["range"][1]):
            self._flash(
                f"!  Out of range  [ {cfg['range'][0]} – {cfg['range'][1]} ]", C_ORANGE)
            return

        self.lives -= 1
        self.used  += 1
        self.lives_lbl.text = self._hrt()
        if self.lives <= 2:
            self.lives_lbl.color = C_RED

        diff = abs(guess - self.secret)
        GS.play_sfx("tick")

        if guess == self.secret:
            self._finish(won=True)
        elif self.lives == 0:
            self._finish(won=False)
        else:
            arrow = ("▼  Too HIGH  —  go lower"
                     if guess > self.secret else "▲  Too LOW  —  go higher")
            ht, hc = self._prox(diff, cfg["range"])
            self._flash(arrow, C_CYAN)
            self.hint_lbl.text  = ht
            self.hint_lbl.color = hc
            sym = "▲" if guess > self.secret else "▼"
            self._log(guess, sym)
            self.entry.text = ""
            GS.play_sfx("wrong")
            Clock.schedule_once(
                lambda *_: setattr(self.entry, 'focus', True), 0.15)

    def _finish(self, won):
        self.game_active = False
        self.submit_btn.disabled = True
        if self._timer_ev:
            self._timer_ev.cancel()

        cfg = self.modes_config[self.current_mode]
        multiplier = 1 + (GS.streak * 0.1)

        if won:
            bonus       = max(0, (self.lives / cfg["lives"]) * self._round_score)
            time_bonus  = max(0, 50 - self.elapsed)
            score       = int((self._round_score + bonus + time_bonus) * multiplier)
            GS.streak      += 1
            GS.total_wins  += 1
            GS.total_score += score
            hs = GS.high_scores[self.current_mode]
            if hs is None or self.used < hs:
                GS.high_scores[self.current_mode] = self.used
            self._log(self.secret, "✅")
        else:
            score     = 0
            GS.streak = 0
            self._log(self.secret, "❌")

        # Persist record
        GS.history.append({
            "mode":    self.current_mode,
            "won":     won,
            "tries":   self.used,
            "elapsed": self.elapsed,
            "score":   score,
        })
        GS.save()

        rs = self.manager.get_screen('result')
        rs.load(won, self.current_mode, self.secret, self.used, self.elapsed, score)
        self.manager.transition = FadeTransition(duration=0.4)
        self.manager.current = 'result'

    def _flash(self, text, color):
        self.hud_lbl.text  = text
        self.hud_lbl.color = (1, 1, 1, 0.15)
        Animation(color=color, duration=0.18).start(self.hud_lbl)

    def _log(self, guess, sym):
        self.hist_box.add_widget(Label(
            text=f"{sym}  #{self.used}  →  {guess}",
            font_size=sp(10), color=C_MUTED,
            size_hint_y=None, height=dp(18), halign='left'))

    def _back(self, *_):
        if self._timer_ev:
            self._timer_ev.cancel()
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'levels'

    def _on_kb(self, window, key, *args):
        # Android back / Esc returns to menu
        if key == 27 and self.manager and self.manager.current == 'game':
            self._back()
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════
class QuantumMatrixApp(App):
    title = "Quantum Matrix"

    def build(self):
        GS.load()
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(LevelScreen(name='levels'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(ResultScreen(name='result'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(LeaderboardScreen(name='leaderboard'))
        return sm

    def on_stop(self):
        GS.save()


if __name__ == '__main__':
    QuantumMatrixApp().run()
