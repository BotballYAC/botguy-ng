# Basic Configuration:
nick = "botguy-ng"
info_file = "botguy_info_converted.db"
server = "irc.freenode.net"
channels = ["#botball"]
block_cursing = True

# Advanced Options
python_targets = (2, 3) # shortening this list may allow for some optimizations
# Warning: Only change python_targets with a fresh database
pickle_protocol = 2 if 2 in python_targets else 3
