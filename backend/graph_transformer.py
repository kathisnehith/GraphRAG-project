from dotenv import load_dotenv
import os
from langchain.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.graphs import Neo4jGraph
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

from utils.visualizer import visualize_neo4j_graph

load_dotenv()
# Get API key from environment variable 
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("Warning: ANTHROPIC_API_KEY not found in environment variables")
    print("Please add ANTHROPIC_API_KEY=your_api_key_here to your .env file")
else:
    print("Anthropic API key loaded successfully")

# Use Claude 3.5 Sonnet with increased max_tokens
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.4,  # Very low temperature for consistent extraction
    max_tokens=8192,  # Increased max_tokens to avoid truncation
    anthropic_api_key=api_key
)

# Create graph transformer with the fixed LLM
graph_transformer = LLMGraphTransformer(
    llm=llm,
    node_properties=False,  # Disabled to reduce token usage
    relationship_properties=False  # Disabled to reduce token usage
)

print(f"✓ Claude LLM initialized with max_tokens=8192")
print(f"✓ Graph transformer created")

# File uploader
uploaded_file = r'/Users/kathisnehith/Downloads/prompt_engineer_sample_book.pdf'
        # Load and split the PDF
loader = PyPDFLoader(uploaded_file)
pages = loader.load_and_split()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=2200, chunk_overlap=40)
docs = text_splitter.split_documents(pages)

lc_docs = []
for i, doc in enumerate(docs):
    # Get page number from metadata, default to 0 if not available
    page_number = doc.metadata.get('page', 0)
    
    # Create document with cleaned content and preserved metadata
    lc_docs.append(Document(
        page_content=doc.page_content.replace("\n", ""), 
        metadata={'page': page_number, 'source': uploaded_file}
    ))
    
    # Print progress and chunk info
    print(f"Chunk {i+1}/{len(docs)} processed - Page {page_number}")
    print(f"Content: {lc_docs[-1].page_content[:100]}...")
    print("-" * 50)

# Convert to graph documents
graph_documents_lc = graph_transformer.convert_to_graph_documents(lc_docs)
print(lc_docs)

# nodes and relationships extracted from the second document chunk
print(f"Nodes:{graph_documents_lc[1].nodes}")
print(f"Relationships:{graph_documents_lc[1].relationships}")


# Connect to Neo4j database
graph = Neo4jGraph(url=os.getenv("NEO4J_URI"), 
                username=os.getenv("NEO4J_USERNAME"), 
                password=os.getenv("NEO4J_PASSWORD"),
                enhanced_schema=True)

# cypher is neo4j query language similar to SQL but for graph databases.
# Cypher query to clear the graph database
cypher = """ MATCH (n)
DETACH DELETE n;
                """
graph.query(cypher)

# add the graph documents to the Neo4j graph
print("Adding graph documents to Neo4j...")
graph.add_graph_documents(graph_documents_lc, include_source=True)


# Get the schema of the graph
schema = graph.get_schema
print("Sucessfully! Added and Graph schema retrieved.........")
print("Graph schema: \n", schema)


## Visualize the Knowledge-graph 
# Run the function with your Neo4j graph
print("🚀 Creating Neo4j visualization...")
result = visualize_neo4j_graph(graph, max_nodes=500, max_relationships=1000)

if result:
    print(f"\n🎉 Visualization completed!")
    print(f"   📊 Nodes: {result['nodes_count']}")
    print(f"   🔗 Relationships: {result['relationships_count']}")
    print(f"   📁 File: {result['output_file']}")