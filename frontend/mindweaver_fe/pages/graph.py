#import reflex as rx
#from mindweaver_fe.components.layout import base_layout
#from mindweaver_fe.components.reusables import card, base_button
#from mindweaver_fe.states.graph_state import GraphState, NodeType
#from mindweaver_fe.components.graph_explorer import graph_explorer_component
#
#
#def db_selector() -> rx.Component:
#	return rx.el.div(
#		rx.el.label(
#			"Knowledge Base", class_name="text-sm font-medium text-gray-700 mr-3"
#		),
#		rx.el.select(
#			rx.foreach(
#				GraphState.all_knowledge_dbs,
#				lambda db: rx.el.option(db["name"], value=db["id"]),
#			),
#			value=GraphState.selected_db_id,
#			on_change=GraphState.select_database,
#			class_name="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
#		),
#		class_name="flex items-center",
#	)
#
#
#def stats_panel() -> rx.Component:
#	def stat_item(icon: str, value: rx.Var, label: str) -> rx.Component:
#		return rx.el.div(
#			rx.icon(icon, class_name="h-5 w-5 text-gray-400"),
#			rx.el.div(
#				rx.el.span(value, class_name="text-lg font-bold text-gray-800"),
#				rx.el.span(label, class_name="text-xs text-gray-500"),
#				class_name="flex flex-col",
#			),
#			class_name="flex items-center gap-3",
#		)
#
#	return rx.el.div(
#		stat_item("circle-dot", GraphState.total_nodes, "Nodes"),
#		stat_item("arrow-right-left", GraphState.total_edges, "Edges"),
#		stat_item("network", GraphState.node_clusters, "Clusters"),
#		class_name="flex items-center gap-6 p-4 bg-white border border-gray-200 rounded-xl shadow-sm",
#	)
#
#
#def control_bar() -> rx.Component:
#	return rx.el.div(
#		rx.el.div(
#			rx.icon(
#				"search",
#				class_name="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400",
#			),
#			rx.el.input(
#				placeholder="Search nodes...",
#				on_change=GraphState.set_search_query,
#				class_name="w-full max-w-xs pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
#			),
#			class_name="relative",
#		),
#		rx.el.div(
#			rx.el.label(
#				"Filter by Type:", class_name="text-sm font-medium text-gray-700"
#			),
#			rx.el.div(
#				rx.foreach(
#					GraphState.node_type_options,
#					lambda type: rx.el.label(
#						rx.el.input(
#							type="checkbox",
#							checked=GraphState.filter_node_types.contains(type),
#							on_change=lambda checked: GraphState.toggle_node_type_filter(
#								type, checked
#							),
#							class_name="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500",
#						),
#						rx.el.span(type, class_name="ml-2 text-sm text-gray-600"),
#						class_name="flex items-center",
#					),
#				),
#				class_name="flex items-center gap-4",
#			),
#			class_name="flex items-center gap-3",
#		),
#		class_name="flex items-center justify-between w-full",
#	)
#
#
#def node_detail_panel() -> rx.Component:
#	return rx.el.div(
#		rx.cond(
#			GraphState.selected_node,
#			rx.el.div(
#				rx.el.div(
#					rx.el.h3(
#						"Node Details", class_name="text-lg font-semibold text-gray-800"
#					),
#					rx.el.button(
#						rx.icon("x", class_name="h-4 w-4"),
#						on_click=GraphState.deselect_node,
#						class_name="p-1 rounded-md hover:bg-gray-100",
#					),
#					class_name="flex justify-between items-center pb-3 border-b border-gray-200",
#				),
#				rx.el.div(
#					rx.el.div(
#						rx.el.span("Label:", class_name="font-medium text-gray-600"),
#						rx.el.span(
#							GraphState.selected_node["label"],
#							class_name="text-gray-800 bg-gray-100 px-2 py-0.5 rounded-md",
#						),
#						class_name="flex justify-between items-center text-sm",
#					),
#					rx.el.div(
#						rx.el.span("Type:", class_name="font-medium text-gray-600"),
#						rx.el.span(
#							GraphState.selected_node["type"], class_name="text-gray-800"
#						),
#						class_name="flex justify-between items-center text-sm mt-2",
#					),
#					rx.el.h4(
#						"Properties",
#						class_name="text-md font-semibold text-gray-700 mt-4 pt-4 border-t",
#					),
#					rx.foreach(
#						GraphState.selected_node["properties"].keys(),
#						lambda key: rx.el.div(
#							rx.el.span(key, class_name="capitalize text-gray-600"),
#							rx.el.span(
#								GraphState.selected_node["properties"][key],
#								class_name="text-gray-800",
#							),
#							class_name="flex justify-between text-xs mt-1",
#						),
#					),
#					rx.el.h4(
#						"Connections",
#						class_name="text-md font-semibold text-gray-700 mt-4 pt-4 border-t",
#					),
#					rx.el.div(
#						rx.foreach(
#							GraphState.selected_node_connections,
#							lambda conn: rx.el.div(
#								rx.el.span(
#									conn["relationship"],
#									class_name="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded",
#								),
#								rx.el.span("->", class_name="text-gray-400"),
#								rx.el.a(
#									conn["target_label"],
#									on_click=lambda: GraphState.select_node(
#										conn["target_id"]
#									),
#									class_name="text-orange-600 hover:underline cursor-pointer",
#								),
#								class_name="flex items-center gap-2 text-sm mt-1",
#							),
#						),
#						class_name="overflow-y-auto max-h-48",
#					),
#					class_name="space-y-2 mt-4",
#				),
#				class_name="p-4",
#			),
#			rx.el.div(
#				rx.icon("info", class_name="h-8 w-8 text-gray-400"),
#				rx.el.p(
#					"Select a node to see its details.",
#					class_name="text-sm text-gray-500 mt-2",
#				),
#				class_name="flex flex-col items-center justify-center h-full text-center p-4",
#			),
#		),
#		class_name="bg-white border-l border-gray-200 w-80 shrink-0 h-full overflow-y-auto",
#	)
#
#
#def graph_page() -> rx.Component:
#	"""The Graph Explorer page content."""
#	return base_layout(
#		rx.el.div(
#			rx.el.div(
#				rx.el.div(
#					db_selector(),
#					stats_panel(),
#					class_name="flex items-center justify-between w-full mb-4",
#				),
#				control_bar(),
#				class_name="p-6 bg-white border border-gray-200 rounded-xl shadow-sm mb-6",
#			),
#			rx.el.div(
#				graph_explorer_component(),
#				node_detail_panel(),
#				class_name="flex-1 flex min-h-0",
#			),
#			class_name="flex flex-col h-full",
#		),
#		on_mount=GraphState.load_page_data,
#	)