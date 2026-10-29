from abc import ABC


# TODO: Add automagically called printing function post init
class Settings(ABC):
    _debug: bool = True

    @property
    def debug(self) -> bool:
        return self._debug


class SettingsDev(Settings): ...


class SettingsPytest(SettingsDev): ...


class SettingsProd(Settings): ...
