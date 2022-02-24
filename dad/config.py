import os
import json


class Config:
    def __init__(self):
        if os.path.isfile("config.json"):
            with open("config.json", "r") as config_file:
                self.data = json.load(config_file)
        else:
            self.data = {
                "previous_folders": [],
                "current_folder": ""
            }

    def save(self):
        with open("config.json", "w") as config_file:
            json.dump(self.data, config_file)

    def get_previous_folders(self):
        self.data["previous_folders"] = list(filter(lambda path: os.path.isdir(path), self.data["previous_folders"]))
        self.save()
        return self.data["previous_folders"]

    def add_previous_folder(self, folder):
        previous_folders = self.data["previous_folders"]
        if folder not in previous_folders:
            previous_folders.insert(0, folder)
            self.data["previous_folders"] = previous_folders[:10]
            self.save()

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key):
        return self.data.get(key, "")
