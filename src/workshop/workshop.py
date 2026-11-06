from time import sleep
from setup import flower


for i in range(0, 4):
    x = flower.fire(i, 500)
    sleep(0.1)
