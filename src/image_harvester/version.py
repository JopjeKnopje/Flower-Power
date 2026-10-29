from importlib import metadata

try:
    __version__ = metadata.version("image-harvester")
except metadata.PackageNotFoundError:
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
    __version__ = tomllib.loads(pyproject.read_text()).get("project.version")
