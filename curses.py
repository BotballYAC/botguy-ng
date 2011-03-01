import re

curses = [re.compile("(.*|^)fuck(.*|$)"), "damn", "damnation", "dammit", "crap",
          "goddammit", "shit", "screwed", "shoes", "ass", "asshat", "jackass",
          "donkey kong", "tits", "sonuvabitch", "dickhead", "gay", "horny",
          "fag", "faggot", "penis", "vagina" "cunt", "bitch", "asshole", "slut",
          "whore", "pussy"]
regex_curses = []

for c in curses:
    regex = c
    if isinstance(c, str):
        regex = re.compile(r"(\W|^)" + re.escape(c) + r"(\W|$)", re.IGNORECASE)
    regex_curses.append(regex)

