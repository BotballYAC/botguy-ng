import re
import collections
from . import BasePlugin
from . import command
from . import CommandReply

class VoteCommand(BaseCommand):
    
    def __init__(self, parent_bot, priority=50):
        super(VoteCommand, self).__init__(parent_bot, "votepoll",
                                          priority=priority)
        self._register_db("shelf", writeback=False, pickled=True)
        self.modified = True
        self.last_list_url = None
    
    @command("make_poll",
             "!make_poll poll_name Some question? (red, green, blue, purple)")
    def make_poll_command(self, opts):
        # Parse command
        match = re.match(r"(?P<poll_name>\w+)\s+(?P<question>.*?)\s*" +
                         r"\(\s*(?P<options>\w+(,\s?\w+)+)\s*\)", opts.args)
        if not match or match.group(0) != opts.args:
            return CommandReply(self.make_poll_command.command_simple_help)
        
        groups = match.groupdict()
        if groups["poll_name"] in self._database:
            return CommandReply("The poll name \"%s\" has already been taken" %
                                groups["poll_name"])
        
        choices = dict.fromkeys(re.split(r"\s*,\s*", groups["options"]))
        for i in choices: choices[i] = set()
        
        # generate and store poll object
        poll = Poll(groups["poll_name"], opts.caller, groups["question"],
                    choices)
        self._database[poll.name] = poll
        self.modified = True
    
    @command("del_poll", "!del poll_name")
    def del_poll_command(self, opts)
            match = re.match(r"\w+", args)
            if not match or match.group(0) != args:
                self.send_message(event, "!del poll_name", True)
                return
            if not match.group(0) in self._database:
                self.send_message(event, "The poll, \"%s\" does not exist." %
                                         match.group(0), True)
                return
            poll = self._database[match.group(0)]
            if poll.maker != event.source and \
               event.source not in self.parent_bot.superusers:
                self.send_message(event, "You must be identified as a " +
                                  "superuser or the poll's maker to delete it.",
                                  True)
                return
            del self._database[poll]
            self.modified = True
        elif command == "vote":
            match = re.match(r"(?P<poll_name>\w+)\s+(?P<choice>\w+)", args)
            if not match or match.group(0) != args:
                self.send_message(event, "!vote poll_name choice", True)
                return
            groups = match.groupdict()
            if groups["poll_name"] not in self._database:
                self.send_message(event, "The poll, \"%s\" does not exist." %
                                         groups["poll_name"], True)
                return
            poll = self._database[groups["poll_name"]]
            if groups["choice"] not in poll.options:
                self.send_message(event, ("%s is not an available option for " +
                                  "this poll") % groups["choice"], True)
                return
            for i in poll.options:
                if event.source in poll.options[i]:
                    self.send_message(event, ("You already voted for %s, so " +
                                      "your vote will be changed.") % i, True)
                    poll.options[i].remove(event.source)
                    break
            poll.options[groups["choice"]].add(event.source)
            self._database[poll.name] = poll
            self.modified = True
        elif command == "poll_results":
            match = re.match(r"\w+", args)
            if not match or match.group(0) != args:
                self.send_message(event, "!del poll_name", True)
                return
            if not match.group(0) in self._database:
                self.send_message(event, "The poll, \"%s\" does not exist." %
                                         match.group(0), True)
                return
            self.send_message(event, self.get_result_string(match.group(0)),
                              True)
        elif command == "list_polls":
            if not self.modified:
                self.send_message(event, self.last_list_url, True)
            else:
                pass
            
    def get_result_string(self, poll):
        poll = self._database[poll]
        votes = {}
        for i in poll.options:
            votes[i] = len(poll.options[i])
        tot = sum(votes.values())
        if not tot:
            return "0 votes"
        return "%d votes: %s" % \
            (tot, ", ".join(["%s %d%%" % (i, int(100.*float(votes[i])/tot)+.5)
                             for i in votes]))

Poll = collections.namedtuple("Poll", "name maker question options")
