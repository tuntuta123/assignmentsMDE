from concrete_syntax.common import indent
from framework.conformance import Conformance, render_conformance_check_result
from util.simulator import MinimalSimulator, InteractiveDecisionMaker


class KitchenSimulator(MinimalSimulator):
    def __init__(self, action_generator, termination_condition, renderer,
                 decision_maker=InteractiveDecisionMaker(), check_conformance=True, verbose=True):
        super().__init__(action_generator=action_generator, decision_maker=decision_maker,
                         termination_condition=lambda od: self.check_render_termination_condition(od), verbose=verbose)
        self.check_conformance = check_conformance
        self.renderer = renderer
        self.model_termination_condition = termination_condition

    def check_render_termination_condition(self, od):
        """
            A termination condition checker that also renders the model, and performs conformance check
        """
        self._print("--------------")
        self._print(indent(self.renderer(od), 2))
        self._print("--------------")
        if self.check_conformance:
            conf = Conformance(od.state, od.m, od.mm)
            self._print(render_conformance_check_result(conf.check_nominal()))
            self._print()
        return self.model_termination_condition(od)
