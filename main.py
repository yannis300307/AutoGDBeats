import base64
import gzip
import sys
import os
import pathlib

from bs4 import BeautifulSoup

import librosa

save_directory_path = pathlib.Path.home().joinpath("AppData/Local/GeometryDash")
save_file_path = save_directory_path.joinpath("CCLocalLevels.dat")


def string_xor(string, key):
    return "".join(chr(ord(c) ^ key) for c in string)


requested_level_name = input("Level Name ? > ").lower()

print("Loading file...")
with open(save_file_path, "r", encoding="UTF-8") as file:
    save_file_data = file.read()

if not save_file_data.startswith('<?xml'):
    print("Converting file...")
    data = string_xor(save_file_data, 11)
    data = base64.urlsafe_b64decode(data+"=======================")
    data = gzip.decompress(data).decode()
else:
    data = save_file_data

print("Parsing file data...")
soup = BeautifulSoup(data, "xml")
levels_tree = soup.plist.d

found_level = False
level_data = ""
level_name = ""
music_id = ""
level_data_reference = None

print("Looking for your level...")
for level in levels_tree.find_all("d"):
    level_data = ""
    level_name = ""
    music_id = ""
    level_data_reference = None
    for marker in level.find_all("k"):
        if marker.text == "k4":
            level_data = marker.find_next("s").text
            level_data_reference = marker.find_next("s")
        if marker.text == "k2":
            level_name = marker.find_next("s").text
        if marker.text == "k45":
            music_id = marker.find_next("i").text
    if level_name == requested_level_name:
        found_level = True
        print("Found!")
        break

if not found_level:
    print("Unable to find the level. Please check the name.")
    sys.exit()

print("name:", level_name)
print("music id:", music_id)
print("raw data:", level_data[:30] + " [...] " + level_data[-30:])

if not level_data.startswith('kS38'):
    print("Converting level...")
    level_data: str = gzip.decompress(base64.urlsafe_b64decode(level_data)).decode()

print("data:", level_data[:30] + " [...] " + level_data[-30:])

level_data: list = level_data.split(",")
beats_index = level_data.index("kA14")+1
beats_list = level_data[beats_index].split("~")

print("Current beats :", ", ".join(beats_list[:15]) + " [...] " + ", ".join(beats_list[len(beats_list)-15:]))

if input("Do you want to remove the current beats ? (Y/n) > ").lower() not in ["y", "o", "oui", "yes", ""]:
    sys.exit()

print("Processing music...")

music_path = save_directory_path.joinpath(f"{music_id}.mp3")

if not os.path.isfile(music_path):
    print("Please download the music in GD before.")
    sys.exit()

x, sr = librosa.load(music_path)
onset_frames = librosa.onset.onset_detect(y=x, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)
onset_times = librosa.frames_to_time(onset_frames)

print("Adding beats...")
beats_list = []
for i in onset_times:
    rounded_time = round(i, 2)
    beats_list.append(str(rounded_time))
    beats_list.append(str(0))  # 0 corresponds to the line color

print("Repackaging level...")
level_data[beats_index] = "~".join(beats_list)

level_data = ",".join(level_data)
level_data_reference.string = level_data

new_data = str(soup)

print("Saving...")
with open(save_file_path, "w", encoding="UTF-8") as file:
    file.write(new_data)
