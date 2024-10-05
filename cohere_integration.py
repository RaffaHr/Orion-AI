import streamlit as st
import pandas as pd
import requests
from langchain_community.vectorstores import FAISS
from langchain.embeddings import CohereEmbeddings
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
    
    # Alterando o prompt para focar somente nas informações solicitadas
    data = {
        'model': 'command-xlarge-nightly',
        'prompt': f"{prompt} \n \n Responda estritamente à pergunta do usuário. Se a pergunta menciona uma empresa específica, forneça apenas o prazo de acareação dessa empresa, sem mencionar outras empresas ou seus prazos. A resposta deve ser direta e precisa. Evite erros, ambiguidade ou informações adicionais que não foram solicitadas. A resposta deve se concentrar unicamente na informação pedida, como por exemplo: 'O prazo de acareação da [NOME DA EMPRESA] é de [PRAZO]'.'",
        'max_tokens': 90,  # Mantemos o limite de tokens mais baixo para respostas curtas
        'temperature': 0.5  # Reduzimos ainda mais a temperatura para respostas mais objetivas
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
    reformulation_prompt = f"Reformule o seguinte título para um chat de forma clara e objetiva: {prompt}"
    return generate_with_cohere(reformulation_prompt)

@st.cache_resource
def load_excel_data():
    try:
        df = pd.read_excel("db_process.xlsx")
        documents = [Document(page_content=row['completions'], metadata={'prompt': row['prompt']}) for index, row in df.iterrows()]
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Excel: {e}")
        return None

    try:
        embeddings = CohereEmbeddings(model='embed-multilingual-light-v3.0', user_agent='HiperBot')
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

# Função para executar a lógica de interação
def run_chain(user_input):
    # Primeiro, tente obter documentos relevantes com base na pergunta
    documents = retriever.get_relevant_documents(user_input)

    # Verifica se há documentos relevantes
    if documents:
        # Se houver documentos relevantes, retorna a resposta do primeiro
        resposta = documents[0].page_content.strip()
        final_response = generate_with_cohere(f"Com base na informação a seguir, formule uma resposta precisa e direta: {resposta}")
        return final_response
    
    # Se não houver documentos relevantes, verifica por relações semelhantes
    similar_documents = retriever.get_similar_documents(user_input)  # Você precisaria implementar essa função
    
    if similar_documents:
        # Se encontrar documentos semelhantes, retorna a resposta do primeiro
        resposta = similar_documents[0].page_content.strip()
        final_response = generate_with_cohere(f"Com base na informação a seguir, formule uma resposta precisa e direta: {resposta}")
        return final_response

    # Se não houver documentos relevantes ou semelhantes, retorna a mensagem padrão
    return "Desculpe, não tenho informações sobre essa pergunta no momento."



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
