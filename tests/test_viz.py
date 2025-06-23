import os
import sys
from dotenv import load_dotenv
#python -m tests.test_viz
from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from utils.visualizer import visualize_neo4j_graph
load_dotenv()
graph = Neo4jGraph(url=os.getenv("NEO4J_URI"), 
                username=os.getenv("NEO4J_USERNAME"), 
                password=os.getenv("NEO4J_PASSWORD"),
                enhanced_schema=True)
# Run the function with your Neo4j graph
print("🚀 Creating Neo4j visualization...")
result = visualize_neo4j_graph(graph, max_nodes=1001, max_relationships=2195)

if result:
    print(f"\n🎉 Visualization completed!")
    print(f"   📊 Nodes: {result['nodes_count']}")
    print(f"   🔗 Relationships: {result['relationships_count']}")
    print(f"   📁 File: {result['output_file']}")