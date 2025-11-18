import reflex as rx
from typing import TypedDict, Literal, Union, Optional
import uuid
import datetime
import asyncio
import logging
from mindweaver_fe.states.knowledge_db_state import KnowledgeDB, KnowledgeDBState

SourceType = Literal["API", "Database", "File Upload", "Web Scraper"]
SourceStatus = Literal["Connected", "Disconnected", "Error"]
ImportStatus = Literal["Running", "Completed", "Failed"]

class APIConfig(TypedDict):
    base_url: str
    api_key: str


class DBConfig(TypedDict):
    host: str
    port: int
    username: str


class WebScraperConfig(TypedDict):
    start_url: str


class FileUploadConfig(TypedDict):
    pass


class DataSourceFormData(TypedDict):
    name: str
    source_type: SourceType
    config: Union[APIConfig, DBConfig, WebScraperConfig, FileUploadConfig]


class DataSource(TypedDict):
    id: str
    name: str
    source_type: SourceType
    config: dict
    status: SourceStatus
    last_sync: str
    created_at: str


class ImportJob(TypedDict):
    id: str
    source_id: str
    kb_id: str
    status: ImportStatus
    records_imported: int
    started_at: str
    completed_at: str


class DataSourcesState(rx.State):
    """Manages the state for the data sources page."""

    all_sources: list[DataSource] = []
    import_jobs: list[ImportJob] = []
    all_knowledge_dbs: list[KnowledgeDB] = []
    show_source_modal: bool = False
    show_delete_dialog: bool = False
    show_import_dialog: bool = False
    is_editing: bool = False
    source_to_edit: DataSource | None = None
    source_to_delete: DataSource | None = None
    source_to_import: DataSource | None = None
    form_data: DataSourceFormData = {
        "name": "asdf",
        "source_type": "API",
        "config": {"base_url": "http://www.google.com", "api_key": "..."},
    }
    form_errors: dict = {}
    search_query: str = ""
    filter_type: str = "All"
    source_type_options: list[str] = ["API", "Database", "File Upload", "Web Scraper"]
    filter_type_options: list[str] = ["All"] + source_type_options
    is_testing_connection: bool = False
    is_importing: bool = False
    import_kb_id: str = ""

    def _get_default_form_data(
        self, source_type: SourceType = "API"
    ) -> DataSourceFormData:
        config: Union[APIConfig, DBConfig, WebScraperConfig, FileUploadConfig]
        if source_type == "API":
            config = {"base_url": "http://www.google.com", "api_key": "asfsadfsadf"}
        elif source_type == "Database":
            config = {"host": "192.168.0.1", "port": 5432, "username": "asd"}
        elif source_type == "Web Scraper":
            config = {"start_url": "http://www.google.com"}
        else:
            config = {}
        return {"name": "", "source_type": source_type, "config": config}
    
    @rx.event
    async def set_search_query(self, value):
        self.search_query = value

    @rx.event
    async def set_filter_type(self, value):
        self.filter_type = value

    @rx.event
    async def load_initial_data(self):
        """Load knowledge bases and mock data on page mount."""
        kdb_state = await self.get_state(KnowledgeDBState)
        self.all_knowledge_dbs = kdb_state.all_databases
        if not self.all_sources:
            self.all_sources = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Stripe Prod API",
                    "source_type": "API",
                    "config": {"base_url": "https://api.stripe.com", "api_key": "..."},
                    "status": "Connected",
                    "last_sync": "2 hours ago",
                    "created_at": "2023-11-01",
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Main Postgres DB",
                    "source_type": "Database",
                    "config": {
                        "host": "db.prod.internal",
                        "port": 5432,
                        "username": "readonly",
                    },
                    "status": "Connected",
                    "last_sync": "1 day ago",
                    "created_at": "2023-10-15",
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Failing Scraper",
                    "source_type": "Web Scraper",
                    "config": {"start_url": "https://broken-site.com"},
                    "status": "Error",
                    "last_sync": "3 days ago",
                    "created_at": "2023-10-28",
                },
            ]

    @rx.var
    def filtered_sources(self) -> list[DataSource]:
        return [
            source
            for source in self.all_sources
            if self.search_query.lower() in source["name"].lower()
            and (self.filter_type == "All" or source["source_type"] == self.filter_type)
        ]

    @rx.var
    def sorted_import_jobs(self) -> list[ImportJob]:
        return sorted(
            self.import_jobs, key=lambda job: job.get("completed_at", ""), reverse=True
        )

    @rx.var
    def source_names(self) -> dict[str, str]:
        return {s["id"]: s["name"] for s in self.all_sources}

    @rx.var
    def kb_names(self) -> dict[str, str]:
        return {db["id"]: db["name"] for db in self.all_knowledge_dbs}

    @rx.event
    def open_create_modal(self):
        self.is_editing = False
        self.form_data = self._get_default_form_data()
        self.form_errors = {}
        self.show_source_modal = True

    @rx.event
    def open_edit_modal(self, source: DataSource):
        self.is_editing = True
        self.source_to_edit = source
        self.form_data = self._get_default_form_data(source["source_type"])
        self.form_data["name"] = source["name"]
        self.form_data["source_type"] = source["source_type"]
        for key in self.form_data["config"]:
            if key in source["config"]:
                self.form_data["config"][key] = source["config"][key]
        self.form_errors = {}
        self.show_source_modal = True

    @rx.event
    def close_source_modal(self):
        self.show_source_modal = False
        self.source_to_edit = None
        self.form_errors = {}

    @rx.event
    def set_form_data_field(self, field: str, value: str):
        if field == "source_type":
            self.form_data = self._get_default_form_data(value)
            self.form_data["name"] = self.form_data.get("name", "")
        else:
            self.form_data[field] = value

    @rx.event
    def handle_submit(self, form_data: dict):
        submitted_name = form_data.get("name", "")
        if not submitted_name.strip():
            self.form_errors = {"name": "Name is required."}
            return
        self.form_errors = {}
        config = {}
        for k, v in form_data.items():
            if k.startswith("config."):
                key = k.split(".")[-1]
                if key == "port":
                    try:
                        config[key] = int(v)
                    except (ValueError, TypeError) as e:
                        logging.exception(f"Error converting port to int: {e}")
                        config[key] = 0
                else:
                    config[key] = v
        current_form_data = self.form_data.copy()
        current_form_data["name"] = submitted_name
        current_form_data["config"] = {**current_form_data["config"], **config}
        if self.is_editing and self.source_to_edit:
            index = next(
                (
                    i
                    for i, s in enumerate(self.all_sources)
                    if s["id"] == self.source_to_edit["id"]
                ),
                -1,
            )
            if index != -1:
                self.all_sources[index]["name"] = current_form_data["name"]
                self.all_sources[index]["config"] = current_form_data["config"]
        else:
            new_source: DataSource = {
                "id": str(uuid.uuid4()),
                "name": current_form_data["name"],
                "source_type": current_form_data["source_type"],
                "config": current_form_data["config"],
                "status": "Disconnected",
                "last_sync": "Never",
                "created_at": datetime.date.today().isoformat(),
            }
            self.all_sources.append(new_source)
        return DataSourcesState.close_source_modal

    @rx.event
    def open_delete_dialog(self, source: DataSource):
        self.source_to_delete = source
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.source_to_delete = None

    @rx.event
    def confirm_delete(self):
        if self.source_to_delete:
            self.all_sources = [
                s for s in self.all_sources if s["id"] != self.source_to_delete["id"]
            ]
        return DataSourcesState.close_delete_dialog

    @rx.event
    async def test_connection(self):
        self.is_testing_connection = True
        yield
        await asyncio.sleep(2)
        self.is_testing_connection = False
        yield rx.toast("Connection test successful!", duration=3000)

    @rx.event
    def open_import_dialog(self, source: DataSource):
        self.source_to_import = source
        self.import_kb_id = ""
        self.show_import_dialog = True

    @rx.event
    def close_import_dialog(self):
        self.show_import_dialog = False
        self.source_to_import = None

    @rx.event
    def set_import_kb_id(self, kb_id: str):
        self.import_kb_id = kb_id

    @rx.event(background=True)
    async def start_import(self):
        if not self.import_kb_id or not self.source_to_import:
            return
        async with self:
            self.is_importing = True
            job_id = str(uuid.uuid4())
            new_job: ImportJob = {
                "id": job_id,
                "source_id": self.source_to_import["id"],
                "kb_id": self.import_kb_id,
                "status": "Running",
                "records_imported": 0,
                "started_at": datetime.datetime.now().isoformat(),
                "completed_at": "",
            }
            self.import_jobs.insert(0, new_job)
        yield DataSourcesState.close_import_dialog
        records_to_import = 1000
        for i in range(records_to_import // 100):
            await asyncio.sleep(0.5)
            async with self:
                job_index = next(
                    (i for i, j in enumerate(self.import_jobs) if j["id"] == job_id), -1
                )
                if job_index != -1:
                    self.import_jobs[job_index]["records_imported"] += 100
            yield
        async with self:
            job_index = next(
                (i for i, j in enumerate(self.import_jobs) if j["id"] == job_id), -1
            )
            if job_index != -1:
                self.import_jobs[job_index]["status"] = "Completed"
                self.import_jobs[job_index]["completed_at"] = (
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                )
            self.is_importing = False