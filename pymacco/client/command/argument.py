class Argument:
    def __init__(self, name, description, optional=False):
        self.name = name
        self.description = description
        self.optional = optional
        self.rightBorder = "]" if optional else ">"
        self.leftBorder = "[" if optional else "<"

    def getHelp(self):
        return self.name + ": " + self.description

USER_NAME = Argument("username", "The user to login as.")
PASSWORD = Argument("password", "The password for the given user.")
COMMAND = Argument("command", "The command to get help with.", optional=True)
