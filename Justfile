FLOWER_MACHINE_IP := "192.168.0.135"

ssh:
	ssh {{FLOWER_MACHINE_IP}}

push:
	rsync -aP image-harvester.toml pyproject.toml README.md crop-settings src --exclude '__pycache__/' {{FLOWER_MACHINE_IP}}:app/ -v
