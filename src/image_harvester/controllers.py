from litestar import Controller, get


class RootController(Controller):
    @get()
    def hello(self) -> str:
        return "hi"
