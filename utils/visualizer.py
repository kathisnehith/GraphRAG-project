from pyvis.network import Network
import os

def visualize_neo4j_graph(graph, max_nodes, max_relationships):
    """
    Visualize Neo4j database using PyVis (similar to your existing function structure)
    """
    
    print("🔄 Fetching data from Neo4j...")
    
    # Get nodes from Neo4j
    nodes_query = f"""
    MATCH (n)
    RETURN 
        id(n) as node_id,
        labels(n) as labels,
        properties(n) as properties
    LIMIT {max_nodes}
    """
    
    # Get relationships from Neo4j
    relationships_query = f"""
    MATCH (a)-[r]->(b)
    RETURN 
        id(a) as source_id,
        id(b) as target_id,
        type(r) as relationship_type,
        properties(r) as rel_properties
    LIMIT {max_relationships}
    """
    
    try:
        nodes_result = graph.query(nodes_query)
        relationships_result = graph.query(relationships_query)
        
        print(f"✅ Retrieved {len(nodes_result)} nodes and {len(relationships_result)} relationships")
        
        if not nodes_result:
            print("❌ No nodes found in database")
            return
        
        # Create network (using your same configuration)
        net = Network(height="1200px", width="100%", directed=True,
                      notebook=False, bgcolor="#222222", font_color="white")
        
        # Build lookup for valid nodes (similar to your approach)
        node_dict = {}
        for node_data in nodes_result:
            node_id = str(node_data['node_id'])
            labels = node_data['labels']
            properties = node_data['properties']
            
            # Create a node object-like structure
            node_dict[node_id] = {
                'id': properties.get('id', f"Node_{node_id}"),
                'type': labels[0] if labels else 'Unknown',
                'neo4j_id': node_id,
                'properties': properties
            }
        
        # Filter out invalid edges and collect valid node IDs (your same logic)
        valid_edges = []
        valid_node_ids = set()
        
        for rel_data in relationships_result:
            source_id = str(rel_data['source_id'])
            target_id = str(rel_data['target_id'])
            
            if source_id in node_dict and target_id in node_dict:
                valid_edges.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'type': rel_data['relationship_type'],
                    'properties': rel_data.get('rel_properties', {})
                })
                valid_node_ids.update([source_id, target_id])
        
        print(f"📊 Valid edges: {len(valid_edges)}, Valid nodes: {len(valid_node_ids)}")
        
        # Add valid nodes (using your same approach)
        for node_id in valid_node_ids:
            node = node_dict[node_id]
            try:
                # Color mapping for different node types
                color_map = {
                    'Concept': '#4ECDC4',
                    'Person': '#FF6B6B', 
                    'Research': '#FF8C94',
                    'Technology': '#45B7D1',
                    'Organization': '#96CEB4',
                    'Publication': '#FFEAA7',
                    'Method': '#DDA0DD',
                    'Framework': '#98D8C8',
                    'Document': '#A8E6CF'
                }
                
                node_color = color_map.get(node['type'], '#CCCCCC')
                
                net.add_node(
                    node_id, 
                    label=node['id'], 
                    title=f"Type: {node['type']}\nID: {node['id']}", 
                    group=node['type'],
                    color=node_color,
                    size=25
                )
            except Exception as e:
                print(f"⚠️ Error adding node {node_id}: {e}")
                continue  # skip if error
        
        # Add valid edges (using your same approach)
        for rel in valid_edges:
            try:
                net.add_edge(
                    rel['source_id'], 
                    rel['target_id'], 
                    label=rel['type'].lower(),
                    title=f"Relationship: {rel['type']}",
                    color={'color': '#666666'},
                    width=2
                )
            except Exception as e:
                print(f"⚠️ Error adding edge: {e}")
                continue  # skip if error
        
        # Configure physics (using your same configuration)
        net.set_options("""
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            }
        }
        """)
        
        # Save graph (using your same approach)
        output_file = "neo4j_knowledge_graph.html"
        net.save_graph(output_file)
        print(f"✅ Graph saved to {os.path.abspath(output_file)}")
        
        # Try to open in browser (your same approach)
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(output_file)}")
            print("🌐 Opened in browser")
        except:
            print("⚠️ Could not open browser automatically")
            print(f"📁 Manually open: {os.path.abspath(output_file)}")
        
        # Return some stats
        return {
            'nodes_count': len(valid_node_ids),
            'relationships_count': len(valid_edges),
            'output_file': output_file
        }
        
    except Exception as e:
        print(f"❌ Error visualizing Neo4j graph: {e}")
        import traceback
        traceback.print_exc()
        return None

