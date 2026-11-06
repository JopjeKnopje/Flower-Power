from setup import camera

# get the amount of people the cameras are detecting
people_count = camera.get_people_count()
# show the amount of people
print(f"people {people_count}")
