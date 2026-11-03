build:
	docker build -t image_harvester . -f docker/Dockerfile

run:
	docker run image_harvester

push-rpi:
	#!/bin/bash

	files=$(git ls-files)
	target_path=~/copy-test
	target_ip=192.168.0.135

	for f in $files
	do
		ssh ${target_ip} "mkdir -p ${target_path}/$(dirname $f)" -v
		scp -r $f ${target_ip}:${target_path}/$f
	done
