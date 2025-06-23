import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

load_dotenv()
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)


graph = Neo4jGraph(url=os.getenv("NEO4J_URI"), 
                username=os.getenv("NEO4J_USERNAME"), 
                password=os.getenv("NEO4J_PASSWORD"),
                enhanced_schema=True)


# All-in-one solution tracker for graph nodes and relationships Retriever
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


# Create tracker and chain
tracker = SimpleGraphTracker()


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



# Create the GraphCypherQAChain with the tracker
chain = GraphCypherQAChain.from_llm(
    llm=llm,                             # Use OpenAI LLM for question answering
    graph=graph,                                # Use the Neo4j graph
    #cypher_prompt=custom_cypher_prompt,
    verbose=True,                               # Enable verbose logging
    top_k=15,                                    # Return top 5 results
    allow_dangerous_requests=True,
    callbacks=[tracker]                         # Add the tracker to the callbacks
)


# Run query
# LLM model choice makes a difference in the cypher query results,
question = "prompting techniues"
result = chain.invoke({"query": question})

# Print results
print(f"\n🔍 ANALYSIS:")
print(f"📊 Retrieved Nodes: {tracker.nodes_count}")
print(f"📋 Context Data: {tracker.context}")
print(f"🔧 Cypher Query: {tracker.cypher}")
print(f"💬 Answer \n: {result['result']}")