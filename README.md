# Flower-Power
This repo contians the packages and tooling for the Flower Power project.

- Image Harvester: Runs a [YOLO](https://docs.ultralytics.com/models/yolo26#overview) model, this will count the amount of  humans it detects. And output that value to the hydraulic controller.




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


## Roadmap


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
