import sys
import tempfile
import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_community.graphs import Neo4jGraph

llm = None
graph_transformer = None
graph = None


st.set_page_config(
        layout="wide",
        page_title="GraphRAG Studio",
        page_icon="🔗",
        initial_sidebar_state="expanded"
    )

st.title("Knowledge-Graph RAG")

# =========================
# LLM & Graph Transformer Initialization
# =========================
with st.sidebar:
    st.subheader("Select LLM Provider & API Key")
    llm_provider = st.selectbox("Choose LLM Provider:", ["Anthropic", "OpenAI"], key="llm_provider")

api_key = st.sidebar.text_input("Enter your API Key:", type='password')
graph_transformer_button = st.sidebar.button("Check & Connect ")

if llm_provider == "OpenAI":
    if api_key:
        llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4.1",
            temperature=0.4
        )
elif llm_provider == "Anthropic":
    if api_key:
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.4,
            anthropic_api_key=api_key
        )
if graph_transformer_button:
    if llm:
        graph_transformer = LLMGraphTransformer(
            llm=llm,
            node_properties=False,  # Disabled to reduce token usage
            relationship_properties=False  # Disabled to reduce token usage
        )
        st.sidebar.success("Graph Transformer initialized successfully!")
    else:
        st.sidebar.error("Please enter a valid API key for the selected LLM provider.")    

# =========================
# Neo4j Database Connection
# =========================
st.sidebar.subheader("Connect to Neo4j Database")
neo4j_url = st.sidebar.text_input("Neo4j URL:", value="neo4j+s://<your-neo4j-url>")
neo4j_username = st.sidebar.text_input("Neo4j Username:", value="neo4j")
neo4j_password = st.sidebar.text_input("Neo4j Password:", type='password')
connect_button = st.sidebar.button("Connect")

if connect_button:
    try:
        graph = Neo4jGraph(
            url=neo4j_url,
            username=neo4j_username,
            password=neo4j_password,
            enhanced_schema=True
        )
        # Clear the graph database
        cypher = """
            MATCH (n)
            DETACH DELETE n;
            """
        graph.query(cypher)

        st.sidebar.success("Connected to Neo4j database successfully!")
    except Exception as e:
        st.sidebar.error(f"Failed to connect to Neo4j: {e}")

# ==================================================
# Document Preparation || Graph Creation ||DB-Storage
# ===================================================
uploaded_file = st.file_uploader("Please select a PDF file.", type="pdf")
if uploaded_file is not None:
    st.success("PDF file uploaded successfully!")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name
        with st.spinner("Processing the PDF..."):
            # Load and split the PDF
            loader = PyPDFLoader(tmp_file_path)
            pages = loader.load_and_split()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=40)
            docs = text_splitter.split_documents(pages)
        with st.spinner("Preparing documents..."):
            lc_docs = []
            for doc in docs:
                lc_docs.append(Document(page_content=doc.page_content.replace("\n", ""), metadata={'source': uploaded_file.name}))
            st.success("Documents prepared successfully!")
        st.write(f"Total chunks created: {len(lc_docs)}")
else:
    st.warning("Please upload a PDF file to continue.")

graph_create_button = st.button("Create & Store Graph Documents")
if graph_create_button and graph_transformer and lc_docs:
    with st.spinner("Converting documents to graph format..."):
        graph_documents_lc = graph_transformer.convert_to_graph_documents(lc_docs)
        st.success("Graph documents created successfully!")
        st.write(f"Total graph documents created: {len(graph_documents_lc)}")
        # Display first nodes and relationships for the first document
        if graph_documents_lc:
            st.write(f"Nodes in first document: {graph_documents_lc[0].nodes}")
            st.write(f"Relationships in first document: {graph_documents_lc[0].relationships}")
            # add the graph documents to the Neo4j graph
            if graph:
                with st.spinner("Adding graph documents to Neo4j..."):
                    graph.add_graph_documents(graph_documents_lc, include_source=True)


# =========================
# QA Chain: Querying the Knowledge Graph
# =========================
if llm and graph:
    st.success("LLM and Neo4j graph are ready for querying!")
# Create the GraphCypherQAChain with the tracker
    chain = GraphCypherQAChain.from_llm(
    llm=llm,                             # Use OpenAI LLM for question answering
    graph=graph,                                # Use the Neo4j graph
    #cypher_prompt=custom_cypher_prompt,
    verbose=True,                               # Enable verbose logging
    top_k=15,                                    # Return top 5 results
    allow_dangerous_requests=True,
    #callbacks=[tracker]                         # Add the tracker to the callbacks
)
    qa=st.text_input("Enter your question about the knowledge graph:", key="qa_input")
    if qa:
        with st.spinner("Running query..."):
            result = chain.invoke({"query": qa})
            st.success("Query executed successfully!")
            with st.container(border=True):
                st.subheader("Query Results")
                st.write(f"🔍 Question: {qa}")
                st.write(f"💡 Answer: {result['result']}")





