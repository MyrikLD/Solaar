class Text:
    def __init__(self, symb="\t", level=0):
        self.level = level
        self.symb = symb

    def __enter__(self):
        self.level += 1
        return self

    def __exit__(self, *args, **kwargs):
        self.level -= 1

    def __call__(self, text=""):
        print(self.symb * self.level + text)
