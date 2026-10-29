from abc import ABC


# TODO: Add automagically called printing function post init
class Settings(ABC):
    _debug: bool = True
    server_host: str = "0.0.0.0"
    server_port: int = 5000

    @property
    def debug(self) -> bool:
        return self._debug


class SettingsDev(Settings): ...


class SettingsPytest(SettingsDev): ...


class SettingsProd(Settings): ...
