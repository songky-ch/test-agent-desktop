from typing import Callable, Optional

from app.agent.model_generation import ModelGenerationService
from app.agent.orchestrator import AgentOrchestrator
from app.agent.workflow import AgentWorkflow, WorkflowState


class LangGraphUnavailableError(RuntimeError):
    pass


class LangGraphAgentWorkflow(AgentWorkflow):
    def __init__(
        self,
        retrieve_context: Callable[[str], list[str]],
        orchestrator: Optional[AgentOrchestrator] = None,
        model_generation: Optional[ModelGenerationService] = None,
    ):
        super().__init__(retrieve_context, orchestrator, model_generation)
        self.graph = self._build_graph()

    def run(self, state: WorkflowState) -> WorkflowState:
        return self.graph.invoke(state)

    def _build_graph(self):
        try:
            from langgraph.graph import END, StateGraph
        except Exception as exc:
            raise LangGraphUnavailableError("请先安装 P8 可选依赖: python -m pip install -e '.[p8]'") from exc

        graph = StateGraph(WorkflowState)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("generate_with_model", self._generate_with_model)
        graph.add_node("generate_test_points", self._generate_test_points)
        graph.add_node("generate_test_cases", self._generate_test_cases)
        graph.set_entry_point("retrieve_context")
        if self.model_generation:
            graph.add_edge("retrieve_context", "generate_with_model")
            graph.add_edge("generate_with_model", END)
        else:
            graph.add_edge("retrieve_context", "generate_test_points")
            graph.add_edge("generate_test_points", "generate_test_cases")
            graph.add_edge("generate_test_cases", END)
        return graph.compile()
