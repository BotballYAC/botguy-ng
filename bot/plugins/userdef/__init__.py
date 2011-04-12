from .. import BasePlugin
from .. import CommandReply
from .. import command
import re
from .. import pastie
import textwrap

class UserDefinedCommand(BasePlugin):
    
    def __init__(self, parent_bot, priority=95):
        super(UserDefinedCommand, self).__init__(parent_bot, "userdef",
                                                 priority=priority)
        self.modified = True
        self.last_list_url = None
        self.command_ref_re = re.compile(r"!(?P<name>\w+)")
        self._register_db("shelf", writeback=False, pickled=False)
    
    
    @command("set", "!set command_name something to say")
    def set_command(self, opts):
        args = opts.args
        if not args:
            return ErrorCommandReply()
        arg_match = re.match(r"(\w+)\s+(.+)", args)
        if not arg_match or opts.args != arg_match.group(0):
            return ErrorCommandReply()
        key, value = arg_match.group(1), arg_match.group(2)
        self.modified = True
        key = key.lower()
        # block undefined references
        match = self.command_ref_re.match(value)
        if match and (str(match.group(1)) not in self._database):
            return ErrorCommandReply("\"%s\" is not in my database." % value)
        
        # block recursion
        old_val = None
        if str(key) in self._database:
            old_val = self._database[key]
        self._database[key] = value # we will go ahead and set this so that
                                  # recursion can be fully tested, and then we
                                  # will remove it later if something goes wrong
        cur_ref = value # current ref, this will change each iteration
        cur_ref_match = match # the re match object for the current ref
        ref_set = set() # keep a db of all previously passed refs, and if we
                        # find a duplicate, it means we have recursion
        while cur_ref_match: # while we are still dealing with refs
            g = cur_ref_match.group(1) # g = grouping
            if g in ref_set: # we have a duplicate, recursion!
                # remove from db:
                if old_val:
                    self._database[key] = old_val
                else:
                    del self._database[key]
                return ErrorCommandReply(
                    "That would make a recursive reference"
                )
            ref_set.add(g)
            cur_ref = self._database[g]
            cur_ref_match = self.command_ref_re.match(cur_ref)
        
        # everything checks out!
    
    
    @command("del", "!del command_name")
    def del_command(self, opts):
        key = opts.args
        if not key:
            return ErrorCommandReply()
        
        key = key.lower()
        if key not in self._database:
            return ErrorCommandReply("\"!%s\" is not in my database" % key)
        for i in self._database:
            ref_match = self.command_ref_re.match(self._database[i])
            if ref_match and ref_match.group("name") == key:
                return CommandReply(("\"!%s\" is a referenced by \"!%s\". " +
                                    "You should delete \"!%s\" first.") %
                                    (key, i, i))
        del self._database[key]
        self.modified = True
    
    
    @command("list", "!list")
    def list_command(self, opts):
        if opts.args:
            return CommandReply(self.list_command.command_simple_help)
        
        if not self.modified:
            return CommandReply(self.last_list_url)
        
        # Build up our reference dictionary
        ref_dict = {}
        keys = list(self._database.keys())
        while keys:
            i = keys[0]; del keys[0]
            ref_set = set()
            while self.command_ref_re.match(self._database[i]):
                ref_set.add(i)
                i = self.command_ref_re.match(self._database[i]).group(1)
            ref_set.add(i)
            i = self._database[i]
            if i in ref_dict:
                ref_dict[i] |= ref_set
            else:
                ref_dict[i] = ref_set
        
        # Generate listing using our reference dictionary
        listing = ""
        for k in list(ref_dict.keys()):
            for i in ref_dict[k]:
                listing += i + ":\n"
            listing += textwrap.fill(k, 80, initial_indent=" " * 4,
                                     subsequent_indent=" " * 4) + "\n\n"
        url = pastie.Pastie(body=listing, parser=None, private=False,
                            name=self.parent_bot.nickname).submit()
        self.modified = False
        self.last_list_url = url
        return CommandReply(url)
    
    
    @command("(get|.*)", "!get command_name [prefix] or !command_name [prefix]",
             95)
    def get_command(self, opts):
        # preprocess args
        args = opts.args
        if opts.command == "get":
            if not args:
                return CommandReply(self.get_command.command_simple_help)
            arg_match = re.match(r"(\w+)(\s+(.+))?", args)
            if not arg_match or arg_match.group(0) != args:
                return CommandReply(self.get_command.command_simple_help)
            command = arg_match.group(1)
            try:
                address = arg_match.group(3)
            except IndexError:
                address = False
        else:
            command, address = opts.command, opts.args
            if not address: address = False
        
        key = command
        key = key.lower()
        if key not in self._database:
            return CommandReply("\"!%s\" is not in my database" % key)
        
        # process references
        while True:
            m = self.command_ref_re.match(self._database[key])
            if not m: break
            key = m.group(1)
        
        return CommandReply(self._database[key], address)
    
    
    @command("get_raw", "!get_raw command_name")
    def get_raw_command(self, opts):
        key = opts.args
        if not key:
            return CommandReply(self.get_raw_command.command_simple_help)
        if key not in self._database:
            return CommandReply("\"!%s\" is not in my database" % key)
        
        return CommandReply(self._database[key])
