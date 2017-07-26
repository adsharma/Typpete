from copy import deepcopy
from typing import List, Set

from abstract_domains.stack import Stack
from abstract_domains.state import State
from abstract_domains.usage.store import UsedStore
from core.expressions import Expression, VariableIdentifier


class UsedStack(Stack, State):
    def __init__(self, variables: List[VariableIdentifier]):
        """Usage-analysis state representation.

        :param variables: list of program variables
        """
        super().__init__(UsedStore, {'variables': variables})
        self._postponed_pushpop = []  # postponed stack pushs/pops that are later executed in ``_assume()``

    def push(self):
        if self.is_bottom():
            return self
        self.stack.append(deepcopy(self.stack[-1]).descend())
        return self

    def pop(self):
        if self.is_bottom():
            return self
        popped = self.stack.pop()
        self.stack[-1].combine(popped)
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        self.stack[-1].access_variable(variable)
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'UsedStack':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'UsedStack':
        # only update used variable in conditional edge via assume call to store
        # if we are on a loop/if exit edge!!
        if self._postponed_pushpop:
            self.stack[-1].assume({condition})

        # make good for postponed push/pop, since that was postponed until assume has been applied to top frame
        # (the engine implements a different order of calls to exit_if/exit_loop and assume than we want)
        for pushpop in self._postponed_pushpop:
            pushpop()
        self._postponed_pushpop.clear()

        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        self.stack[-1].evaluate_literal(literal)
        return {literal}

    def _postponed_exit_if(self):
        if self.is_bottom():
            return self
        self.pop()
        return self

    def enter_loop(self):
        return self.enter_if()

    def exit_loop(self):
        return self.exit_if()

    def enter_if(self):
        if self.is_bottom():
            return self
        self.push()
        return self

    def exit_if(self):
        self._postponed_pushpop.append(self._postponed_exit_if)
        return self

    def _output(self, output: Expression) -> 'UsedStack':
        if self.is_bottom():
            return self
        self.stack[-1].output({output})
        return self

    def _substitute_variable(self, left: Expression, right: Expression) -> 'UsedStack':
        if isinstance(left, VariableIdentifier):
            self.stack[-1].substitute_variable({left}, {right})  # TODO correct to use non-underscore interface???
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self
