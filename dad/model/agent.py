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
                temp_ims = []
                if "I+" in cycle:
                    intention = Intention(cycle["I+"], cycle["nr"], sys.maxsize, [], [], [])
                    data.intentions[cycle["I+"]] = intention
                if "IM+" in cycle:
                    for im_data in cycle["IM+"]:
                        intention = data.intentions[im_data["i"]]
                        im = IntendedMeans(im_data["id"], intention, cycle["nr"], sys.maxsize, "?", im_data["file"],
                                           im_data["line"], data.plans[im_data["plan"]], im_data["trigger"], [], None,
                                           None)
                        intention.means.append(im)
                        temp_ims.append(im)
                        im.plan.used += 1
                        data.intended_means[im_data["id"]] = im

                        if "parent" in im_data:
                            parent_im_id = int(im_data["parent"])
                            parent_im = data.intended_means[parent_im_id]
                            im.parent = parent_im
                            parent_im.children.append(im)
                if "E+" in cycle:
                    for event_data in cycle["E+"]:
                        ev_id, trigger = event_data.split(": ")
                        event = BDIEvent(None, cycle["nr"], trigger, -1)
                        if ev_id != "B":  # max. 1 event of this type
                            parent_im_id = int(ev_id)
                            event.parent = data.intended_means[parent_im_id]
                            event.parent.intention.events.append(event)
                        else:
                            pass  # TODO see other TODO below
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
                if "SE" in cycle:  # E+ and IM+ need to be processed before SE
                    event_data = cycle["SE"]
                    ev_id, trigger = event_data.split(": ")
                    if ev_id != "B":
                        intention_id = int(ev_id)
                        intention = data.intentions[intention_id]
                        event = intention.events[-1]
                        event.selected = cycle["nr"]
                    else:
                        event = BDIEvent(None, cycle["nr"], trigger, cycle["nr"])
                        intention_id = cycle["I+"]  # SE with B-id means a new intention is created
                        intention = data.intentions[intention_id]
                        intention.events.append(event)
                        # TODO when was the event actually posted?
                    for im in temp_ims:
                        im.event = event
                    #     if event.parent:
                    #         im.parent = event.parent
                    #         event.parent.children.append(im)
                    #         # print(f"{im.plan.trigger} --> {im.parent.plan.trigger}")
                if "B+" in cycle:
                    for belief in cycle["B+"]:
                        data.beliefs.append(BeliefChange(cycle["nr"], True, belief))
                if "B-" in cycle:
                    for belief in cycle["B-"]:
                        data.beliefs.append(BeliefChange(cycle["nr"], False, belief))
        return data
