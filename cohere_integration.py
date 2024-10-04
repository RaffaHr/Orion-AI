import streamlit as st
import pandas as pd
import requests
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OllamaEmbeddings
from dotenv import load_dotenv
from langchain.schema import Document
import cohere
import os
import json
# Carregar as variáveis de ambiente
load_dotenv()

# Inicializa o cliente cohere usando a chave de API do arquivo .env
api_key = os.getenv("COHERE_API_KEY")
if api_key is None:
    st.error("API key da Cohere não encontrada. Verifique seu arquivo .env.")
else:
    co = cohere.ClientV2(api_key)

# Função para chamar a API do Cohere e reformular a resposta
def generate_with_cohere(prompt):
    url = 'https://api.cohere.ai/generate'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'command-xlarge-nightly',
        'prompt': prompt,
        'max_tokens': 40,
        'temperature': 1
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if 'text' in result:
            return result['text'].strip()
        else:
            st.error("Resposta inesperada da API Cohere: 'text' não encontrado.")
            st.json(result)
            return "Erro: Resposta inesperada da API."
    else:
        return f"Erro: {response.status_code} - {response.text}"

@st.cache_data
def load_excel_data():
    try:
        df = pd.read_excel("Base_de_conhecimento.xlsx")
        documents = [Document(page_content=row['Resposta'], metadata={'pergunta': row['Pergunta']}) for index, row in df.iterrows()]
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Excel: {e}")
        return None

    try:
        embeddings = OllamaEmbeddings(model='nomic-embed-text')
    except ValueError as e:
        st.error(f"Erro ao inicializar embeddings: {e}")
        return None  

    try:
        vectorstore = FAISS.from_documents(documents, embeddings)
    except Exception as e:
        st.error(f"Erro ao criar o vectorstore: {e}")
        return None  

    retriever = vectorstore.as_retriever()
    return retriever

retriever = load_excel_data()
if retriever is None:
    st.stop()

st.markdown("<h1 style='text-align: center;'>Assistente Virtual - Hiper Bot 🤖</h1>", unsafe_allow_html=True)

def run_chain(user_input):
    documents = retriever.get_relevant_documents(user_input)

    if not documents or not documents[0].page_content.strip():
        return "Desculpe, não consegui encontrar uma resposta para sua pergunta ou ainda não fui programado para responder essa pergunta."

    original_answer = documents[0].page_content.strip()
    reformulation_prompt = f"""
    Reformule a seguinte resposta de forma direta e assertiva, mantendo o contexto: {original_answer} 
    Evite retornar respostas que não estejam relacionadas à pergunta do usuário: {original_answer}.
    Determine a melhor resposta com base na base de conhecimento.
    """
    
    reformulated_response = generate_with_cohere(reformulation_prompt)
    return reformulated_response

if 'conversations' not in st.session_state:
    st.session_state.conversations = {}

selected_chat = ""

if st.sidebar.button("Iniciar Nova Conversa"):
    selected_chat = ""

st.sidebar.title("Conversas")
chat_names = list(st.session_state.conversations.keys())

for chat_name in chat_names:
    if st.sidebar.button(chat_name):
        selected_chat = chat_name

if selected_chat and selected_chat in st.session_state.conversations:
    messages = st.session_state.conversations[selected_chat]
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if user_input := st.chat_input("Você:"):
    # Cria nova conversa se não houver conversa selecionada
    if selected_chat == "":
        chat_name = f"{user_input[:20]}..."  # Limita o nome da conversa
        st.session_state.conversations[chat_name] = []
        selected_chat = chat_name  # Define a nova conversa como selecionada

    st.session_state.conversations[selected_chat].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Chama a função com o input do usuário
    response = run_chain(user_input)
    
    with st.chat_message("assistant"):
        st.markdown(response)
        st.session_state.conversations[selected_chat].append({"role": "assistant", "content": response})

# Atualiza a barra lateral para refletir a nova conversa
st.sidebar.session_state.conversations = json.dumps(st.session_state.conversations)
