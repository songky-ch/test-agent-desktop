from dataclasses import dataclass, field
from typing import Callable, Optional

from app.agent.model_generation import ModelGenerationService
from app.agent.orchestrator import AgentOrchestrator
from app.models.entities import RequirementContext, TestCase, TestPoint


@dataclass
class WorkflowState:
    requirement: RequirementContext
    use_rag: bool = True
    executed_nodes: list[str] = field(default_factory=list)
    test_points: list[TestPoint] = field(default_factory=list)
    test_cases: list[TestCase] = field(default_factory=list)


class AgentWorkflow:
    def __init__(
        self,
        retrieve_context: Callable[[str], list[str]],
        orchestrator: Optional[AgentOrchestrator] = None,
        model_generation: Optional[ModelGenerationService] = None,
    ):
        self.retrieve_context = retrieve_context
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.model_generation = model_generation

    def run(self, state: WorkflowState) -> WorkflowState:
        if state.use_rag:
            state = self._retrieve_context(state)
        if self.model_generation:
            return self._generate_with_model(state)
        state = self._generate_test_points(state)
        return self._generate_test_cases(state)

    def _generate_with_model(self, state: WorkflowState) -> WorkflowState:
        state.test_points = self.model_generation.generate_test_points(state.requirement)
        state.executed_nodes.append("generate_test_points_with_model")
        return state

    def _retrieve_context(self, state: WorkflowState) -> WorkflowState:
        query = state.requirement.markdown + "\n" + state.requirement.supplemental
        state.requirement.rag_context.extend(self.retrieve_context(query))
        state.executed_nodes.append("retrieve_context")
        return state

    def _generate_test_points(self, state: WorkflowState) -> WorkflowState:
        state.test_points = self.orchestrator.generate_test_points(state.requirement)
        state.executed_nodes.append("generate_test_points")
        return state

    def _generate_test_cases(self, state: WorkflowState) -> WorkflowState:
        state.test_cases = self.orchestrator.generate_test_cases(state.test_points)
        state.executed_nodes.append("generate_test_cases")
        return state
