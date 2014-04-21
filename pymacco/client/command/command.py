class Command:

    def __init__(self, name, description, target, arguments, requirements):
        self.name = name
        self.description = description
        self.target = target
        self.arguments = arguments
        self.requiredArguments = [arg for arg in arguments if not arg.optional]
        self.optionalArguments = [arg for arg in arguments if arg.optional]
        self.requirements = requirements

    def getHelp(self):
        helpstr = self.name
        for argument in self.arguments:
            helpstr += (" " + argument.leftBorder + argument.name +
                        argument.rightBorder)

        helpstr += ": " + self.description + "\n"

        for argument in self.arguments:
            helpstr += "\t" + argument.getHelp() + "\n"

        return helpstr

    def isUsable(self):
        for requirement in self.requirements:
            if not requirement():
                return False
        return True

    def execute(self, *args):
        self.target(*args)
