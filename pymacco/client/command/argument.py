class Argument:
    def __init__(self, name, description, optional=False):
        self.name = name
        self.description = description
        self.optional = optional
        self.rightBorder = "]" if optional else ">"
        self.leftBorder = "[" if optional else "<"

    def getHelp(self):
        return self.name + ": " + self.description

USER_NAME = Argument("username", "The username.")
PASSWORD = Argument("password", "The password for the given user.")
COMMAND = Argument("command", "The command to get help with.", optional=True)
HOST_NAME = Argument("hostname", "The host to connect to.")
PORT = Argument("port", "The port to connect to.", optional=True)
TABLE_NAME = Argument("tablename", "The name of the table.")
