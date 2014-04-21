import traceback

from twisted.internet import reactor
from twisted.protocols import basic

import pymacco
from pymacco.client.command.command import Command
import pymacco.client.command.argument as argument

DEBUG = True


class BaseCommandProcessor(basic.LineReceiver):
    """ Protocol that implements something similar to `cmd.Cmd` for Twisted.

        Subclasses simply implement commands by creating ``do_<something>``

        For example:

        >>> class MyCommand(BaseCommandProcessor):
        >>>    def do_help(self):
        >>>        self.sendLine("My help message.")

    """
    delimiter = '\n'
    _prompt = '>>> '

    def __init__(self, factory):
        self.factory = factory
        self.commands = []
        self._initCommands()

    def _initCommands(self):
        self.commands = []

    def prompt(self):
        self.transport.write(self._prompt)

    def sendLine(self, line, prompt=True):
        basic.LineReceiver.sendLine(self, line)
        if prompt:
            self.prompt()

    def connectionMade(self):
        self.sendLine("Pymacco (version: %s)" % pymacco.getVersionString(),
                prompt=False)
        self.sendLine("Type 'help' for a list of available commands.")

    def connectionLost(self, reason):
        self.sendLine("Connection lost", prompt=False)
        if reactor.running:
            reactor.stop()

    def lineReceived(self, line):
        if not line:
            self.prompt()
            return

        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]
        self._dispatch(command, args)

    def _dispatch(self, commandName, args):
        command = None
        for c in self.commands:
            if c.name == commandName:
                command = c

        if command is None:
            self.sendLine("Error: No such command.")
            return
        elif not command.isUsable():
            self.sendLine("Error: Command not currently available.")
            return

        if len(args) < len(command.requiredArguments):
            self.sendLine(command.getHelp())
            return

        command.execute(*args)


class ExtendedCommandProcessor(BaseCommandProcessor):
    """A `BaseCommandProcessor` subclass that implements some common commands.
    """
    def _initCommands(self):
        BaseCommandProcessor._initCommands(self)
        self.commands.extend(
                [Command("help",
                         "List commands, or show help of the given command.",
                         self.do_help, [argument.COMMAND], []),
                 Command("quit",
                         "Quit this session.",
                         self.do_quit, [], [])])

    def do_help(self, command=None):
        if command:
            matchingCommand = None
            for c in self.commands:
                if command == c.name:
                    matchingCommand = c

            if matchingCommand is not None:
                if not matchingCommand.isUsable():
                    self.sendLine("Error: Command not currently available.")
                else:
                    self.sendLine(matchingCommand.getHelp())
            else:
                self.sendLine("Error: No such command.")
        else:
            commands = [c.name for c in self.commands if c.isUsable()]
            self.sendLine('Valid commands:\n\t' + '\n\t'.join(commands))

    def do_quit(self):
        """quit: Quit this session"""
        self.sendLine("Quitting...", prompt=False)
        self.transport.loseConnection()


class PymaccoClientCommandProcessor(ExtendedCommandProcessor):
    def __init__(self, client):
        ExtendedCommandProcessor.__init__(self, None)
        self.client = client

    def _initCommands(self):
        ExtendedCommandProcessor._initCommands(self)
        self.commands.extend(
                [Command("connect",
                         "Connect to the given server.",
                         self.do_connect, [argument.HOST_NAME, argument.PORT],
                         [self.require_disconnect]),
                 Command("disconnect",
                         "Disconnect from the current server.",
                         self.do_disconnect, [], [self.require_connect]),

                 Command("register", "Register the given username/password.",
                         self.do_register, [argument.USER_NAME,
                                            argument.PASSWORD],
                         [self.require_connect]),
                 Command("login", "Log in to the current server with the given "
                                  "username and password.",
                         self.do_login, [argument.USER_NAME, argument.PASSWORD],
                         [self.require_connect, self.require_logout]),
                 Command("users", "List the logged-in users.",
                         self.do_users, [], [self.require_connect,
                                             self.require_login]),

                 Command("tables", "List the available tables.",
                         self.do_tables, [], [self.require_connect,
                                              self.require_login]),
                 Command("create-table", "Create a new table with the given name.",
                         self.do_create_table, [argument.TABLE_NAME],
                         [self.require_connect, self.require_login]),
                 Command("join-table", "Join the table with the given name.",
                         self.do_join_table, [argument.TABLE_NAME],
                         [self.require_connect, self.require_login]),
                 Command("leave-table", "Leave the table with the given name.",
                         self.do_leave_table, [argument.TABLE_NAME],
                         [self.require_connect, self.require_login])])

    def do_connect(self, hostname, port=8777):
        def completeConnection(success):
            if self.client.connected is True:
                self.sendLine("Successfully connected to %s." % hostname)
            else:
                self.sendLine("Failed to connect to %s." % hostname)

        self.sendLine("Connecting to %s." % hostname, False)
        root = self.client.connect(hostname, int(port))
        root.addCallback(completeConnection)

    def do_disconnect(self):
        host = self.client.host
        self.client.disconnect()
        self.sendLine("Disconnected from %s" % host)

    def do_register(self, username, password):
        def registerSuccess(avatar):
            self.sendLine("Successfully registered.")

        d = self.client.register(username, password)
        d.addCallbacks(registerSuccess, self.errback)

    def do_login(self, username, password):
        def loginSuccess(avatar):
            self.sendLine("Successfully logged in.")

        d = self.client.login(username, password)
        d.addCallbacks(loginSuccess, self.errback)

    def errback(self, failure):
        self.sendLine("Error: %s" % failure.getTraceback())

    def do_users(self):
        self._getRoster('users')

    def do_tables(self):
        self._getRoster('tables')

    def do_create_table(self, name):
        def createSuccess(table):
            self.sendLine("Created table '%s'." % name)

        def join(table):
            self.do_join_table(name)

        d = self.client.createTable(name)
        d.addCallbacks(createSuccess, self.errback)
        #d.addCallback(join)

    def do_join_table(self, name):
        def joinSuccess(table):
            self.sendLine("Joined '%s'" % name)

        d = self.client.joinTable(name)
        d.addCallbacks(joinSuccess, self.errback)

    def do_leave_table(self, name):
        def leaveSuccess(table):
            self.sendLine("Left table '%s'" % name)

        d = self.client.leaveTable(name)
        d.addCallbacks(leaveSuccess, self.errback)

    def _getRoster(self, name):
        entries = "\n".join(getattr(self.client, name))
        self.sendLine(entries)

    def require_connect(self):
        return self.client.connected

    def require_disconnect(self):
        return not self.require_connect()

    def require_login(self):
        return self.client.avatar is not None

    def require_logout(self):
        return not self.require_login()
