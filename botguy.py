from bot.ircutils import bot
import re
from bot import curses
from bot.rss import rss
from bot.rss import rss_feeds
from bot import shove
import dbm
import atexit
import threading
import traceback
from bot.commands import userdef

class Botguy(bot.SimpleBot):
    
    def __init__(self, *args, **kwargs):
        info_file = "botguy_info.db"
        if "command_file" in kwargs:
            command_file = kwargs["command_file"]
            del kwargs["command_file"]
        super(Botguy, self).__init__(*args, **kwargs)
        self.channel_set = set()
        self.command_db = shove.Shove("file://" + command_file, protocol=2)
        atexit.register(self.command_db.close)
        self.commands_list = [userdef.UserDefinedCommand(self)]
        self.commands_list.sort()
        #for f in rss_feeds.feed_list:
        #    rss.RssPoller(f[0], self.on_feed_update, f[1])
    
    def on_join(self, event):
        if event.source == self.nickname:
            with threading.Lock():
                self.channel_set.add(event.target)
            print("Joined Channel: " + event.target)
    
    def on_invite(self, event):
        print("Invited to Channel: " + event.params[0])
        with threading.Lock():
            self.join_channel(event.params[0])
    
    def on_quit(self, event):
        # I still need to figure this function out. It is needed if the bot is
        # to be stable
        print("Quit from server: " + event.source)
        if event.target == self.nickname:
            with threading.Lock():
                self.channel_set.remove(event.target)
                self.join_channel(event.target)
    
    def on_kick(self, event):
        if event.params[0] == self.nickname:
            print("Kicked from Channel: " + event.target)
            with threading.Lock():
                self.channel_set.remove(event.target)
    
    def on_channel_message(self, event):
        with threading.Lock():
            if event.source == self.nickname: return
            m = event.message
            has_curse = False
            # Cursing
            if botguy_config.block_cursing:
                for c in curses.regex_curses:
                    if c.search(m):
                        self.send_message(event.target,
                                          event.source +
                                          ", please refrain from " +
                                          "using cuss words in the " +
                                          event.target + " chat.")
                        has_curse = True
                        break
            if not has_curse:
                base_command_re = re.compile(r"!(\w+)(\s+(.+))?")
                base_command_match = base_command_re.match(m)
                if base_command_match:
                    command_name = base_command_match.group(1)
                    command_args = None
                    try:
                        command_args = base_command_match.group(3)
                    except IndexError:
                        pass
                    had_command = False
                    for c in self.commands_list:
                        if c.command_re.match(command_name):
                            try: # sandboxing!
                                c.parse_command(command_name, command_args,
                                                event)
                            except Exception as ex:
                                self.send_message(event.target, event.source +
                                                  ", something has caused me " +
                                                  "to run into an error. " +
                                                  "Please bother the " +
                                                  "operator of this bot to " +
                                                  "fix me.")
                                print((traceback.print_exc()))
                            had_command = True
                            break;
                    if not had_command:
                        self.send_message(event.target, event.source +
                                      ", sorry, \"!" + command_name + "\" is " +
                                      "not a defined command.")
    
    def on_feed_update(self, entry):
        for c in self.channel_set:
            print(c)
            print(entry.link + ": " + entry.title)
            with threading.Lock():
                self.send_message(c, entry.link + ": " + entry.title)

if __name__ == "__main__":
    from bot import botguy_config
    bot = Botguy(botguy_config.nick, command_file=botguy_config.info_file)
    bot.connect(botguy_config.server, channel=botguy_config.channels)
    bot.start()
