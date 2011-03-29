import abc
from .. import pastie

class BaseCommand(object):
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __init__(self, parent_bot, command_re, command_name,
                 priority=50):
        super(BaseCommand, self).__init__()
        self.__parent_bot = parent_bot
        self.__command_re = command_re
        self.__command_name = command_name
        self.__db_handler = None
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
    
    def _register_database(self, *args, **kwargs):
        self.__db_handler = self.parent_bot.command_db.register_plugin(
            self.__command_name, *args, **kwargs
        )
    
    _register_db = _register_database
    
    def _get_database_handler(self):
        return self.__db_handler
    
    _get_db_handler = _get_database_handler
    
    _get_database = _get_database_handler
    
    _database_handler = property(_get_database_handler)
    _db_handler = property(_get_db_handler)
    _database = property(_get_database)
