import abc
import collections
import re
from .. import pastie

class BasePlugin(object):
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __init__(self, parent_bot, plugin_name, private=True, public=True,
                 priority=50):
        super(BasePlugin, self).__init__()
        self.__parent_bot = parent_bot
        self.__plugin_name = plugin_name
        self.__db_handler = None
        self.priority = priority
        self.public = public
        self.private = private
        self.__events = self.parent_bot.events
        self._commands = []
        for i in dir(self): # TODO: FIXME: dir isn't made to be used like this
            try:
                assert getattr(self, i).is_command
                self._commands.append(getattr(self, i))
            except (AssertionError, AttributeError):
                pass
        self._commands.sort(key=lambda x: x.command_priority)
    
    def supports_command(self, *args, **kwargs):
        command = CommandCall(self, *args, **kwargs)
        if command.public and not self.public or \
           command.private and not self.private:
            return False
        for i in self._commands:
            m = i.command_regex.match(command.command)
            if m and m.group(0) == command.command:
                return True
        return False
    
    def parse_command(self, *args, **kwargs):
        if not self.supports_command(*args, **kwargs):
            return False
        command = CommandCall(self, *args, **kwargs)
        for i in self._commands:
            m = i.command_regex.match(command.command)
            if m and m.group(0) == command.command:
                result = i(command)
                if isinstance(result, CommandReply):
                    if isinstance(result, ErrorCommandReply):
                        result.send_reply(command, i.command_simple_help)
                    else:
                        result.send_reply(command)
                return True
        return False
    
    def get_parent_bot(self):
        return self.__parent_bot
    
    parent_bot = property(get_parent_bot)
    
    def get_events(self):
        return self.__events
    
    events = property(get_events)
    
    def get_name(self):
        return self.__command_name
    
    name = property(get_name)
    
    def __cmp__(self, other):
        return self.priority - other.priority
    
    def _register_database(self, *args, **kwargs):
        self.__db_handler = self.parent_bot.plugin_db.register_plugin(
            self.__plugin_name, *args, **kwargs
        )
    
    _register_db = _register_database
    
    def _get_database_handler(self):
        return self.__db_handler
    
    _get_db_handler = _get_database_handler
    
    _get_database = _get_database_handler
    
    _database_handler = property(_get_database_handler)
    _db_handler = property(_get_db_handler)
    _database = property(_get_database)



class CommandCall(collections.namedtuple("CommandCallBase",
                                         "plugin_handler event command args")):
    
    def get_is_public(self):
        return self.event.target[0] == "#"
    
    is_public = property(get_is_public)
    public = property(get_is_public)
    
    def get_is_private(self):
        return not self.is_public
    
    is_private = property(get_is_private)
    private = property(get_is_private)
    
    def get_parent_bot(self):
        return self.plugin_handler.parent_bot
    
    parent_bot = property(get_parent_bot)
    
    def get_caller(self):
        return self.event.source
    
    caller = property(get_caller)
    
    def get_location(self):
        """If this is a public message, this returns the channel that the
        command was issued from. If this is a private message, this returns the
        user who spoke the command, the ``caller``. The location is the default
        target for sending a reply."""
        return self.event.target
    
    location = property(get_location)
    
    def send_reply(self, *args, **kwargs):
        """Equivalent to
        ``CommandReply(*args, **kwargs).send_reply(command_call)``"""
        CommandReply(*args, **kwargs).send_reply(self)


CommandReplyBase = collections.namedtuple("CommandReplyBase",
                                          "message addressed target")

class CommandReply(CommandReplyBase):
    """Commands can return a CommandReply to have a message sent back, as an
    alternative to sending a reply directly through the CommandCall object."""
    
    def __new__(cls, message, addressed=True, target=None):
        """If addressed is ``True`` (the default), the message will be addressed
        to the command's caller, as in ``user_nick, message to send user``. If
        it is a string, the message will be addressed in the form of ``address
        string with spaces, message to respond with``. ``target`` defaults to
        the ``location`` from which the command originated. If for example, if
        you had a command that was designed to issue a private message to
        another user, you could change the reply ``target``."""
        return CommandReplyBase.__new__(cls, message, addressed, target)
    
    def send_reply(self, command_call, message=None):
        parent_bot = command_call.parent_bot
        
        # solve for target
        target = self.target
        if target == None:
            target = command_call.location
        is_public_target = target[0] == "#"
        is_private_target = not is_public_target
        
        # solve for addressed
        addressed = self.addressed
        if is_public_target and addressed is True:
            # If addressed is a boolean marked as True, address to caller
            addressed = command_call.caller
        elif is_private_target and addressed is True:
            # Ignore anything but explicit addressing with private messages,
            # addressing a private messaged person is redundant.
            addressed = False
        
        # solve for message
        if not message:
            message = self.message
        if addressed:
            message = "%s, %s" % (addressed, message)
        
        # send it off
        parent_bot.send_message(target, message)

class ErrorCommandReply(CommandReply):
    def __new__(cls, message=None):
        return CommandReply.__new__(cls, message, addressed=True)
    
    def send_message(self, command_call, default_message="Something has " +
                     "caused me to run into an error. Please bother the " +
                     "operator of this bot to fix me."):
        if not self.message:
            CommandReply.send_reply(self, command_call, default_message)
        else:
            CommandReply.send_reply(self, command_call)

try:
    basestring
except:
    basestring = str

def command(regex, simple_help=None, priority=50):
    if isinstance(regex, basestring):
        regex = re.compile(regex)
    def command_decorator(f):
        f.is_command = True
        f.command_regex = regex
        f.command_simple_help = simple_help
        f.command_priority = priority
        return f
    return command_decorator
