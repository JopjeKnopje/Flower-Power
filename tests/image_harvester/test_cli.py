import image_harvester
import importlib
from image_harvester.flower_api import Flower
from image_harvester.processor import AbstractProcessor, Processor


def test_class_list() -> None:
    sub_classes = [cls.__name__ for cls in AbstractProcessor.__subclasses__()]



    api = Flower("192.168.0.1:9000")

    obj = getattr(importlib.import_module("image_harvester.processor"), sub_classes[0])(api)
    assert isinstance(obj, Processor)

