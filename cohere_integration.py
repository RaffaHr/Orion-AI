import streamlit as st
import pandas as pd
import requests
import json
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv
from langchain.schema import Document
import cohere
import os

# Carregar as variáveis de ambiente
load_dotenv()

# Inicializa o cliente Cohere usando a chave de API do arquivo .env
api_key = os.getenv("COHERE_API_KEY")
if api_key is None:
    st.error("API key da Cohere não encontrada. Verifique seu arquivo .env.")
else:
    co = cohere.ClientV2(api_key)

# Função para chamar a API do Cohere e reformular a resposta de forma mais precisa
def generate_with_cohere(prompt):
    url = 'https://api.cohere.ai/generate'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'command-xlarge-nightly',
        'prompt': f"{prompt} \n\nResponda estritamente à pergunta do usuário, baseando-se apenas nas informações fornecidas abaixo. Não adicione informações extras e não invente conteúdo. Se não houver uma resposta precisa, apenas diga que não encontrou uma resposta.",
        'max_tokens': 90,
        'temperature': 0.4  # Reduzimos ainda mais a temperatura para respostas mais objetivas
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

# Função para reformular o título da conversa com base na primeira pergunta
def generate_chat_title(prompt):
    reformulation_prompt = f"Reformule a seguinte pergunta em forma de título, e que seja o mais curto possível, mantendo só o contexto. {prompt}"
    return generate_with_cohere(reformulation_prompt)

# Função para carregar os dados do arquivo JSON
@st.cache_resource
def load_json_data():
    try:
        # Carregar o arquivo JSON
        with open('db_process.json', 'r') as f:
            data = json.load(f)
        
        # Criar uma lista de documentos para o retriever a partir do conteúdo do JSON
        documents = [Document(page_content=item['completions'], metadata={'prompt': item['prompt']}) for item in data]
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados do JSON: {e}")
        return None

    try:
        # Inicializar embeddings Cohere
        embeddings = CohereEmbeddings(model='embed-multilingual-light-v3.0', user_agent='HiperBot')
    except ValueError as e:
        st.error(f"Erro ao inicializar embeddings: {e}")
        return None  

    try:
        # Criar o vectorstore com FAISS
        vectorstore = FAISS.from_documents(documents, embeddings)
    except Exception as e:
        st.error(f"Erro ao criar o vectorstore: {e}")
        return None  

    retriever = vectorstore.as_retriever()
    return retriever

# Carregar a base de dados JSON
retriever = load_json_data()
if retriever is None:
    st.stop()

st.markdown("<h1 style='text-align: center;'>Assistente Virtual - Hiper Bot 🤖</h1>", unsafe_allow_html=True)

# Função para executar a lógica de interação
def run_chain(user_input):
    # Limite de mensagens a serem enviadas como contexto (ajuste conforme necessário)
    max_history = 5
    
    # Recuperar o histórico da conversa atual
    selected_chat = st.session_state.selected_chat
    if selected_chat and selected_chat in st.session_state.conversations:
        conversation_history = st.session_state.conversations[selected_chat]
        
        # Criar um contexto formatado de perguntas e respostas
        context = ""
        for message in conversation_history[-max_history:]:
            if message["role"] == "user":
                context += f"Usuário: {message['content']}\n"
            elif message["role"] == "assistant":
                context += f"Assistente: {message['content']}\n"
        
        # Adicionar a nova pergunta ao contexto
        prompt_with_history = f"{context}Usuário: {user_input}\nAssistente:"
    else:
        # Se não houver histórico, usar apenas a pergunta do usuário
        prompt_with_history = f"Usuário: {user_input}\nAssistente:"

    # Primeiro, tente obter documentos relevantes com base na pergunta e no histórico
    try:
        # Usando o método `invoke` em vez de `get_relevant_documents`
        documents = retriever.invoke(user_input)[:5]  # Pegamos os 5 documentos mais relevantes

        if documents:
            # Obter a primeira resposta relevante
            resposta = documents[0].page_content.strip()

            # Reformular a resposta baseada no conteúdo exato do documento e no histórico
            final_response = generate_with_cohere(
                f"Com base na informação a seguir: {resposta}, "
                f"e considerando a pergunta do usuário: '{user_input}', "
                "forneça uma resposta clara e direta que responda à nova pergunta."
            )
            return final_response
            
    except Exception as e:
        st.error(f"Erro ao recuperar documentos: {e}")

    # Se nenhum documento relevante for encontrado ou a resposta for insuficiente
    return "Desculpe, não tenho informações suficientes para responder a essa pergunta no momento."

# Inicializar sessão de conversas
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'selected_chat' not in st.session_state:
    st.session_state.selected_chat = ""

# Sidebar para exibir conversas
st.sidebar.title("Conversas")
chat_names = list(st.session_state.conversations.keys())

# Botão para iniciar nova conversa
if st.sidebar.button("Iniciar Nova Conversa"):
    st.session_state.selected_chat = ""

# Listar conversas existentes e permitir seleção
for chat_name in chat_names:
    if st.sidebar.button(chat_name):
        st.session_state.selected_chat = chat_name

# Exibir mensagens da conversa selecionada
selected_chat = st.session_state.selected_chat
if selected_chat and selected_chat in st.session_state.conversations:
    messages = st.session_state.conversations[selected_chat]
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Receber a entrada do usuário
if user_input := st.chat_input("Você:"):
    # Se uma conversa já estiver selecionada, adiciona a nova mensagem
    if selected_chat:
        st.session_state.conversations[selected_chat].append({"role": "user", "content": user_input})
    else:
        # Cria uma nova conversa com um título reformulado pela IA
        chat_name = generate_chat_title(user_input[:50])  # Reformula o título baseado na primeira pergunta
        st.session_state.conversations[chat_name] = []
        st.session_state.conversations[chat_name].append({"role": "user", "content": user_input})
        st.session_state.selected_chat = chat_name

    # Exibir mensagem do usuário no chat
    with st.chat_message("user"):
        st.markdown(user_input)

    # Executar a função para gerar a resposta da IA
    response = run_chain(user_input)
    
    # Adicionar a resposta da IA ao histórico
    with st.chat_message("assistant"):
        st.markdown(response)
        st.session_state.conversations[st.session_state.selected_chat].append({"role": "assistant", "content": response})
