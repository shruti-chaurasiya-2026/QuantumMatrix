[app]

# ── Identity ────────────────────────────────────────────────────────
title           = Quantum Matrix
package.name    = quantummatrix
# IMPORTANT: change com.yourname to something unique before publishing
# e.g.  com.shruti.quantummatrix
package.domain  = com.yourname

# ── Source ──────────────────────────────────────────────────────────
source.dir      = .
source.include_exts    = py,png,jpg,kv,atlas,wav,ogg,mp3,json,ttf
source.include_patterns = assets/*

# ── Entry point (MUST be named main.py for buildozer) ───────────────
# The file main.py in this folder imports python.py — see main.py
# Do NOT rename python.py; main.py is a one-line shim.

# ── Version ─────────────────────────────────────────────────────────
version         = 2.0

# ── Requirements ────────────────────────────────────────────────────
# pillow is only needed for generate_assets.py (screenshot tool) — NOT at runtime
requirements = python3,kivy==2.3.0

# ── Android display ─────────────────────────────────────────────────
orientation     = portrait
fullscreen       = 1

# ── Icons & presplash ───────────────────────────────────────────────
# Provide a 512×512 PNG as assets/icon.png for the app store icon
# icon.filename        = %(source.dir)s/assets/icon.png
# presplash.filename   = %(source.dir)s/assets/presplash.png
presplash.color = #0A0A12

# ── Android SDK / NDK ───────────────────────────────────────────────
android.api         = 33
android.minapi      = 21
android.ndk         = 25b
android.ndk_api     = 21
android.archs       = arm64-v8a, armeabi-v7a

# No special permissions needed — game is fully offline
android.permissions =

# ── Android features ────────────────────────────────────────────────
android.allow_backup        = True
android.wakelock            = False

# ── Buildozer internals ─────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1
