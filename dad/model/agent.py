from dataclasses import dataclass

import sys
import json
from functools import cache

from model.bdi import BeliefChange, Plan, Intention, BDIEvent, IntendedMeans, Instruction, EventType, FailureReason


class AgentData:
    def __init__(self):
        self.intentions: dict[int, Intention] = {}
        self.intended_means: dict[int, IntendedMeans] = {}
        self.plans: dict[str, Plan] = {}
        self.events: dict[int, BDIEvent] = {}
        self.beliefs: list[BeliefChange] = []


@dataclass
class AgentStateDiff:
    beliefs_added: list[str]
    beliefs_deleted: list[str]
    goals_added: list[IntendedMeans]
    goals_achieved: list[IntendedMeans]


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

    def get_diff(self, agent_name: str, cycle1: int, cycle2: int) -> AgentStateDiff:
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

        return AgentStateDiff(list(beliefs_added), list(beliefs_removed), goals_started, goals_finished)

    def get_cycle_diff(self, agent: str, cycle: int):
        return self.get_diff(agent, cycle - 1, cycle)

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
                ims_added_this_cycle = []
                if "I+" in cycle:
                    intention = Intention(cycle["I+"], cycle["nr"], sys.maxsize, [], [])
                    data.intentions[cycle["I+"]] = intention
                if "IM+" in cycle:
                    for im_data in cycle["IM+"]:
                        intention = data.intentions[im_data["i"]]
                        im = IntendedMeans(im_data["id"], intention, cycle["nr"], sys.maxsize, "?", None,
                                           im_data["file"], im_data["line"], [], data.plans[im_data["plan"]],
                                           im_data["trigger"], im_data.get("ctx", "T"), [], None, None)
                        intention.means.append(im)
                        ims_added_this_cycle.append(im)
                        im.plan.used += 1
                        data.intended_means[im_data["id"]] = im

                if "E+" in cycle:
                    for event_data in cycle["E+"]:
                        ev_id = event_data["id"]
                        trigger = event_data["t"]
                        event = BDIEvent(ev_id, None, trigger, EventType.BELIEF_UPDATE, cycle["nr"], -1)
                        if event_data["src"] == "B":  # event is belief update
                            pass
                        else:
                            if "nf" in event_data:  # new focus (!!...)
                                event.type = EventType.GOAL_NEW_FOCUS
                            else:
                                event.type = EventType.SUB_GOAL
                            if "I" in cycle:
                                parent_im_id = int(cycle["I"]["im"])
                            else:  # parent is SE because no applicable plan
                                parent_event_id = cycle["SE"]
                                parent_event = data.events[parent_event_id]
                                parent_im_id = parent_event.parent.id
                            event.parent = data.intended_means[parent_im_id]
                            event.parent.intention.events.append(event)
                        data.events[ev_id] = event
                if "I" in cycle:
                    instr_data = cycle["I"]
                    im = data.intended_means[instr_data["im"]]
                    instruction = Instruction(instr_data["file"], instr_data["line"], instr_data["instr"], cycle["nr"])
                    im.instructions.append(instruction)
                    if "U" in cycle:
                        instruction.unifier = cycle["U"]
                if "IM-" in cycle:
                    for im_data in cycle["IM-"]:
                        im_id = im_data["id"]
                        if im_id == -1:  # IM did not really exist -> no applicable/relevant plan
                            pass  # TODO selected event SE could not be handled
                        else:
                            im = data.intended_means[im_data["id"]]
                            im.end = cycle["nr"]
                            im.res = im_data["res"]
                            if "reason" in im_data:
                                reason = im_data["reason"]
                                im.failure_reason = FailureReason.from_jason_dict(reason)

                if "I-" in cycle:
                    for intention_id in cycle["I-"]:
                        data.intentions[intention_id].end = cycle["nr"]
                if "SE" in cycle:  # E+ and IM+ need to be processed before SE
                    ev_id = cycle["SE"]
                    event = data.events[ev_id]
                    event.cycle_selected = cycle["nr"]
                    if not event.type == EventType.SUB_GOAL:  # i.e. new intention if applicable plan for event
                        if "I+" in cycle:
                            intention_id = cycle["I+"]
                            intention = data.intentions[intention_id]
                            intention.events.append(event)
                    for im in ims_added_this_cycle:
                        im.event = event
                        if event.parent:
                            im.parent = event.parent
                            event.parent.children.append(im)
                if "B+" in cycle:
                    for belief in cycle["B+"]:
                        data.beliefs.append(BeliefChange(cycle["nr"], True, belief))
                if "B-" in cycle:
                    for belief in cycle["B-"]:
                        data.beliefs.append(BeliefChange(cycle["nr"], False, belief))
                # TODO parse and put unifier somewhere
        return data
