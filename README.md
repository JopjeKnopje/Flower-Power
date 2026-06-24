# Flower-Power
This repo contains packages and tooling for the Flower Power project, currently this setup is supposed to run on a linux based laptop.


Image Harvester: Runs a [YOLO](https://docs.ultralytics.com/models/yolo26#overview) model, this will count the amount of humans it detects. And output that value to the hydraulic controller using HTTP requests.


## Dependencies
- [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) 
- [prek](https://prek.j178.dev/installation/) (dev)
- [ruff](https://docs.astral.sh/ruff/editors/setup/) (dev)
- [basedpyright](https://github.com/DetachHead/basedpyright) (dev)


## Installation
1. Clone the repo and install its packages
```bash
git clone https://github.com/JopjeKnopje/Flower-Power
uv sync --all-packages
```

2. Make sure the config file values are correctly set, see [example](image-harvester.toml.example) config file.

3. Before running the image-harvester make sure that your machine can reach the cameras, see [Reaching the cameras](#reaching-the-cameras).

3. Run the image-harvester, it should automatically connect to the cameras.
```bash
uv run image-harvester
```





## Hardware
We are using a PoE Switch to power the cameras, the cameras don't actually have internet access.

The cameras we're using are [AXIS P3364-VE](https://www.axis.com/dam/public/ee/0b/43/axis-p3364-ve--user-manual-en-US-113863.pdf) security cameras (without their creepy housing).

### Camera addressing
The camera's are running on `192.168.0.X/24`, and are marked (see [photo](docs/cameras.jpg)) with their number representing the last digit of their IP address.
They are looking for a gateway at `192.168.0.1`, in order to reach the camera's we can set our machine's address to that.
### Reaching the cameras
Under linux you can add multiple addresses to your network interface.
```bash
# sudo ip addr add 192.168.0.1/24 dev <dev>
# in my case:
sudo ip addr add 192.168.0.1/24 dev enp42s0
```

You should now be able to reach the camera (and any other devices on the network)


## Troubleshooting
If for some reason the image-harvester won't connect to the camera(s)

Try seeing if they are reachable, I've made a tool which will ping the cameras defined in the config file.
You can run it with.
```bash
uv run ping-test
```

## Todo


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
