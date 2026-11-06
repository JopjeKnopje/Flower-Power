from setup import camera, flower

# get the amount of people the cameras are detecting
people_count = camera.get_people_count()
# show the amount of people
print(f"people {people_count}")

# check if the count is between 1 and 9
if people_count >= 1 <= 9:
    print("people count with in range")
    # move the flower to that position
    flower.move(people_count)

# move the flower to position 0
else:
    flower.move(0)
