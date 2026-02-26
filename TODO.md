# Mindweaver TODO List

Based on the project's roadmap and constitution, here are the features that need to be developed next, organized by expected release version:

## Version 0.1: Data Platform Orchestration
Focus on Data Platform deployment orchestration capabilities. Establish a robust foundation for deploying dependency components.

- [ ] **Kubernetes Clusters**: Develop backend services (`k8s_cluster.py`) and frontend UI to manage Kubernetes clusters and their kubeconfig.
- [ ] **Kafka Deployment**: Add backend service (`kafka.py`), Kubernetes manifest templates, and frontend UI (`KafkaPage.jsx`).
- [ ] **Trino Deployment**: Add backend service (`trino.py`), Kubernetes manifest templates, and frontend UI (`TrinoPage.jsx`).
- [ ] **Airflow Deployment**: Add backend service (`airflow.py`), Kubernetes manifest templates, and frontend UI (`AirflowPage.jsx`).
- [ ] **Superset Deployment**: Add backend service (`superset.py`), Kubernetes manifest templates, and frontend UI (`SupersetPage.jsx`).

## Version 0.2: Data Ingestion Support
Focus on providing capabilities to ingest data into the platform.

- [ ] **Ingestion Jobs**: Develop the frontend UI for `ingestion.py` to manage, execute, and schedule data ingestion jobs.

## Version 0.3: RAG Support
Focus on providing Retrieval-Augmented Generation capabilities.

- [ ] **AI Model API Connections**: Develop frontend UI/pages for managing AI model API connections (e.g., Gemini, OpenAI).
- [ ] **Knowledge Bases**: Develop the frontend UI (`KnowledgeBasesPage.jsx`) to manage knowledge bases for AI agents.
- [ ] **AI Agents**: Develop the frontend UI (`AIAgentsPage.jsx`) to interface with `ai_agent.py` and assign knowledge bases to agents.
- [ ] **SQL RAG**: Implement SQL RAG with Trino integration.
- [ ] **GraphRAG Platform**: Add comprehensive support for GraphRAG and ontology management.

## Version 0.4: Data Vault Support
Focus on advanced modeling capabilities.

- [ ] **Data Vault Modeling**: Introduce Data Vault modeling capabilities and support.

## Future Plans (Version TBD)
- [ ] **AI Visualization**: Develop an AI-powered dashboard and visualization creation tool.

---

### Technical Debt / Refinement (Ongoing)
- [ ] Ensure all new React pages strictly use the `DynamicForm` and custom providers as defined in the frontend standards.
- [ ] Validate that all new backend API endpoints correctly implement the JSON:API 1.1 specification and error formats.
- [ ] Develop comprehensive `pytest` coverage for newly added backend services before frontend implementation (TDD). 
