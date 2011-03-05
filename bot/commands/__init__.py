import abc
from .. import pastie

class BaseCommand(object):
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __init__(self, parent_bot, command_re, command_name, priority=50):
        self.__parent_bot = parent_bot
        self.__command_re = command_re
        self.__command_name = command_name
        self.priority = priority
    
    @abc.abstractmethod
    def parse_command(self, command, args, event):
        pass
    
    def get_command_re(self):
        return self.__command_re
    
    command_re = property(get_command_re)
    
    def get_parent_bot(self):
        return self.__parent_bot
    
    parent_bot = property(get_parent_bot)
    
    def get_name(self):
        return self.__command_name
    
    name = property(get_name)
    
    def __cmp__(self, other):
        return self.priority - other.priority
    
    def get_database(self):
        if self.name in self.parent_bot.command_db:
            return self.parent_bot.command_db[self.name]
        return None
    
    def set_database(self, db):
        self.parent_bot.command_db[self.name] = db
    
    database = property(get_database, set_database)
