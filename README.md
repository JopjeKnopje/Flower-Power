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

3. Before running the image-harvester make sure that your machine can reach the cameras, see [reaching the cameras](#reaching-the-cameras).

3. Run the image-harvester, it should automatically connect to the cameras.
```bash
uv run image-harvester
```





## Hardware
We are using a PoE Switch to power the cameras, the cameras don't actually have internet access.

The cameras we're using are [AXIS P3364-VE](https://www.axis.com/dam/public/ee/0b/43/axis-p3364-ve--user-manual-en-US-113863.pdf) security cameras (without their creepy housing).

### Camera addressing
The camera's are running on `192.168.0.X/24`, and are marked (see [photo](docs/cameras.jpg)) with their number representing the last digits of their IP address.

### Reaching the cameras
In order to reach the camaras we have to tell our machine that, you can do this by _adding_ a static IP address to your network interface.
Which will also add a route to your routing table. (`ip route`)

You can add the address to your network interface with.
```bash
# sudo ip addr add 192.168.0.20/24 dev <dev>
# in my case:
sudo ip addr add 192.168.0.20/24 dev enp42s0
```

You should now be able to reach the camera (and any other devices on that network)




## Troubleshooting
### Camera unreachable
If for some reason the image-harvester won't connect to the camera(s)

Try seeing if they are reachable, I've made a tool which will ping the cameras defined in the config file.
You can run it with.
```bash
uv run ping-test
```

### Bad camera focus


### Resetting the camera
Checkout the manual
TBA pressing the actual button

Set the password to `admin`



## Todo V2
- See if we EVEN NEED this cuda lib `python -c "import torch; print(torch.cuda.is_available())"`
- Add `cam_id` to config file, also check that there are no duplicates
- Add support to the `Config` for using linux video devices indentified by a number e.g `cv2.VideoCapture(0)`
- Ping tool also pings flower endpoint lol
- Tweak model (set minimum confidence score threshold in config file?)
- Send out a status check to the hydraulic controller at the same time it connects with the cameras to make sure its online
- Set it up on a RPI (ansible? or some other iac tool) and write setup instructions for that.
- Container to keep track of all the file recording stuff, such as the filepath.
- Script to do initial setup of the cameras.
- Add threading while connecting to the cameras.
- Benchmark yolo runs and image stitching parts of the program
- fix hconcat
- Wait for all cameras in feed to come online with a set timeout, also when camera goes offline log it. But keep going
- Check the camera resolution
- Increase yolo resolution?
- Do 2 builds/modes?, one for x86_64 and the other for ARM64
- `value = math.tanh(1 * math.pi / 2)  * 10`

## Weird nvidia fix
`torch==2.11.0` adds a bunch of nvidia packages, even when running on aarch64 (which doesn't hava GPU lol)
I "fixed" this by running `torch==2.6.0`. I still have to figure out why this is being added
When running `2.11.0` we get illegal instruction, probablyt because it calls to an nvidia cuda binary which we cannot execute ofc.
Lets `strace` that


When we strace `2.11.0` we can see its looking for 
```bash
openat(AT_FDCWD, "/home/pi/rpi-object-detection/venv/lib/python3.13/site-packages/torch/lib/../../nvidia/cudnn/lib/libcuda.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/home/pi/rpi-object-detection/venv/lib/python3.13/site-packages/torch/lib/../../nvidia/nvshmem/lib/libcuda.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/home/pi/rpi-object-detection/venv/lib/python3.13/site-packages/torch/lib/../../nvidia/nccl/lib/libcuda.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/home/pi/rpi-object-detection/venv/lib/python3.13/site-packages/torch/lib/../../nvidia/cusparselt/lib/libcuda.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/home/pi/rpi-object-detection/venv/lib/python3.13/site-packages/torch/lib/../../nvidia/cu13/lib/libcuda.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/home/pi/rpi-object-detection/venv/lib/python3.13/site-packages/torch/lib/libcuda.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or dir
```


When we strace `2.6.0`, `libcuda` is not even mentioned

2.9 also works

## Resources
- [pyproject.toml - dependency version syntax](https://stackoverflow.com/questions/54720072/dependency-version-syntax-for-python-poetry)
- [pyproject.toml - environment markers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/)
- [yolo - python docx](https://docs.ultralytics.com/usage/python)
- [what are tensors](https://medium.com/@payalparida_datascientist/why-tensors-are-essential-in-ml-dl-3fdd12365bca)
- [uv project structure](https://stackoverflow.com/a/79817200/7363348)
- [python logging cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [python forward declaration __future__](https://stackoverflow.com/a/55344418/7363348)

## Credits
- [bufferless-video-capture](https://stackoverflow.com/a/54755738/7363348)
- [colored logging python](https://stackoverflow.com/a/56944256/7363348)
