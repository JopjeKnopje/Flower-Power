# Flower-Power
This repo contians alls the packages and tooling for the Flower Power project.

The project currently has 2 main parts, and a 3rd for debugging and development.

- Image Harvester: Computer vision model, this will detect certain actions/movements of a crowd of people. And output a dataset (tbd) for our Flour Brain to use.
- Flour Brain: takes the previously generated dataset and generates reponses for it, it will talk to the 

- Hydraulic-sim: Simulatating the hydraulic cylinder's movement and providing a fake serial interface for our Flour Brain to talk to. I'd like for this to have a pytest interface as well so we can run some tests on the "cylinder".



## Dependencies
- [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)
- [prek](https://prek.j178.dev/installation/)

## Lsp
- [ruff](https://docs.astral.sh/ruff/editors/setup/)
- [basedpyright](https://github.com/DetachHead/basedpyright)

To install these in neovim I use [mason.nvim](https://github.com/mason-org/mason.nvim)


## Running
Running the flower sim
```bash
uv run hydraulic-sim
```

### Other uv commands
Add a dependency to a package
```bash
uv add --package <package> <dependency-to-install>
```


Because we're running in a workspace, you gotta add `--all-packages` when syncing.
```bash
uv sync --all-packages
```


## Resources
- [pyproject.toml - dependency version syntax](https://stackoverflow.com/questions/54720072/dependency-version-syntax-for-python-poetry)
- [yolo - python docx](https://docs.ultralytics.com/usage/python)
