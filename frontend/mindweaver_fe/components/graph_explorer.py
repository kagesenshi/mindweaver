#import reflex as rx
#from mindweaver_fe.states.graph_state import GraphState
#
#
#def graph_explorer_component() -> rx.Component:
#	"""The interactive graph visualization component using reflex-enterprise."""
#	return rxe.flow.provider(
#		rxe.flow(
#			rxe.flow.background(variant="dots"),
#			rxe.flow.controls(),
#			nodes=GraphState.flow_nodes,
#			edges=GraphState.flow_edges,
#			fit_view=True,
#			on_node_click=lambda node: GraphState.select_node(node["id"]),
#			class_name="w-full h-full bg-gray-50 rounded-lg border border-gray-200",
#		)
#	)