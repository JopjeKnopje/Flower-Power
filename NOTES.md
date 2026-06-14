# Python jargon

- Module: just a python file containing some functions, variables etc. just a python file.
- Package: a collection of modules, it needs a `__init__.py` so the interpreter recognizes it as a package. The package is essentially a namespace.
- Libary: a loose term, we usually assume that its a collection of packages.

[uv init package/library](https://docs.astral.sh/uv/concepts/projects/init/)
[uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)


-------------------------------------------------
what is your intended pipeline?(high level)
image-harvester(detect people - output a level 1-4)
Flour brain(map level)
arduino/hyraulic controller
petal does things



# plan to get things going:
## scafold: ultralytics - opencv-python(video capture) - pyserial(to communicate output) - pyyaml(config) a YAML for any tunable config (camera, magic numbers, etc) - structlog(logging and debug) - 


## camera: a python script that opens the camera using opencv and shows a live window - 

## yolo inference - run pretrained(no need for training) on your frames - no need for CUDA wrestling - yolov8n on CPU ? - 

## before making a final decision for the level, wait a bit for confidence/stability? - so for example detect for x min to get a level, and take action based on that(would take x min for thr flower to do things), and then maybe again hold that level for x min before the loop begins again(so petals won't jitter or the action of opening and closing the petals is noticable and/or meaningful)

## output to brain via a queue (not sure)
the confuser running the script sends a byte(indicating a level) over serial to arduino

## source the camera?
## testing with humans :))) (call in all your friends over to walk around your mansion) - test with low lights
## testing with camera placement(height/angle) 

let me know what you think and also what next step you wanna take(don't wanna drop shites in your repo)