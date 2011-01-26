from __future__ import with_statement

from ircutils import bot
import re
import curses
import rss
import rss_feeds
import shelve
import atexit
import threading
import traceback
from commands import userdef

class Botguy(bot.SimpleBot):
    
    def __init__(self, *args, **kwargs):
        info_file = "botguy-info.dat"
        if "info_file" in kwargs:
            info_file = kwargs["info_file"]
            del kwargs["info_file"]
        super(Botguy, self).__init__(*args, **kwargs)
        self.channel_set = set()
        self.info_db = shelve.open(info_file)
        atexit.register(self.info_db.close)
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
            for c in curses.regex_curses:
                if c.search(m):
                    self.send_message(event.target,
                                      event.source + ", please refrain from " +
                                      "using cuss words in the #botball chat.")
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
                                print(traceback.print_exc())
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
    import botguy_config
    bot = Botguy(botguy_config.nick, info_file=botguy_config.info_file)
    bot.connect(botguy_config.server, channel=botguy_config.channels)
    bot.start()
