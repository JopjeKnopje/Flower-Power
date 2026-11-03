docker_build:
	#!/bin/bash
	docker build -t pojpe/image_harvester:latest -t pojpe/image_harvester:$(git rev-parse --short HEAD) . -f docker/Dockerfile

docker_push:
	#!/bin/bash
	# docker image push pojpe/image_harvester:latest pojpe/image_harvester:$(git rev-parse --short HEAD)
	docker image push pojpe/image_harvester:$(git rev-parse --short HEAD)

docker_run:
	#!/bin/bash
	docker run pojpe/image_harvester:$(git rev-parse --short HEAD)

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
