from .. import BaseCommand
import re
from .. import pastie
import textwrap

class UserDefinedCommand(BaseCommand):
    
    def __init__(self, parent_bot, priority=95):
        regex = re.compile("(set|del|get|get_raw|list|.*)")
        super(UserDefinedCommand, self).__init__(parent_bot, regex, "userdef",
                                                 priority)
        self.modified = True
        self.last_list_url = None
        self.command_ref_re = re.compile(r"!(\w+)")
        self._register_db("shelf", writeback=False, pickled=False)
    
    def parse_command(self, command, args, event, public):
        if command == "set":
            set_command = None
            if args:
                set_command = re.match(r"(\w+)\s+(.+)", args)
            if not set_command:
                self.send_message(event, "!set command_name something to say",
                                  True)
            else:
                self.db_set(set_command.group(1), set_command.group(2), event)
        elif command == "del":
            if not args:
                self.parent_bot.send_message(event, "!del command_name", True)
            else:
                self.db_del(args, event)
        elif command == "list":
            if not self.modified:
                self.send_message(event, self.last_list_url, True)
            else:
                listing = ""
                ref_dict = {}
                keys = list(self._database.keys())
                while keys:
                    i = keys[0]; del keys[0]
                    ref_set = set()
                    while self.command_ref_re.match(self._database[i]):
                        ref_set.add(i)
                        i = self.command_ref_re.match(self._database[i]) \
                            .group(1)
                    ref_set.add(i)
                    i = self._database[i]
                    if i in ref_dict:
                        ref_dict[i] |= ref_set
                    else:
                        ref_dict[i] = ref_set
                # Generate listing
                for k in list(ref_dict.keys()):
                    for i in ref_dict[k]:
                        listing += i + ":\n"
                    listing += textwrap.fill(k, 80, initial_indent=" " * 4,
                                             subsequent_indent=" " * 4) + "\n\n"
                url = pastie.Pastie(body=listing, parser=None, private=False,
                                    name=self.parent_bot.nickname).submit()
                self.send_message(event, url, True)
                self.modified = False
                self.last_list_url = url
        elif command == "get":
            if not args:
                self.send_message(event, "!get command_name [prefix]", True)
            else:
                get_command = re.match(r"(\w+)(\s+(.+))?", args)
                target = None
                try:
                    target = get_command.group(3)
                except IndexError:
                    pass
                self.db_get(get_command.group(1), target, event)
        elif command == "get_raw":
            if not args:
                self.send_message(event, "!get_raw command_name", True)
            else:
                self.db_get_raw(args, event)
        else:
            self.db_get(command, args, event)
    
    
    def db_set(self, key, value, event):
        self.modified = True
        key = key.lower()
        # block undefined references
        match = self.command_ref_re.match(value)
        if match and (str(match.group(1)) not in self._database):
            self.send_message(event, "\"%s\" is not in my database." % value,
                              True)
            return
        
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
                self.send_message(event,
                                  "That would make a recursive reference", True)
                # remove from db:
                if old_val:
                    self._database[key] = old_val
                else:
                    del self._database[key]
                return # something went wrong, exit early
            ref_set.add(g)
            cur_ref = self._database[g]
            cur_ref_match = self.command_ref_re.match(cur_ref)
    
    
    def db_del(self, key, event):
        self.modified = True
        key = key.lower()
        if str(key) not in self._database:
            self.send_message(event, "\"!%s\" is not in my database" % key,
                              True)
            return
        del self._database[key]
    
    
    def db_get(self, key, target, event):
        if str(key) not in self._database:
            self.send_message(event, "\"!%s\" is not in my database" % key,
                              True)
            return
        # process references
        while True:
            m = self.command_ref_re.match(self._database[key])
            if not m: break
            key = m.group(1)
        if not target:
            target = False
        self.send_message(event, self._database[key], target)
    
    
    def db_get_raw(self, key, event):
        self.send_message(event, self._database[key])
