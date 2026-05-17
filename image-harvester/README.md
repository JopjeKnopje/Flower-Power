# Image Harvester
This package will take care of crowd detection


> [!note]
> This has only been tested on a GTX 1080 TI, any other CUDA <12.6 should work too I guess
## Issues

### GPU Problems
When running the example code I was greeted with this message
```bash

/home/joppe/Stuff/Programming/Flower-Power/.venv/lib/python3.13/site-packages/torch/cuda/__init__.py:384: UserWarning: Found GPU0 NVIDIA GeForce GTX 1080 Ti which is of compute capability (CC) 6.1.
The following list shows the CCs this version of PyTorch was built for and the hardware CCs it supports:
- 7.5 which supports hardware CC >=7.5,<8.0
- 8.0 which supports hardware CC >=8.0,<9.0 except {8.7}
- 8.6 which supports hardware CC >=8.6,<9.0 except {8.7}
- 9.0 which supports hardware CC >=9.0,<10.0
- 10.0 which supports hardware CC >=10.0,<11.0 except {10.1}
- 12.0 which supports hardware CC >=12.0,<13.0
Please follow the instructions at https://pytorch.org/get-started/locally/ to install a PyTorch release that supports one of these CUDA versions: 12.6
  _warn_unsupported_code(d, device_cc, code_ccs)
/home/joppe/Stuff/Programming/Flower-Power/.venv/lib/python3.13/site-packages/torch/cuda/__init__.py:502: UserWarning:
NVIDIA GeForce GTX 1080 Ti with CUDA capability sm_61 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_75 sm_80 sm_86 sm_90 sm_100 sm_120.
If you want to use the NVIDIA GeForce GTX 1080 Ti GPU with PyTorch, please check the instructions at https://pytorch.org/get-started/locally/
```

As you can see its complaining about the `CC`([Compute Capability](https://developer.nvidia.com/cuda/gpus)) version since I'm running a pretty old card.



### Compute Capability vs CUDA Version????!?!?!
Take a look at [this](https://gist.github.com/CyberSys/9e65d4c7c92cc9d6fa12c7bae133ce50#cuda-terminology-reference) nice matrix.


sm_61 in my case the GTX 1080ti, running cc 6.1.
The `SM` version is set, since thats the actual hardware.
I'm pretty sure that the `CC` is also "hard-linked" to the `SM`.

Then the question is: is the `CUDA Version` dependend on the installed drivers or hard-coupled to the hardware?

the discrepancy is when running `nvidia-smi` which tells me I'm running CUDA Version `13.0`?

When looking at [CUDA Version vs CC](https://stackoverflow.com/a/28933055/7363348), it seems I can run CUDA Version `=<12.6`


I went over to [pytorch previous-versions](https://pytorch.org/get-started/previous-versions/)
```bash
uv add --package image-harvester torch==2.11.0+cu126 torchvision==0.26.0 torchaudio==2.11.0 --default-index https://download.pytorch.org/whl/cu126
```



Pytorch ships with its own [CUDA runtime](https://discuss.pytorch.org/t/compatibility-between-cuda-12-6-and-pytorch/209649/2)

### Installing without package manager
It this point I wanted to not deal with `uv` just yet, when I installed the packages with just `pip` and ran their example code. It did run, without any GPU issues.

```bash
pip install torch==2.11.0+cu126  --index-url https://download.pytorch.org/whl/cu126
pip install torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu126
pip install ultralytics
```

After that I slowly moved back to a `uv` setup, which now works :)

