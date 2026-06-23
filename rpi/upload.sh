#!/bin/bash

PI_ADDR="192.168.0.10"
PI_APP_DIR="~/app"

rsync -aPpz uv.lock pyproject.toml src packages ${PI_ADDR}:${PI_APP_DIR}/
