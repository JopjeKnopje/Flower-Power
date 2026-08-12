# Flower-Power
This repo contains packages and tooling for the Flower Power project, currently this setup is supposed to run on a linux based laptop.


Image Harvester: Runs a [YOLO](https://docs.ultralytics.com/models/yolo26#overview) model, this will count the amount of humans it detects. And output that value to the hydraulic controller using HTTP requests.


## Dependencies
- [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) 
- [prek](https://prek.j178.dev/installation/) (dev)
- [ruff](https://docs.astral.sh/ruff/editors/setup/) (dev)
- [basedpyright](https://github.com/DetachHead/basedpyright) (dev)
- [just](https://just.systems/man/en/)


## Installation
1. Clone the repo and install its packages
```bash
git clone https://github.com/JopjeKnopje/Flower-Power
uv sync --all-packages
```

2. Make sure the config file values are correctly set, see [example](image-harvester.toml.example) config file.

3. Before running the image-harvester make sure that your machine can reach the cameras, see [reaching the cameras](#reaching-the-cameras).

4. Optionally you can setup cropping for the camera feeds by running.
```bash
uv run image-harvester crop
```

5. Run the image-harvester, it should automatically connect to the cameras.
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




TODO: CLEAN UP DOWCX AHHAHAHHA


# Addressing

If you cannot reach the camera check fi they're running on `192.168.0.90` which is their default address.


Its all in the `192.168.0.0/24` range, these addresses are static.
We connect to this network using a laptop, also configured with a static address.
We can connect our laptop to a mobile hotspot or wifi network if we wan't connectivity.

In case we need network access to the RPI, we could setup a route to the laptop which will have a masqurade rule?


RPI: 192.168.0.135
CAM-1: 192.168.0.1
CAM-2: 192.168.0.2
CAM-3: 192.168.0.3
CAM-4: 192.168.0.4
FLOWER_ENDPOINT: 192.168.0.42

## Configure WAN less setup

Add a static ip to our interface so we can access the "flower network"

### Laptop configuration
```bash
sudo ip link set enp0s31f6 down
sudo ip a add 192.168.0.10/24 dev enp0s31f6
sudo ip link set enp0s31f6 up
# there should be a route added, if thats not the case run.
sudo ip route add 192.168.0.0/24 dev enp0s31f6
```


### Desktop configuration

```bash
sudo ip a add 192.168.0.10/24 dev enp42s0
```

### Using DHCP server to reach the PI in-case of static ip issues
```bash
sysctl net.ipv4.ip_unprivileged_port_start=67
apt install dns masq
```

in its config `/etc/dnsmasq.conf` set `port=0` to disable its DNS shit

Monitor its logs with
```bash
journalctl --follow -u dnsmasq
```
## Troubleshooting
### Check if running cuda

```bash
uv run python -c "import torch; print(torch.cuda.is_available())"
```

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
### Crop mode
Select which camera frame we wanna modify and set a horizontal crop line for that using a UI.
We'd run the program like `image-harvester crop`

- [ ] Fix fonts
- [ ] The cropper should be `VideoSource` agnostic, it currently only works for `VideoSourceRTP`.
- [ ] Crop images to remove sky, join images together to optimize space.
- [ ] Don't die when camara disconnects
- [ ] Use predict instead of track
- [ ] Use optimized model format for PI / edge devices
- [ ] Stream/log datapoints
- [ ] Remote video feed
- [ ] Flower animation
- [ ] NOTE: Flower pos is 0-9
- [ ] Add endpoint to ping test
- [ ] Setup/preview mode, run the GUI without any api calls or processing
- [ ] Run simple server on the RPI which logs the data both pre and post processed from the flower.
- [ ] Add seek to video playback
- [ ] Think about design pattern so we can inject behaviour in our loop regarding running headless.
- [ ] Add `cam_id` to config file, also check that there are no duplicates
- [ ] Add support to the `Config` for using linux video devices indentified by a number e.g `cv2.VideoCapture(0)`
- [ ] Ping tool also pings flower endpoint lol
- [ ] Tweak model (set minimum confidence score threshold in config file?)
- [ ] Send out a status check to the hydraulic controller at the same time it connects with the cameras to make sure its online
- [ ] Set it up on a RPI (ansible? or some other iac tool) and write setup instructions for that.
- [ ] Container to keep track of all the file recording stuff, such as the filepath.
- [ ] Script to do initial setup of the cameras.
- [ ] Add threading while connecting to the cameras.
- [ ] Benchmark yolo runs and image stitching parts of the program
- [ ] fix hconcat
- [ ] Wait for all cameras in feed to come online with a set timeout, also when camera goes offline log it. But keep going
- [ ] Check the camera resolution
- [ ] Increase yolo resolution?
- [ ] Do 2 builds/modes?, one for x86_64 and the other for ARM64
- [ ] `value = math.tanh(1 * math.pi / 2)  * 10`

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
- [python protocols](https://andrewbrookins.com/technology/building-implicit-interfaces-in-python-with-protocol-classes/)

## Credits
- [bufferless-video-capture](https://stackoverflow.com/a/54755738/7363348)
- [colored logging python](https://stackoverflow.com/a/56944256/7363348)
