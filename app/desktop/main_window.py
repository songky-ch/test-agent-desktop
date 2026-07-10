from pathlib import Path
import json

from app.config.config_manager import ModelConfig
from app.services.application_service import ApplicationService

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QSplitter,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QApplication = None
    QMainWindow = object


class MainWindow(QMainWindow):
    def __init__(self, root_dir: Path):
        super().__init__()
        if QApplication is None:
            raise RuntimeError("PySide6 is required to start the desktop UI")
        self.service = ApplicationService(root_dir)
        self.uploaded_files = QListWidget()
        self.markdown_preview = QPlainTextEdit()
        self.points_table = QTableWidget(0, 9)
        self.cases_table = QTableWidget(0, 9)
        self.supplemental_input = QPlainTextEdit()
        self.rag_enabled = QCheckBox("启用检索")
        self.rag_enabled.setChecked(True)
        self.vector_rag_enabled = QCheckBox("启用向量检索")
        self.vector_backend = QComboBox()
        self.vector_backend.addItems(["本地 JSON", "Qdrant"])
        self.rag_top_k = QLineEdit("5")
        self.rag_similarity_threshold = QLineEdit("0.30")
        self.embedding_model = QLineEdit("nomic-embed-text")
        self.qdrant_url = QLineEdit("http://localhost:6333")
        self.qdrant_collection = QLineEdit("test_agent_desktop")
        self.model_generation_enabled = QCheckBox("使用模型生成")
        self.model_generation_enabled.setChecked(True)
        self.status_label = QLabel("模型状态: 未测试")
        self.rag_documents = QListWidget()
        self.rag_stats_label = QLabel("知识库统计\n文档数量: 0\n分块数量: 0\n索引路径: -")
        self.skill_selector = QComboBox()
        self.skill_result = QPlainTextEdit()
        self._build_window()
        self._load_config()

    def _build_window(self) -> None:
        self.setWindowTitle("Test Agent Desktop")
        self.resize(1280, 760)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addLayout(self._top_bar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._nav_panel())
        splitter.addWidget(self._workspace_panel())
        splitter.addWidget(self._rag_panel())
        splitter.setSizes([160, 820, 260])
        layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _top_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        title = QLabel("Test Agent Desktop")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        project = QLabel("当前项目: 本地测试项目")
        layout.addWidget(title)
        layout.addSpacing(24)
        layout.addWidget(project)
        layout.addStretch()
        layout.addWidget(self.status_label)
        return layout

    def _nav_panel(self) -> QWidget:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        for item in ["项目工作区", "需求文档", "知识库", "Agent 任务", "Skills", "模型设置"]:
            button = QPushButton(item)
            button.setMinimumHeight(36)
            layout.addWidget(button)
        layout.addStretch()
        layout.addWidget(QLabel("tester_admin\n角色: 测试工程师"))
        return panel

    def _workspace_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        top = QHBoxLayout()
        top.addWidget(self._upload_panel(), 2)
        top.addWidget(self._model_panel(), 1)
        layout.addLayout(top)
        layout.addWidget(self._supplemental_panel())
        layout.addWidget(self._output_tabs(), 1)
        layout.addWidget(self._skill_panel())
        return panel

    def _upload_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        upload = QPushButton("选择需求文档 (DOCX/PDF/MD/TXT/XLSX)")
        remove = QPushButton("移除选中文档")
        upload.clicked.connect(self._select_document)
        remove.clicked.connect(self._remove_selected_document)
        layout.addWidget(QLabel("文档上传区"))
        layout.addWidget(upload)
        layout.addWidget(remove)
        layout.addWidget(self.uploaded_files)
        return panel

    def _model_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        form = QFormLayout(panel)
        self.source = QComboBox()
        self.source.addItems(["Ollama", "OpenAI-compatible"])
        self.source.currentTextChanged.connect(self._update_model_source_view)
        self.ollama_model = QComboBox()
        self.refresh_ollama = QPushButton("刷新本地模型")
        self.refresh_ollama.clicked.connect(self._refresh_ollama_models)
        self.api_base_url = QLineEdit()
        self.api_model = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.ollama_model_label = QLabel("本地模型")
        self.ollama_refresh_label = QLabel("")
        self.api_base_url_label = QLabel("Base URL")
        self.api_model_label = QLabel("Model")
        self.api_key_label = QLabel("API Key")
        save = QPushButton("保存配置")
        test = QPushButton("测试连接")
        save.clicked.connect(self._save_config)
        test.clicked.connect(self._test_model_connection)
        form.addRow(QLabel("模型配置摘要"))
        form.addRow("模型来源", self.source)
        form.addRow(self.ollama_model_label, self.ollama_model)
        form.addRow(self.ollama_refresh_label, self.refresh_ollama)
        form.addRow(self.api_base_url_label, self.api_base_url)
        form.addRow(self.api_model_label, self.api_model)
        form.addRow(self.api_key_label, self.api_key)
        form.addRow("", save)
        form.addRow("", test)
        return panel

    def _supplemental_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        self.supplemental_input.setPlaceholderText("输入补充业务规则、测试范围、边界条件、兼容性要求...")
        layout.addWidget(self.supplemental_input, 1)
        actions = QVBoxLayout()
        self.export_format = QComboBox()
        self.export_format.addItems(["Markdown", "Excel"])
        self.case_template_fields = QLineEdit()
        self.case_template_fields.setPlaceholderText("用例编号,所属模块,功能点,前置条件,测试步骤,预期结果,优先级,类型,备注")
        convert = QPushButton("转换 Markdown")
        points = QPushButton("拆解测试点")
        cases = QPushButton("生成测试用例")
        export = QPushButton("导出")
        convert.clicked.connect(self._convert_selected)
        points.clicked.connect(self._generate_points)
        cases.clicked.connect(self._generate_cases)
        export.clicked.connect(self._export_markdown)
        actions.addWidget(self.model_generation_enabled)
        actions.addWidget(self.export_format)
        actions.addWidget(self.case_template_fields)
        for button in [convert, points, cases, export]:
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        return panel

    def _output_tabs(self) -> QWidget:
        tabs = QTabWidget()
        self.markdown_preview.setReadOnly(True)
        point_headers = ["模块", "功能点", "正向场景", "反向场景", "边界场景", "异常场景", "数据校验", "权限校验", "兼容性"]
        self.points_table.setHorizontalHeaderLabels(point_headers)
        headers = ["用例编号", "所属模块", "功能点", "前置条件", "测试步骤", "预期结果", "优先级", "类型", "备注"]
        self.cases_table.setHorizontalHeaderLabels(headers)
        tabs.addTab(self.markdown_preview, "Markdown 预览")
        tabs.addTab(self.points_table, "功能测试点")
        tabs.addTab(self.cases_table, "测试用例")
        return tabs

    def _rag_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        import_doc = QPushButton("添加文档")
        remove_doc = QPushButton("移除选中文档")
        test_rag = QPushButton("测试 RAG")
        import_doc.clicked.connect(self._import_knowledge_document)
        remove_doc.clicked.connect(self._remove_knowledge_document)
        test_rag.clicked.connect(self._test_rag_connection)
        layout.addWidget(QLabel("RAG 知识库"))
        layout.addWidget(import_doc)
        layout.addWidget(remove_doc)
        layout.addWidget(self.rag_documents)
        layout.addWidget(self.rag_enabled)
        layout.addWidget(self.vector_rag_enabled)
        layout.addWidget(QLabel("向量库"))
        layout.addWidget(self.vector_backend)
        layout.addWidget(QLabel("Top-K"))
        layout.addWidget(self.rag_top_k)
        layout.addWidget(QLabel("相似度阈值"))
        layout.addWidget(self.rag_similarity_threshold)
        layout.addWidget(QLabel("Embedding 模型"))
        layout.addWidget(self.embedding_model)
        layout.addWidget(QLabel("Qdrant URL"))
        layout.addWidget(self.qdrant_url)
        layout.addWidget(QLabel("Qdrant Collection"))
        layout.addWidget(self.qdrant_collection)
        layout.addWidget(test_rag)
        layout.addStretch()
        layout.addWidget(self.rag_stats_label)
        return panel

    def _skill_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        refresh = QPushButton("刷新 Skills")
        run = QPushButton("执行 Skill")
        refresh.clicked.connect(self._refresh_skills)
        run.clicked.connect(self._run_selected_skill)
        self.skill_result.setReadOnly(True)
        layout.addWidget(QLabel("Skill"))
        layout.addWidget(self.skill_selector)
        layout.addWidget(refresh)
        layout.addWidget(run)
        layout.addWidget(self.skill_result, 1)
        return panel

    def _load_config(self) -> None:
        config = self.service.load_model_config()
        self._refresh_ollama_models()
        if config.ollama_model and self.ollama_model.findText(config.ollama_model) == -1:
            self.ollama_model.addItem(config.ollama_model)
        self.ollama_model.setCurrentText(config.ollama_model)
        self.api_base_url.setText(config.api_base_url)
        self.api_model.setText(config.api_model)
        self.api_key.setText(config.api_key)
        self.source.setCurrentText("Ollama" if config.source == "ollama" else "OpenAI-compatible")
        self._update_model_source_view(self.source.currentText())
        self.case_template_fields.setText("用例编号,所属模块,功能点,前置条件,测试步骤,预期结果,优先级,类型,备注")
        self._refresh_skills()

    def _save_config(self) -> None:
        if self.source.currentText() == "Ollama":
            config = ModelConfig(
                source="ollama",
                ollama_model=self.ollama_model.currentText(),
            )
        else:
            config = ModelConfig(
                source="openai_compatible",
                api_base_url=self.api_base_url.text(),
                api_key=self.api_key.text(),
                api_model=self.api_model.text(),
            )
        self.service.save_model_config(config)
        self.status_label.setText(f"模型状态: 已保存 ({config.display_name})")

    def _test_model_connection(self) -> None:
        self._save_config()
        result = self.service.test_model_connection()
        self.status_label.setText(f"模型状态: {result.message}")
        self._info(result.message)

    def _refresh_ollama_models(self) -> None:
        current = self.ollama_model.currentText()
        self.ollama_model.clear()
        models = self.service.list_ollama_models()
        self.ollama_model.addItems(models)
        if current and self.ollama_model.findText(current) != -1:
            self.ollama_model.setCurrentText(current)

    def _update_model_source_view(self, source: str) -> None:
        is_ollama = source == "Ollama"
        self.ollama_model_label.setVisible(is_ollama)
        self.ollama_model.setVisible(is_ollama)
        self.ollama_refresh_label.setVisible(is_ollama)
        self.refresh_ollama.setVisible(is_ollama)
        self.api_base_url_label.setVisible(not is_ollama)
        self.api_base_url.setVisible(not is_ollama)
        self.api_model_label.setVisible(not is_ollama)
        self.api_model.setVisible(not is_ollama)
        self.api_key_label.setVisible(not is_ollama)
        self.api_key.setVisible(not is_ollama)

    def _select_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择需求文档",
            str(self.service.root_dir),
            "Documents (*.docx *.pdf *.md *.txt *.xlsx)",
        )
        if path:
            self.uploaded_files.addItem(path)

    def _remove_selected_document(self) -> None:
        row = self.uploaded_files.currentRow()
        if row < 0:
            self._info("请先选择要移除的文档")
            return
        self.uploaded_files.takeItem(row)

    def _convert_selected(self) -> None:
        item = self.uploaded_files.currentItem()
        if item is None:
            self._info("请先选择一个需求文档")
            return
        document = self.service.convert_document(Path(item.text()))
        self.markdown_preview.setPlainText(document.content)

    def _import_knowledge_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择知识库文档",
            str(self.service.root_dir),
            "Documents (*.docx *.pdf *.md *.txt *.xlsx)",
        )
        if not path:
            return
        self._apply_rag_settings()
        try:
            stats = self.service.import_knowledge_document(Path(path))
        except Exception as exc:
            self._info(str(exc))
            return
        self.rag_documents.addItem(path)
        self._refresh_rag_stats()
        self._info(f"知识库已导入, 分块数量: {stats.chunk_count}, 向量数量: {stats.vector_count}")

    def _remove_knowledge_document(self) -> None:
        item = self.rag_documents.currentItem()
        if item is None:
            self._info("请先选择要移除的知识库文档")
            return
        try:
            stats = self.service.remove_knowledge_document(Path(item.text()).name)
        except Exception as exc:
            self._info(str(exc))
            return
        self.rag_documents.takeItem(self.rag_documents.currentRow())
        self._refresh_rag_stats()
        self._info(f"知识库文档已移除, 当前文档数量: {stats.document_count}")

    def _test_rag_connection(self) -> None:
        self._apply_rag_settings()
        result = self.service.test_rag_connection()
        self._info(result.message)

    def _refresh_rag_stats(self) -> None:
        stats = self.service.rag_stats()
        self.rag_stats_label.setText(
            "知识库统计\n"
            f"文档数量: {stats.document_count}\n"
            f"分块数量: {stats.chunk_count}\n"
            f"向量数量: {stats.vector_count}\n"
            f"索引路径: {stats.index_path}"
        )

    def _generate_points(self) -> None:
        if self.model_generation_enabled.isChecked():
            self._save_config()
        self._save_case_template()
        self._apply_rag_settings()
        try:
            points = self.service.generate_test_points(
                self.supplemental_input.toPlainText(),
                self.rag_enabled.isChecked(),
                self.model_generation_enabled.isChecked(),
            )
        except Exception as exc:
            self._info(str(exc))
            return
        self.points_table.setRowCount(len(points))
        for row, point in enumerate(points):
            values = [
                point.module,
                point.function,
                "\n".join(point.positive_scenarios),
                "\n".join(point.negative_scenarios),
                "\n".join(point.boundary_scenarios),
                "\n".join(point.exception_scenarios),
                "\n".join(point.data_checks),
                "\n".join(point.permission_checks),
                "\n".join(point.compatibility_notes),
            ]
            for column, value in enumerate(values):
                self.points_table.setItem(row, column, QTableWidgetItem(value))

    def _generate_cases(self) -> None:
        if not self.service.current_points:
            self._generate_points()
            if not self.service.current_points:
                return
        self._save_case_template()
        self._sync_points_from_table()
        cases = self.service.generate_test_cases()
        self.cases_table.setRowCount(len(cases))
        for row, case in enumerate(cases):
            values = [
                case.case_id,
                case.module,
                case.function,
                case.precondition,
                "\n".join(case.steps),
                "\n".join(case.expected_results),
                case.priority,
                case.case_type,
                case.remark,
            ]
            for column, value in enumerate(values):
                self.cases_table.setItem(row, column, QTableWidgetItem(value))
        self.service.persist_current_run("latest")

    def _export_markdown(self) -> None:
        self._save_case_template()
        self._sync_cases_from_table()
        output_format = "excel" if self.export_format.currentText() == "Excel" else "markdown"
        path = self.service.export_cases(output_format)
        self._info(f"已导出: {path}")

    def _save_case_template(self) -> None:
        fields = [field.strip() for field in self.case_template_fields.text().split(",") if field.strip()]
        self.service.save_case_template(fields)

    def _sync_points_from_table(self) -> None:
        headers = [
            "module",
            "function",
            "positive_scenarios",
            "negative_scenarios",
            "boundary_scenarios",
            "exception_scenarios",
            "data_checks",
            "permission_checks",
            "compatibility_notes",
        ]
        rows = []
        for row in range(self.points_table.rowCount()):
            item = {}
            for column, key in enumerate(headers):
                cell = self.points_table.item(row, column)
                item[key] = cell.text() if cell else ""
            rows.append(item)
        self.service.sync_points_from_rows(rows)

    def _apply_rag_settings(self) -> None:
        self.service.configure_rag(
            top_k=self._int_value(self.rag_top_k.text(), 5),
            similarity_threshold=self._float_value(self.rag_similarity_threshold.text(), 0.3),
            embedding_model=self.embedding_model.text() or "nomic-embed-text",
            use_vector=self.vector_rag_enabled.isChecked(),
            vector_backend="qdrant" if self.vector_backend.currentText() == "Qdrant" else "local",
            qdrant_url=self.qdrant_url.text() or "http://localhost:6333",
            qdrant_collection=self.qdrant_collection.text() or "test_agent_desktop",
            project_id=self.service.root_dir.name or "default",
        )

    def _int_value(self, value: str, fallback: int) -> int:
        try:
            return int(value)
        except ValueError:
            return fallback

    def _float_value(self, value: str, fallback: float) -> float:
        try:
            return float(value)
        except ValueError:
            return fallback

    def _sync_cases_from_table(self) -> None:
        headers = [
            "case_id",
            "module",
            "function",
            "precondition",
            "steps",
            "expected_results",
            "priority",
            "case_type",
            "remark",
        ]
        rows = []
        for row in range(self.cases_table.rowCount()):
            item = {}
            for column, key in enumerate(headers):
                cell = self.cases_table.item(row, column)
                item[key] = cell.text() if cell else ""
            rows.append(item)
        self.service.sync_cases_from_rows(rows)

    def _refresh_skills(self) -> None:
        current = self.skill_selector.currentText()
        self.skill_selector.clear()
        for skill in self.service.list_skills():
            self.skill_selector.addItem(skill.name)
        if current and self.skill_selector.findText(current) != -1:
            self.skill_selector.setCurrentText(current)

    def _run_selected_skill(self) -> None:
        skill_name = self.skill_selector.currentText()
        if not skill_name:
            self._info("请先选择 Skill")
            return
        result = self.service.run_skill(skill_name, self._skill_payload())
        self.skill_result.setPlainText(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("ok"):
            self._info(f"Skill 已执行: {skill_name}")
        else:
            self._info(f"Skill 执行失败: {result.get('message', '')}")

    def _skill_payload(self) -> dict:
        return {
            "supplemental": self.supplemental_input.toPlainText(),
            "points": [
                {"module": point.module, "function": point.function}
                for point in self.service.current_points
            ],
            "cases": [
                {"case_id": case.case_id, "module": case.module, "function": case.function}
                for case in self.service.current_cases
            ],
            "items": [
                {"module": case.module, "title": case.function, "priority": case.priority}
                for case in self.service.current_cases
            ],
        }

    def _info(self, message: str) -> None:
        QMessageBox.information(self, "Test Agent Desktop", message)
