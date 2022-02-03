import sys
import json
from functools import cache


class AgentRepository:
    def __init__(self, config):
        self.config = config

    # TODO improve with caching
    def get_agent_state(self, agent_name, cycle) -> dict:
        agent_data = self.get_agent_data(agent_name)

        beliefs = set()
        for current_cycle, type, belief in agent_data["beliefs"]:
            if current_cycle > cycle:
                break
            if type == "+":
                beliefs.add(belief)
            else:
                beliefs.remove(belief)

        imeans_active = []
        for im_id, im in agent_data["means"].items():
            if im["start"] <= cycle and im["end"] >= cycle:
                imeans_active.append(im_id)

        intentions_active = []
        for intention in agent_data["intentions"].values():
            if intention["start"] <= cycle and intention["end"] >= cycle:
                intentions_active.append(intention)

        state = {
            "beliefs": list(beliefs),
            "imeans": imeans_active,
            "intentions": intentions_active
        }
        return state

    def get_agent_state_diff(self, agent_name, cycle1, cycle2):
        agent_data = self.get_agent_data(agent_name)
        state1 = self.get_agent_state(agent_name, cycle1)
        state2 = self.get_agent_state(agent_name, cycle2)
        beliefs_added = set(state2["beliefs"]) - set(state1["beliefs"])
        beliefs_removed = set(state1["beliefs"]) - set(state2["beliefs"])

        goals_started = []
        goals_finished = []
        for im_id, im in agent_data["means"].items():
            if im["start"] >= cycle1:
                goals_started.append(im)
            if im["end"] <= cycle2:
                goals_finished.append(im)

        diff = {
            "B+": list(beliefs_added),
            "B-": list(beliefs_removed),
            "G+": goals_started,
            "G-": goals_finished
        }
        return diff

    @cache
    def get_agent_data(self, agent_name: str) -> dict:
        intentions = {}
        intended_means = {}
        plans = {}
        events = {}
        beliefs = []
        data = {
            "plans": plans,
            "intentions": intentions,
            "means": intended_means,
            "events": events,
            "beliefs": beliefs
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
                        "end": sys.maxsize,
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
                            "end": sys.maxsize,
                            "res": "?",
                            "file": im_data["file"],
                            "line": im_data["line"],
                            "plan": im_data["plan"],
                            "children": [],
                            "event": None
                        }
                        plans[im["plan"]]["used"] += 1
                        intended_means[im_data["id"]] = im
                        causing_event_id = cycle["SE"]
                        causing_event = events[causing_event_id]
                        im["event"] = causing_event
                        if causing_event["parent"]:
                            parent_im_id = causing_event["parent"]
                            im["parent"] = intended_means[parent_im_id]
                            intended_means[parent_im_id]["children"].append(im_data["id"])
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
                        instr = cycle["I"]["instr"] if "I" in cycle else ""
                        event = {
                            "parent": None,
                            "name": event_content,
                            "cycle": cycle["nr"],
                            "instruction": instr
                        }
                        events[int(event_id)] = event
                        if "I" in cycle and "im" in cycle["I"]:
                            event["parent"] = cycle["I"]["im"]
                if "SE" in cycle:
                    selected_event_id = cycle["SE"]
                    events[selected_event_id]["sel"] = cycle["nr"]
                if "B+" in cycle:
                    for belief in cycle["B+"]:
                        beliefs.append((cycle["nr"], "+", belief))
                if "B-" in cycle:
                    for belief in cycle["B-"]:
                        beliefs.append((cycle["nr"], "-", belief))
        return data