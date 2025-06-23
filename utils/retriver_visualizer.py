import ast
from backend.graph_query import SimpleGraphTracker

# Create tracker and chain
tracker = SimpleGraphTracker()
# --- Visualization Section ---
# Parse the context data (safe for your own generated data)
print("=== DEBUG: tracker.context ===")
print(repr(tracker.context))

try:
    context_list = ast.literal_eval(tracker.context)
except Exception as e:
    print(f"Error parsing context: {e}")
    context_list = []
print("=== DEBUG: context_list ===")
print(repr(context_list))
print("=== DEBUG: context_list type and length ===")
print(type(context_list), len(context_list))
# Create a PyVis network
net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)

# Add nodes and edges based on context
node_ids = set()
for item in context_list:
    for key, value in item.items():
        if isinstance(value, dict) and 'id' in value:
            node_id = value['id']
            node_ids.add(node_id)
            color = '#FF6B6B' if key.lower() == 'react' else '#4ECDC4'
            net.add_node(node_id, label=node_id, color=color)

# Add edges between all nodes in the same item (if more than one node per item)
for item in context_list:
    ids = [v['id'] for v in item.values() if isinstance(v, dict) and 'id' in v]
    if len(ids) > 1:
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                net.add_edge(ids[i], ids[j], label="related", color='#AAAAAA')

# Save and display the HTML
output_file = "qa_chain_dynamic_result.html"
net.save_graph(output_file)
print(f"Visualization saved to {output_file}")

# Optionally open in browser
webbrowser.open(f"file://{os.path.abspath(output_file)}")