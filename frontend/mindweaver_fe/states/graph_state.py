#import reflex as rx
#from typing import TypedDict, Literal, Optional
#import random
#import math
#from mindweaver_fe.states.knowledge_db_state import KnowledgeDB, KnowledgeDBState
#
#NodeType = Literal["Entity", "Document", "User"]
#LayoutAlgorithm = Literal["force", "hierarchical", "radial"]
#
#
#class GraphNode(TypedDict):
#	id: str
#	label: str
#	type: NodeType
#	properties: dict[str, str]
#
#
#class GraphEdge(TypedDict):
#	source: str
#	target: str
#	label: str
#
#
#class GraphData(TypedDict):
#	nodes: list[GraphNode]
#	edges: list[GraphEdge]
#
#
#class GraphState(rx.State):
#	"""Manages the state for the Graph Explorer page."""
#
#	all_knowledge_dbs: list[KnowledgeDB] = []
#	selected_db_id: str = ""
#	graph_data: GraphData = {"nodes": [], "edges": []}
#	selected_node: Optional[GraphNode] = None
#	search_query: str = ""
#	filter_node_types: list[NodeType] = ["Entity", "Document", "User"]
#	layout_algorithm: LayoutAlgorithm = "force"
#	node_type_options: list[NodeType] = ["Entity", "Document", "User"]
#	layout_options: list[LayoutAlgorithm] = ["force", "hierarchical", "radial"]
#	node_type_colors: dict[NodeType, str] = {
#		"Entity": "#6366f1",
#		"Document": "#10b981",
#		"User": "#ec4899",
#	}
#
#	def _generate_mock_graph_data(self) -> GraphData:
#		"""Generates mock graph data for a given DB."""
#		nodes: list[GraphNode] = []
#		edges: list[GraphEdge] = []
#		entity_names = ["Reflex", "Python", "React", "AI", "Database"]
#		doc_titles = ["Getting Started", "API Reference", "Advanced Guide", "Tutorial"]
#		user_names = ["Alice", "Bob", "Charlie"]
#		for name in entity_names:
#			nodes.append(
#				{
#					"id": f"ent-{name.lower()}",
#					"label": name,
#					"type": "Entity",
#					"properties": {
#						"created_by": "system",
#						"verified": str(random.choice([True, False])),
#					},
#				}
#			)
#		for title in doc_titles:
#			nodes.append(
#				{
#					"id": f"doc-{title.replace(' ', '-').lower()}",
#					"label": title,
#					"type": "Document",
#					"properties": {
#						"version": f"1.{random.randint(0, 5)}",
#						"status": "published",
#					},
#				}
#			)
#		for name in user_names:
#			nodes.append(
#				{
#					"id": f"usr-{name.lower()}",
#					"label": name,
#					"type": "User",
#					"properties": {
#						"role": random.choice(["Admin", "Editor", "Viewer"])
#					},
#				}
#			)
#		edges.extend(
#			[
#				{
#					"source": "usr-alice",
#					"target": "doc-getting-started",
#					"label": "AUTHORED_BY",
#				},
#				{
#					"source": "usr-bob",
#					"target": "doc-api-reference",
#					"label": "AUTHORED_BY",
#				},
#				{
#					"source": "doc-getting-started",
#					"target": "ent-reflex",
#					"label": "MENTIONS",
#				},
#				{
#					"source": "doc-getting-started",
#					"target": "ent-python",
#					"label": "MENTIONS",
#				},
#				{
#					"source": "doc-api-reference",
#					"target": "ent-react",
#					"label": "REFERENCES",
#				},
#				{
#					"source": "doc-advanced-guide",
#					"target": "ent-ai",
#					"label": "REFERENCES",
#				},
#				{"source": "ent-reflex", "target": "ent-react", "label": "BASED_ON"},
#			]
#		)
#		return {"nodes": nodes, "edges": edges}
#
#	@rx.event
#	async def load_page_data(self):
#		"""Load databases and initial graph data."""
#		kdb_state = await self.get_state(KnowledgeDBState)
#		self.all_knowledge_dbs = kdb_state.all_databases
#		if self.all_knowledge_dbs:
#			self.selected_db_id = self.all_knowledge_dbs[0]["id"]
#			self.graph_data = self._generate_mock_graph_data()
#
#	@rx.event
#	def select_database(self, db_id: str):
#		"""Select a database and load its graph data."""
#		self.selected_db_id = db_id
#		self.graph_data = self._generate_mock_graph_data()
#		self.selected_node = None
#		self.search_query = ""
#
#	@rx.event
#	def select_node(self, node_id: str):
#		"""Select a node to display its details."""
#		for node in self.graph_data["nodes"]:
#			if node["id"] == node_id:
#				self.selected_node = node
#				return
#
#	@rx.event
#	def deselect_node(self):
#		"""Deselect the current node."""
#		self.selected_node = None
#
#	@rx.event
#	def toggle_node_type_filter(self, node_type: NodeType, checked: bool):
#		"""Toggle the filter for a specific node type."""
#		if checked:
#			if node_type not in self.filter_node_types:
#				self.filter_node_types.append(node_type)
#		elif node_type in self.filter_node_types:
#			self.filter_node_types.remove(node_type)
#
#	@rx.var
#	def filtered_graph_data(self) -> GraphData:
#		"""Return graph data filtered by node type and search query."""
#		nodes = self.graph_data["nodes"]
#		edges = self.graph_data["edges"]
#		filtered_nodes_by_type = [
#			node for node in nodes if node["type"] in self.filter_node_types
#		]
#		node_ids_by_type = {node["id"] for node in filtered_nodes_by_type}
#		final_nodes = [
#			node
#			for node in filtered_nodes_by_type
#			if self.search_query.lower() in node["label"].lower()
#		]
#		final_node_ids = {node["id"] for node in final_nodes}
#		final_edges = [
#			edge
#			for edge in edges
#			if edge["source"] in final_node_ids and edge["target"] in final_node_ids
#		]
#		return {"nodes": final_nodes, "edges": final_edges}
#
#	@rx.var
#	def flow_nodes(self) -> list[FlowNode]:
#		"""Transforms graph data into the format required by reflex-enterprise flow."""
#		nodes = self.filtered_graph_data["nodes"]
#		count = len(nodes)
#		if count == 0:
#			return []
#		radius = 200 * (1 + count // 10)
#		center_x, center_y = (400, 300)
#		flow_nodes: list[FlowNode] = []
#		for i, node in enumerate(nodes):
#			angle = i / count * 2 * math.pi
#			x = center_x + radius * math.cos(angle)
#			y = center_y + radius * math.sin(angle)
#			is_selected = self.selected_node and self.selected_node["id"] == node["id"]
#			flow_nodes.append(
#				{
#					"id": node["id"],
#					"position": {"x": x, "y": y},
#					"data": {"label": node["label"]},
#					"style": {
#						"background": self.node_type_colors.get(node["type"], "#ccc"),
#						"color": "white",
#						"borderRadius": "999px",
#						"padding": "10px 15px",
#						"border": f"2px solid {('#ff8c00' if is_selected else 'transparent')}",
#						"boxShadow": "0 2px 5px rgba(0,0,0,0.2)"
#						if is_selected
#						else "none",
#					},
#				}
#			)
#		return flow_nodes
#
#	@rx.var
#	def flow_edges(self) -> list[FlowEdge]:
#		"""Transforms graph edge data into the format required by reflex-enterprise flow."""
#		return [
#			{
#				"id": f"{edge['source']}-{edge['target']}-{edge['label']}",
#				"source": edge["source"],
#				"target": edge["target"],
#				"animated": True,
#				"label": edge["label"],
#				"style": {"strokeWidth": 2},
#			}
#			for edge in self.filtered_graph_data["edges"]
#		]
#
#	@rx.var
#	def total_nodes(self) -> int:
#		"""Total number of nodes in the current view."""
#		return len(self.filtered_graph_data["nodes"])
#
#	@rx.var
#	def total_edges(self) -> int:
#		"""Total number of edges in the current view."""
#		return len(self.filtered_graph_data["edges"])
#
#	@rx.var
#	def node_clusters(self) -> int:
#		"""Calculates the number of clusters (connected components)."""
#		if not self.filtered_graph_data["nodes"]:
#			return 0
#		adj = {node["id"]: [] for node in self.filtered_graph_data["nodes"]}
#		for edge in self.filtered_graph_data["edges"]:
#			adj[edge["source"]].append(edge["target"])
#			adj[edge["target"]].append(edge["source"])
#		visited = set()
#		clusters = 0
#		for node_id in adj:
#			if node_id not in visited:
#				clusters += 1
#				stack = [node_id]
#				while stack:
#					curr = stack.pop()
#					if curr not in visited:
#						visited.add(curr)
#						for neighbor in adj[curr]:
#							stack.append(neighbor)
#		return clusters
#
#	@rx.var
#	def selected_node_connections(self) -> list[dict[str, str]]:
#		"""Get connections for the selected node."""
#		if not self.selected_node:
#			return []
#		connections = []
#		node_map = {node["id"]: node for node in self.graph_data["nodes"]}
#		for edge in self.graph_data["edges"]:
#			if edge["source"] == self.selected_node["id"]:
#				target_node = node_map.get(edge["target"])
#				if target_node:
#					connections.append(
#						{
#							"relationship": edge["label"],
#							"target_label": target_node["label"],
#							"target_id": target_node["id"],
#						}
#					)
#			elif edge["target"] == self.selected_node["id"]:
#				source_node = node_map.get(edge["source"])
#				if source_node:
#					connections.append(
#						{
#							"relationship": edge["label"],
#							"target_label": source_node["label"],
#							"target_id": source_node["id"],
#						}
#					)
#		return connections