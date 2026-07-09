from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MarkdownDocument:
    source_path: Path
    markdown_path: Path
    content: str


@dataclass(frozen=True)
class RequirementContext:
    markdown: str
    supplemental: str = ""
    rag_context: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TestPoint:
    module: str
    function: str
    positive_scenarios: list[str] = field(default_factory=list)
    negative_scenarios: list[str] = field(default_factory=list)
    boundary_scenarios: list[str] = field(default_factory=list)
    exception_scenarios: list[str] = field(default_factory=list)
    data_checks: list[str] = field(default_factory=list)
    permission_checks: list[str] = field(default_factory=list)
    compatibility_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TestCase:
    case_id: str
    module: str
    function: str
    precondition: str
    steps: list[str]
    expected_results: list[str]
    priority: str
    case_type: str
    remark: str = ""


@dataclass(frozen=True)
class CaseTemplate:
    fields: list[str]


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    entry: str
    prompt: str
    path: Path


@dataclass(frozen=True)
class ConnectionTestResult:
    ok: bool
    message: str
