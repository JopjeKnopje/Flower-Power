# Flower-Power
This repo contians all the packages and tooling for the Flower Power project.

The project currently has 2 main parts, and a 3rd for debugging and development.

- Image Harvester: Computer vision model, this will detect certain actions/movements of a crowd of people. And output a dataset (tbd) for our Flour Brain to use.
- Flour Brain: takes the previously generated dataset and generates reponses for it, it will talk to the 

- Hydraulic-sim: Simulatating the hydraulic cylinder's movement and providing a fake serial interface for our Flour Brain to talk to. I'd like for this to have a pytest interface as well so we can run some tests on the "cylinder".



## Dev dependencies
- [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)
- [prek](https://prek.j178.dev/installation/)
- [ruff](https://docs.astral.sh/ruff/editors/setup/)
- [basedpyright](https://github.com/DetachHead/basedpyright)

## After cloning
Install all the packages within the [`uv workspace`](https://docs.astral.sh/uv/concepts/projects/workspaces/)
```bash
uv sync --all-packages
```

## Running
Running the image-harvester
```bash
uv run image-harvester
```

### Other uv commands
Add a dependency to a package
```bash
uv add --package <package> <dependency-to-install>
```


### Camera setup
The camera's are running on `192.168.0.X/24`. They are marked with their number representing their `X` value.
They are looking for a gateway at `192.168.0.1`, in order to reach the camera's we can set our machine's address to that.
#### Reaching the cameras
Under linux you can add multiple addresses to your network interface.
```bash
# sudo ip addr add 192.168.0.1/24 dev <dev>
# in my case:
sudo ip addr add 192.168.0.1/24 dev enp42s0
```

You should now be able to reach the camera (and any other devices on the network)


## Raspberry PI
### Flashing the OS
I've flashed the an 64gb SD-card using [`rpi-imager`](https://github.com/raspberrypi/rpi-imager).
1. `Device -> Raspberry PI 4`.
2. `OS -> Raspberry PI OS (other) -> Raspberry PI OS Lite (64-bit)`.
3. Select the available storage drive.
4. `hostname -> 'flower-brain'`


hostname: `flower-brain` address





## Resources
- [pyproject.toml - dependency version syntax](https://stackoverflow.com/questions/54720072/dependency-version-syntax-for-python-poetry)
- [yolo - python docx](https://docs.ultralytics.com/usage/python)
- [what are tensors](https://medium.com/@payalparida_datascientist/why-tensors-are-essential-in-ml-dl-3fdd12365bca)
- [uv project structure](https://stackoverflow.com/a/79817200/7363348)
- [python logging cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [python forward declaration __future__](https://stackoverflow.com/a/55344418/7363348)

## Credits
- [bufferless-video-capture](https://stackoverflow.com/a/54755738/7363348)
- [colored logging python](https://stackoverflow.com/a/56944256/7363348)
