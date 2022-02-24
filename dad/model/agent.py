import sys
import json
from functools import cache

from model.bdi import BeliefChange, Plan, Intention, BDIEvent, IntendedMeans


class AgentData:
    def __init__(self):
        self.intentions: dict[int, Intention] = {}
        self.intended_means: dict[int, IntendedMeans] = {}
        self.plans: dict[str, Plan] = {}
        self.events: dict[int, BDIEvent] = {}
        self.beliefs: list[BeliefChange] = []


class AgentRepository:
    def __init__(self, config):
        self.config = config

    # TODO improve with caching
    def get_agent_state(self, agent_name, cycle) -> dict:
        agent_data = self.get_agent_data(agent_name)

        beliefs = set()
        for belief_change in agent_data.beliefs:
            if belief_change.cycle > cycle:
                break
            if belief_change.added:
                beliefs.add(belief_change.belief)
            else:
                beliefs.remove(belief_change.belief)

        imeans_active = []
        for im_id, im in agent_data.intended_means.items():
            if im.start <= cycle <= im.end:
                imeans_active.append(im_id)

        intentions_active = []
        for intention in agent_data.intentions.values():
            if intention.start <= cycle <= intention.end:
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
        for im_id, im in agent_data.intended_means.items():
            if im.start >= cycle1:
                goals_started.append(im)
            if im.end <= cycle2:
                goals_finished.append(im)

        diff = {
            "B+": list(beliefs_added),
            "B-": list(beliefs_removed),
            "G+": goals_started,
            "G-": goals_finished
        }
        return diff

    @cache
    def get_agent_data(self, agent_name: str) -> AgentData:
        data = AgentData()
        log_path = self.config.get("current_folder") + "/" + agent_name + ".log"

        with open(log_path, "r") as log_file:
            info = json.loads(log_file.readline())
            details = info["details"]
            for label, pd in details["plans"].items():
                data.plans[label] = Plan(label, pd["trigger"], pd.get("ctx", "T"), pd["body"], pd["file"], pd["line"])

            for line in log_file.readlines():
                cycle = json.loads(line)
                if "I+" in cycle:
                    intention = Intention(cycle["I+"], cycle["nr"], sys.maxsize, [], [])
                    data.intentions[cycle["I+"]] = intention
                if "IM+" in cycle:
                    for im_data in cycle["IM+"]:
                        intention = data.intentions[im_data["i"]]
                        im = IntendedMeans(im_data["id"], intention, cycle["nr"], sys.maxsize, "?", im_data["file"],
                                           im_data["line"], data.plans[im_data["plan"]], [], None, None)
                        intention.means.append(im)
                        im.plan.used += 1
                        data.intended_means[im_data["id"]] = im
                        causing_event_id = cycle["SE"]
                        causing_event = data.events[causing_event_id]
                        im.event = causing_event
                        if causing_event.parent:
                            parent_im = causing_event.parent
                            im.parent = parent_im
                            parent_im.children.append(im)
                if "SI" in cycle:
                    intention = data.intentions[cycle["SI"]]
                    if "I" in cycle:
                        intention.instructions.append(cycle["I"]["instr"])
                if "IM-" in cycle:
                    for im_data in cycle["IM-"]:
                        im = data.intended_means[im_data["id"]]
                        im.end = cycle["nr"]
                        im.res = im_data.get("res", "?")
                if "I-" in cycle:
                    data.intentions[cycle["I-"]].end = cycle["nr"]
                if "E+" in cycle:
                    for event_data in cycle["E+"]:
                        event_id, event_content = event_data.split(": ")
                        instr = cycle["I"]["instr"] if "I" in cycle else ""
                        event = BDIEvent(None, cycle["nr"], event_content, instr, -1)
                        data.events[int(event_id)] = event
                        if "I" in cycle and "im" in cycle["I"]:
                            event.parent = data.intended_means[cycle["I"]["im"]]
                if "SE" in cycle:
                    selected_event_id = cycle["SE"]
                    data.events[selected_event_id].selected = cycle["nr"]
                if "B+" in cycle:
                    for belief in cycle["B+"]:
                        data.beliefs.append(BeliefChange(cycle["nr"], True, belief))
                if "B-" in cycle:
                    for belief in cycle["B-"]:
                        data.beliefs.append(BeliefChange(cycle["nr"], False, belief))
        return data
