class MyClass:
    def __init__(self):
        self.name = "John"
        self.age = 23
        self.active = True

    # Method to print all variables inside the class
    def print_variables(self):
        for var, value in vars(self).items():
            print(f"{var}: {value}")


# Create an instance
obj = MyClass()

# Print all variables
obj.print_variables()