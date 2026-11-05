from core.flower_api import FlowerAPI
from core.image_harvester_api import ImageHarvesterAPI
# from image_harvester.flower_config import FlowerConfig

camera = ImageHarvesterAPI("192.168.0.10:5000")
flower = FlowerAPI("192.168.0.135:5000")
