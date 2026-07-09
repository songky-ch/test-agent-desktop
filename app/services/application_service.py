from pathlib import Path
from typing import Optional

from app.agent.llm_provider import LlmMessage, ModelRouter, OllamaAdapter, UrlLibHttpClient
from app.agent.model_generation import ModelGenerationService
from app.agent.orchestrator import AgentOrchestrator
from app.agent.workflow import AgentWorkflow, WorkflowState
from app.config.config_manager import ConfigManager, ModelConfig
from app.documents.pipeline import DocumentPipeline
from app.models.entities import CaseTemplate, ConnectionTestResult, MarkdownDocument, RequirementContext, TestCase, TestPoint
from app.rag.embeddings import OllamaEmbeddingAdapter
from app.rag.engine import RagEngine
from app.services.export_service import CASE_FIELD_KEYS_BY_LABEL, DEFAULT_CASE_TEMPLATE, ExportService
from app.services.result_store import ResultStore
from app.skills.runtime import SkillRuntime


class ApplicationService:
    def __init__(self, root_dir: Path, http_client=None):
        self.root_dir = Path(root_dir)
        self.http_client = http_client
        self.config = ConfigManager(self.root_dir / "data" / "config" / "model.json")
        self.documents = DocumentPipeline(self.root_dir / "data" / "markdown")
        self.rag = RagEngine(self.root_dir / "data" / "knowledge")
        self.agent = AgentOrchestrator()
        self.workflow = AgentWorkflow(self.rag.retrieve, self.agent)
        self.skills = SkillRuntime(self.root_dir / "skills")
        self.export = ExportService(self.root_dir / "data" / "outputs")
        self.results = ResultStore(self.root_dir / "data" / "outputs" / "runs")
        self.current_markdown: Optional[MarkdownDocument] = None
        self.current_points: list[TestPoint] = []
        self.current_cases: list[TestCase] = []
        self.case_template = DEFAULT_CASE_TEMPLATE
        self.executed_nodes: list[str] = []

    def load_model_config(self) -> ModelConfig:
        return self.config.load_model_config()

    def save_model_config(self, config: ModelConfig) -> None:
        self.config.save_model_config(config)

    def list_ollama_models(self) -> list[str]:
        return OllamaAdapter(ModelConfig(source="ollama")).list_models()

    def convert_document(self, source_path: Path) -> MarkdownDocument:
        self.current_markdown = self.documents.convert_to_markdown(source_path)
        return self.current_markdown

    def import_knowledge_document(self, source_path: Path):
        markdown = self.documents.convert_to_markdown(source_path)
        return self.rag.import_markdown(markdown.markdown_path)

    def rag_stats(self):
        return self.rag.stats()

    def configure_rag(
        self,
        top_k: int,
        similarity_threshold: float,
        embedding_model: str,
        use_vector: bool,
        vector_backend: str = "local",
        qdrant_url: str = "http://localhost:6333",
        qdrant_collection: str = "test_agent_desktop",
        embedding_adapter=None,
        qdrant_client=None,
    ) -> None:
        adapter = embedding_adapter
        if use_vector and adapter is None:
            adapter = OllamaEmbeddingAdapter(embedding_model, self.http_client or UrlLibHttpClient())
        self.rag.top_k = top_k
        self.rag.similarity_threshold = similarity_threshold
        self.rag.use_vector = use_vector
        self.rag.embedding_adapter = adapter
        self.rag.vector_backend = vector_backend
        self.rag.qdrant_url = qdrant_url
        self.rag.qdrant_collection = qdrant_collection
        self.rag.qdrant_client = qdrant_client
        self.rag.vector_index = self.rag._create_vector_index()

    def test_model_connection(self) -> ConnectionTestResult:
        config = self.load_model_config()
        try:
            if config.source == "ollama" and not config.ollama_model:
                return ConnectionTestResult(False, "未选择 Ollama 本地模型")
            if config.source == "openai_compatible" and not config.api_model:
                return ConnectionTestResult(False, "未配置 API 模型")
            router = ModelRouter(config, self.http_client)
            router.chat([LlmMessage(role="user", content="ping")])
        except Exception as exc:
            return ConnectionTestResult(False, f"连接失败: {exc}")
        return ConnectionTestResult(True, "连接成功")

    def generate_test_points(
        self,
        supplemental: str = "",
        use_rag: bool = True,
        use_model: bool = False,
    ) -> list[TestPoint]:
        markdown = self.current_markdown.content if self.current_markdown else ""
        workflow = self._workflow(use_model)
        state = workflow.run(
            WorkflowState(
                requirement=RequirementContext(markdown=markdown, supplemental=supplemental),
                use_rag=use_rag,
            )
        )
        self.current_points = state.test_points
        self.current_cases = state.test_cases
        self.executed_nodes = state.executed_nodes
        return self.current_points

    def generate_test_cases(self) -> list[TestCase]:
        if not self.current_cases:
            self.current_cases = self.agent.generate_test_cases(self.current_points)
        return self.current_cases

    def export_markdown(self) -> Path:
        return self.export.export_cases_markdown(self.current_cases)

    def export_cases(self, output_format: str) -> Path:
        if output_format == "excel":
            return self.export.export_cases_excel(self.current_cases, template=self.case_template)
        return self.export.export_cases_markdown(self.current_cases, template=self.case_template)

    def persist_current_run(self, run_id: str) -> Path:
        return self.results.save_run(run_id, self.current_points, self.current_cases)

    def sync_cases_from_rows(self, rows: list[dict]) -> list[TestCase]:
        cases = []
        for row in rows:
            cases.append(
                TestCase(
                    case_id=row.get("case_id", ""),
                    module=row.get("module", ""),
                    function=row.get("function", ""),
                    precondition=row.get("precondition", ""),
                    steps=self._split_lines(row.get("steps", "")),
                    expected_results=self._split_lines(row.get("expected_results", "")),
                    priority=row.get("priority", ""),
                    case_type=row.get("case_type", ""),
                    remark=row.get("remark", ""),
                )
            )
        self.current_cases = cases
        return self.current_cases

    def sync_points_from_rows(self, rows: list[dict]) -> list[TestPoint]:
        points = []
        for row in rows:
            points.append(
                TestPoint(
                    module=row.get("module", ""),
                    function=row.get("function", ""),
                    positive_scenarios=self._split_lines(row.get("positive_scenarios", "")),
                    negative_scenarios=self._split_lines(row.get("negative_scenarios", "")),
                    boundary_scenarios=self._split_lines(row.get("boundary_scenarios", "")),
                    exception_scenarios=self._split_lines(row.get("exception_scenarios", "")),
                    data_checks=self._split_lines(row.get("data_checks", "")),
                    permission_checks=self._split_lines(row.get("permission_checks", "")),
                    compatibility_notes=self._split_lines(row.get("compatibility_notes", "")),
                )
            )
        self.current_points = points
        self.current_cases = []
        return self.current_points

    def save_case_template(self, fields: list[str]) -> CaseTemplate:
        valid = []
        for field in fields:
            key = CASE_FIELD_KEYS_BY_LABEL.get(field, field)
            if key in DEFAULT_CASE_TEMPLATE.fields:
                valid.append(key)
        self.case_template = CaseTemplate(fields=valid or DEFAULT_CASE_TEMPLATE.fields)
        return self.case_template

    def _workflow(self, use_model: bool) -> AgentWorkflow:
        if not use_model:
            return self.workflow
        config = self.load_model_config()
        return AgentWorkflow(
            self.rag.retrieve,
            self.agent,
            ModelGenerationService(ModelRouter(config, self.http_client), self.case_template),
        )

    def _split_lines(self, value: str) -> list[str]:
        return [line.strip() for line in value.splitlines() if line.strip()]
