import streamlit as st
from openai import OpenAI
from pinecone import Pinecone

# ==========================================================
# CONFIGURATION
# ==========================================================
OPENAI_API_KEY = "Enter your OpenAI API key here"
PINECONE_API_KEY = "Enter your Pinecone API key here"

INDEX_NAME = "rag-chat-pinecone"

EMBEDDING_MODEL = "text-embedding-ada-002"   # 1536 dims
CHAT_MODEL = "gpt-4o-mini"                   # fast & cheap
TOP_K = 3

# ==========================================================
# INITIALIZE CLIENTS
# ==========================================================
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# ==========================================================
# STREAMLIT PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="📄 RAG PDF Chatbot",
    layout="centered"
)

st.title("📄 AI-Powered RAG Chatbot for PDF Knowledge Bases")
st.write("building an AI agent trained on 500+ PDF files that provides accurate and precise answers to questions related to the training data")

# ==========================================================
# FUNCTIONS
# ==========================================================
def get_embedding(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def query_pinecone(query_embedding):
    result = index.query(
        vector=query_embedding,
        top_k=TOP_K,
        include_metadata=True
    )
    return result["matches"]

def build_context(matches):
    context = ""
    for match in matches:
        source = match["metadata"].get("source", "Unknown")
        text = match["metadata"].get("text", "")
        context += f"Source: {source}\n{text}\n\n"
    return context

def ask_llm(question, context):
    prompt = f"""
You are a helpful assistant answering questions strictly based on the provided documents.

Context:
{context}

Question:
{question}

Answer clearly and concisely.
"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

# ==========================================================
# UI INPUT
# ==========================================================
question = st.text_input("💬 Ask a question")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching documents and thinking..."):
            # Step 1: Embed question
            query_embedding = get_embedding(question)

            # Step 2: Retrieve relevant chunks
            matches = query_pinecone(query_embedding)

            if not matches:
                st.error("No relevant documents found.")
            else:
                # Step 3: Build context
                context = build_context(matches)

                # Step 4: Ask LLM
                answer = ask_llm(question, context)

                # Step 5: Display results
                st.subheader("✅ Answer")
                st.write(answer)

                st.subheader("📄 Sources")
                for m in matches:
                    st.write(f"- {m['metadata'].get('source', 'Unknown')}")
