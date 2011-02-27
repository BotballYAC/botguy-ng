import re

curses = ["fuck", "fucking", "fucked", "damn", "damnation", "dammit", "crap",
          "goddammit", "shit", "screwed", "shoes"]
regex_curses = []

for c in curses:
    regex = c
    if isinstance(c, str):
        regex = re.compile(r"(\W|^)" + re.escape(c) + r"(\W|$)", re.IGNORECASE)
    regex_curses.append(regex)

