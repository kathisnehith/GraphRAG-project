import streamlit as st
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
import os

# Use Streamlit secrets for sensitive info
def get_llm(api_key):
    return ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        anthropic_api_key=api_key
    )

class SimpleGraphTracker(BaseCallbackHandler):
    def __init__(self):
        self.nodes_count = 0
        self.context = ""
        self.cypher = ""
    def on_text(self, text: str, **kwargs):
        if "MATCH" in text or "RETURN" in text:
            self.cypher = text.strip()
        if text.startswith("[{") and "}]" in text:
            self.context = text.strip()
            try:
                self.nodes_count = len(eval(text))
            except:
                self.nodes_count = 0

custom_cypher_prompt = PromptTemplate.from_template("""
You are a Cypher expert working with a knowledge graph about prompt engineering concepts, techniques, parameters, and best practices.
with this Neo4j schema:
{schema}
Generate a Cypher query to answer the following question:
{question}

Guidelines:
- Use flexible matching with `toLower(n.id)` or `CONTAINS` instead of exact `id` matches.
- Prefer `MATCH (a)-[r]->(b)` patterns to explore relationships.
- Use `LIMIT` to avoid overly large result sets.
- If the question involves multiple concepts (e.g., temperature, top-k, top-p), try to find how they relate via shared concepts or recommendations.
- Return relevant properties like `id`, `description`, `recommendation`, or `example`.

Only return the Cypher query. Do not include explanations.
""")

st.set_page_config(page_title="GraphRAG App", page_icon="🧠")
st.title("🧠 GraphRAG ")
st.caption("A Streamlit interface for querying a Neo4j-powered knowledge graph using LLMs.")

# Use os.environ for local testing, comment out st.secrets usage
with st.form("db_form"):
    api_key = st.text_input("Anthropic API Key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
    neo4j_url = st.text_input("Neo4j URL", value=os.getenv("NEO4J_URI", ""))
    neo4j_username = st.text_input("Neo4j Username", value=os.getenv("NEO4J_USERNAME", ""))
    neo4j_password = st.text_input("Neo4j Password", type="password", value=os.getenv("NEO4J_PASSWORD", ""))
    # api_key = st.text_input("Anthropic API Key", type="password", value=st.secrets.get("ANTHROPIC_API_KEY", ""))
    # neo4j_url = st.text_input("Neo4j URL", value=st.secrets.get("NEO4J_URI", ""))
    # neo4j_username = st.text_input("Neo4j Username", value=st.secrets.get("NEO4J_USERNAME", ""))
    # neo4j_password = st.text_input("Neo4j Password", type="password", value=st.secrets.get("NEO4J_PASSWORD", ""))
    connect_clicked = st.form_submit_button("Connect DB")

if 'graph' not in st.session_state:
    st.session_state['graph'] = None
    st.session_state['chain'] = None
    st.session_state['tracker'] = None
    st.session_state['connected'] = False

if connect_clicked:
    try:
        graph = Neo4jGraph(url=neo4j_url, username=neo4j_username, password=neo4j_password, enhanced_schema=True)
        llm = get_llm(api_key)
        tracker = SimpleGraphTracker()
        schema = graph.get_schema
        chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            top_k=15,
            allow_dangerous_requests=True,
            callbacks=[tracker]
        )
        st.session_state['graph'] = graph
        st.session_state['chain'] = chain
        st.session_state['tracker'] = tracker
        st.session_state['connected'] = True
        st.success("Connected to Neo4j database!")
    except Exception as e:
        st.session_state['connected'] = False
        st.error(f"Failed to connect: {e}")

if st.session_state['connected']:
    st.markdown("---")
    st.subheader("Ask a Question")
    with st.form("query_form"):
        question = st.text_input("Enter your question")
        query_clicked = st.form_submit_button("Query")
    if query_clicked and question:
        with st.spinner("Querying knowledge graph..."):
            try:
                result = st.session_state['chain'].invoke({"query": question})
                tracker = st.session_state['tracker']
                with st.container(border=True):
                    st.markdown(f"**Answer:** {result['result']}")
                    st.caption(f"Retrieved Nodes: {tracker.nodes_count}")
                    st.caption(f"Cypher Query: {tracker.cypher}")
            except Exception as e:
                st.error(f"Query failed: {e}")
else:
    st.info("Please connect to the Neo4j database first.")
