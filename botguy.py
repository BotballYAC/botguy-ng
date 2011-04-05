from bot.ircutils import bot
import re
from bot import curses
from bot.rss import rss
from bot.rss import rss_feeds
from bot import database
import dbm
import threading
import traceback
from bot.commands import userdef

class Botguy(bot.SimpleBot):
    
    def __init__(self, *args, **kwargs):
        info_file = "botguy_info.db"
        if "command_file" in kwargs:
            command_file = kwargs["command_file"]
            del kwargs["command_file"]
        plugins = []
        if "plugins" in kwargs:
            plugins = kwargs["plugins"]
            del kwargs["plugins"]
        if "superusers" in kwargs:
            self.superusers = kwargs["superusers"]
            del kwargs["superusers"]
        else:
            self.superusers = []
        super(Botguy, self).__init__(*args, **kwargs)
        self.channel_set = set()
        self.command_db = database.Database(command_file, True)
        self.commands_list = sorted([i(self) for i in plugins],
                                    key=lambda x: x.priority)
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
    
    def has_curse(self, message):
        if botguy_config.block_cursing:
                for c in curses.regex_curses:
                    if c.search(message):
                        return True
        return False
    
    def on_channel_message(self, event):
        with threading.Lock():
            if event.source == self.nickname: return
            m = event.message
            # Cursing
            if self.has_curse(m):
                self.send_message(event.target, event.source +
                    ", please refrain from using cuss words in the " +
                    event.target + " chat.")
            else:
                self.parse_command(event, True)
    
    def on_private_message(self, event):
        with threading.Lock():
            if event.source == self.nickname: return
            m = event.message
            # Cursing
            if self.has_curse(m):
                self.send_message(event.source,
                                  "Please refrain from using cuss words")
            else:
                self.parse_command(event, False)
    
    def parse_command(self, event, public_message):
        # pre-process event
        m = event.message
        channel = None
        user = event.source
        if public_message:
            channel = event.target
        
        def send_message(msg):
            print(msg)
            if public_message:
                self.send_message(channel, "%s, %s" % (user, msg))
            else:
                self.send_message(user, msg)
        
        base_command_re = r"(\w+)(\s+(.+))?\s*"
        if public_message:
            base_command_re = "!%s" % base_command_re
        else:
            base_command_re = "!?%s" % base_command_re
        base_command_re = re.compile(base_command_re)
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
                if (c.public and public_message or
                    c.private and not public_message) \
                   and c.command_re.match(command_name):
                    try: # sandboxing!
                        c.parse_command(command_name, command_args,
                                        event, public_message)
                    except Exception as ex:
                        send_message("Something has caused me to run into an " +
                                     "error. Please bother the operator of " +
                                     "this bot to fix me.")
                        print((traceback.print_exc()))
                    had_command = True
                    break;
            if not had_command:
                send_message("Sorry, \"!%s\" is not a defined commmand" %
                             command_name)
    
    def on_feed_update(self, entry):
        for c in self.channel_set:
            print(c)
            print(entry.link + ": " + entry.title)
            with threading.Lock():
                self.send_message(c, entry.link + ": " + entry.title)

if __name__ == "__main__":
    from bot import botguy_config
    bot = Botguy(botguy_config.nick, command_file=botguy_config.info_file,
                 plugins=botguy_config.command_plugins,
                 superusers=botguy_config.superusers)
    bot.connect(botguy_config.server, channel=botguy_config.channels)
    bot.start()
