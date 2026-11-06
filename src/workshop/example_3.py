from setup import flower
from time import sleep


counter = 0
# run this loop while counter is less than 10
while counter < 10:
    print(f"moving flower to position {counter}")
    flower.move(counter)
    print("waiting a second")
    sleep(1)
    # increase counter by 1
    counter += 1

print("done :)")
