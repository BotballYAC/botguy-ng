import abc

class BaseCommand(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __init__(self, parent_bot, command_re, priority=50):
        self.__parent_bot = parent_bot
        self.__command_re = command_re
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
    
    def __cmp__(self, other):
        return self.priority - other.priority
