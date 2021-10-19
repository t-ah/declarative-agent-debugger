import json
from functools import cache
from collections import Counter


class AgentRepository:
    def __init__(self, config):
        self.config = config

    @cache
    def get(self, agent_name):
        intentions = {}
        intended_means = {}
        plans_used = Counter()
        plans = {}
        data = {
            "plans": plans,
            "plans_used": plans_used,
            "intentions": intentions,
            "means": intended_means,
        }

        log_path = self.config.get("current_folder") + "/" + agent_name + ".log"

        with open(log_path, "r") as log_file:
            info = json.loads(log_file.readline())
            details = info["details"]
            for label, trigger in details["plans"].items():
                plans[label] = trigger

            for line in log_file.readlines()[1:]:
                cycle = json.loads(line)
                if "I+" in cycle:
                    intention = {
                        "start": cycle["nr"],
                        "means": [],
                        "instructions": []
                    }
                    intentions[cycle["I+"]] = intention
                if "IM+" in cycle:
                    for im_data in cycle["IM+"]:
                        intention = intentions[im_data["i"]]
                        intention["means"].append(im_data["id"])
                        im = {
                            "intention": im_data["i"],
                            "start": cycle["nr"],
                            "end": -1,
                            "res": "?",
                            "file": im_data["file"],
                            "line": im_data["line"],
                            "plan": im_data["plan"]
                        }
                        plans_used[im["plan"]] += 1
                        intended_means[im_data["id"]] = im
                if "SI" in cycle:
                    intention = intentions[cycle["SI"]]
                    intention["instructions"].append(())
                if "IM-" in cycle:
                    for im_data in cycle["IM-"]:
                        im = intended_means[im_data["id"]]
                        im["end"] = cycle["nr"]
                        im["res"] = im_data.get("res", "?")
                if "I-" in cycle:
                    intentions[cycle["I-"]]["end"] = cycle["nr"]
                if "E+" in cycle and "SI" in cycle:
                    for event in cycle["E+"]:
                        event_id = int(event.split(":")[0])
        return data