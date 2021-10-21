import json
from functools import cache


class AgentRepository:
    def __init__(self, config):
        self.config = config

    @cache
    def get(self, agent_name):
        intentions = {}
        intended_means = {}
        plans = {}
        events = {}
        data = {
            "plans": plans,
            "intentions": intentions,
            "means": intended_means,
        }

        log_path = self.config.get("current_folder") + "/" + agent_name + ".log"

        with open(log_path, "r") as log_file:
            info = json.loads(log_file.readline())
            details = info["details"]
            for label, plan_data in details["plans"].items():
                plans[label] = plan_data
                plan_data["used"] = 0

            for line in log_file.readlines():
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
                            "plan": im_data["plan"],
                            "children": []
                        }
                        plans[im["plan"]]["used"] += 1
                        intended_means[im_data["id"]] = im
                        causing_event_id = cycle["SE"]
                        causing_event = events[causing_event_id]
                        if causing_event["parent"]:
                            parent_im_id = causing_event["parent"]
                            im["parent"] = intended_means[parent_im_id]["children"].append(im_data["id"])
                if "SI" in cycle:
                    intention = intentions[cycle["SI"]]
                    if "I" in cycle:
                        intention["instructions"].append(cycle["I"]["instr"])
                if "IM-" in cycle:
                    for im_data in cycle["IM-"]:
                        im = intended_means[im_data["id"]]
                        im["end"] = cycle["nr"]
                        im["res"] = im_data.get("res", "?")
                if "I-" in cycle:
                    intentions[cycle["I-"]]["end"] = cycle["nr"]
                if "E+" in cycle:
                    for event_data in cycle["E+"]:
                        event_id, event_content = event_data.split(": ")
                        event = {
                            "parent": None,
                            "name": event_content
                            }
                        events[int(event_id)] = event
                        if "I" in cycle and "im" in cycle["I"]:
                            event["parent"] = cycle["I"]["im"]
        return data