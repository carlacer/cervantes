"""Pawfect Care decorations (paws, banners) and date/time input masks."""

import customtkinter as ctk

from utils.theme import COLORS

PAW = "🐾"

# Soft versions of the brand colours, used for background decoration.
PASTEL = {
    "pink": "#FFD9E5",
    "blue": "#D6EBFF",
    "yellow": "#FFF0C2",
}


def paw_strip(parent, pady=(14, 0)):
    """A small row of paws in pink, yellow and blue."""
    strip = ctk.CTkFrame(parent, fg_color="transparent")
    strip.pack(pady=pady)
    for color in ("pink", "yellow", "blue", "yellow", "pink"):
        ctk.CTkLabel(
            strip, text=PAW, font=("Arial", 18), text_color=COLORS[color]
        ).pack(side="left", padx=5)
    return strip


def paw_banner(parent, title, subtitle=None):
    """Blue header banner with pink/yellow paws and a pink-yellow accent line."""
    banner = ctk.CTkFrame(parent, fg_color=COLORS["blue"], corner_radius=0)
    banner.pack(fill="x")

    inner = ctk.CTkFrame(banner, fg_color="transparent")
    inner.pack(pady=(14, 12))

    ctk.CTkLabel(
        inner, text=PAW, font=("Arial", 28), text_color=COLORS["pink"]
    ).pack(side="left", padx=(0, 14))

    text_frame = ctk.CTkFrame(inner, fg_color="transparent")
    text_frame.pack(side="left")
    ctk.CTkLabel(
        text_frame, text=title, font=("Arial", 24, "bold"), text_color="#FFFFFF"
    ).pack()
    if subtitle:
        ctk.CTkLabel(
            text_frame, text=subtitle, font=("Arial", 13), text_color="#FFFFFF"
        ).pack()

    ctk.CTkLabel(
        inner, text=PAW, font=("Arial", 28), text_color=COLORS["yellow"]
    ).pack(side="left", padx=(14, 0))

    stripe = ctk.CTkFrame(parent, fg_color="transparent")
    stripe.pack(fill="x", pady=(0, 16))
    for color in ("pink", "yellow", "pink", "yellow", "pink"):
        ctk.CTkFrame(
            stripe, height=6, corner_radius=0, fg_color=COLORS[color]
        ).pack(side="left", fill="x", expand=True)
    return banner


def scatter_paws(parent):
    """Place large pastel paws on a background. Call before adding the card."""
    spots = [
        (0.06, 0.10, 54, "pink"), (0.20, 0.30, 36, "yellow"),
        (0.10, 0.55, 46, "blue"), (0.24, 0.80, 58, "pink"),
        (0.04, 0.88, 34, "yellow"), (0.94, 0.12, 50, "blue"),
        (0.80, 0.28, 38, "pink"), (0.90, 0.52, 56, "yellow"),
        (0.76, 0.78, 44, "blue"), (0.95, 0.90, 36, "pink"),
        (0.50, 0.06, 32, "yellow"), (0.50, 0.94, 40, "blue"),
    ]
    for relx, rely, size, color in spots:
        ctk.CTkLabel(
            parent, text=PAW, font=("Arial", size), text_color=PASTEL[color]
        ).place(relx=relx, rely=rely, anchor="center")


# ---------------------------------------------------------------------------
# Date / time input masks
# ---------------------------------------------------------------------------

_IGNORED_KEYS = {
    "Left", "Right", "Up", "Down", "Home", "End", "Tab", "ISO_Left_Tab",
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    "Caps_Lock", "Escape", "Return", "KP_Enter",
}

DATE_GROUPS = (4, 2, 2)      # YYYY-MM-DD
DATE_LIMITS = (None, 1, 3)   # first digit of month > 1 or day > 3 gets a leading 0
TIME_GROUPS = (2, 2)         # HH:MM
TIME_LIMITS = (2, 5)         # first digit of hour > 2 or minute > 5 gets a leading 0


def format_masked(raw, groups, limits, separator, trailing=True):
    """Return raw text formatted into groups of digits joined by separator.

    With trailing=True, the separator is added as soon as a group is full
    (typing forward). With trailing=False (deleting) it is not.
    """
    digits = "".join(ch for ch in raw if ch.isdigit())[:sum(groups)]
    parts = []
    position = 0
    for size, limit in zip(groups, limits):
        if position >= len(digits):
            break
        chunk = digits[position:position + size]
        if limit is not None and size == 2 and chunk[0] > str(limit):
            chunk = "0" + chunk[0]
            position += 1
        else:
            position += len(chunk)
        parts.append(chunk)
    text = separator.join(parts)
    if (trailing and parts and len(parts) < len(groups)
            and len(parts[-1]) == groups[len(parts) - 1]):
        text += separator
    return text


def _bind_mask(entry, groups, limits, separator):
    def on_key(event):
        if event.keysym in _IGNORED_KEYS:
            return
        trailing = event.keysym not in ("BackSpace", "Delete")
        current = entry.get()
        formatted = format_masked(current, groups, limits, separator, trailing)
        if formatted != current:
            entry.delete(0, "end")
            entry.insert(0, formatted)

    entry.bind("<KeyRelease>", on_key, add="+")


def bind_date_mask(entry):
    """Auto-insert dashes while typing a YYYY-MM-DD date."""
    _bind_mask(entry, DATE_GROUPS, DATE_LIMITS, "-")


def bind_time_mask(entry):
    """Auto-insert the colon while typing a 24-hour HH:MM time."""
    _bind_mask(entry, TIME_GROUPS, TIME_LIMITS, ":")
