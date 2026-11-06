from core.flower_api import FlowerAPI
from core.image_harvester_api import ImageHarvesterAPI

# from image_harvester.flower_config import FlowerConfig

camera = ImageHarvesterAPI("192.168.0.135:5000")
flower = FlowerAPI("192.168.0.42")
# ensure we're not running in mainmode
_ = flower.main_mode(False)
