import streamlit as st
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain.llms import Ollama
from langchain.embeddings import OllamaEmbeddings
from dotenv import load_dotenv
from langchain.schema import Document

# Carregar variáveis de ambiente
load_dotenv()

# Inicialização do modelo local
model_local = Ollama(model="llama3.2")

@st.cache_data
def load_excel_data():
    # Carregar dados do arquivo Excel usando pandas
    try:
        df = pd.read_excel("Base_de_conhecimento.xlsx")
        # Criar uma lista de Document com a estrutura correta
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

st.title("Assistente Virtual - Hiper Bot 🤖")

# Função para executar a lógica de interação
def run_chain(user_input):
    # Obter documentos relevantes com base na pergunta do usuário
    documents = retriever.get_relevant_documents(user_input)

    # Se não houver documentos relevantes, retorne a mensagem padrão
    if not documents or not documents[0].page_content.strip():
        return "Desculpe, não consegui encontrar uma resposta para sua pergunta ou ainda não fui programado para responder essa pergunta."

    # Assume que o primeiro documento é o mais relevante
    original_answer = documents[0].page_content.strip()

    # Reformular a resposta para que seja direta e mantenha o contexto
    reformulation_prompt = [f"Reformule a seguinte resposta com tom formal e direta, reformule a resposta original mas mantendo o contexto: {original_answer}"]
    
    # Gere a reformulação
    reformulated_response = model_local.generate(reformulation_prompt)
    
    # Retorna somente a resposta reformulada
    return reformulated_response.generations[0][0].text.strip()  # Acessa o texto da resposta reformulada

# Inicializa a sessão de conversas se não existir
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}

# Cria a barra lateral para exibir as conversas
st.sidebar.title("Conversas")
chat_names = list(st.session_state.conversations.keys())
selected_chat = st.sidebar.selectbox("Escolha a conversa:", options=chat_names + ["Nova conversa"])

# Se o usuário selecionar "Nova conversa"
if selected_chat == "Nova conversa":
    if user_input := st.sidebar.text_input("Digite sua pergunta para iniciar uma nova conversa:"):
        # Gera um nome para a nova conversa baseado na pergunta do usuário
        chat_name = f"Conversa: {user_input[:10]}..."  # Pode ser ajustado para um nome mais representativo
        st.session_state.conversations[chat_name] = []  # Cria uma nova aba com lista vazia
        selected_chat = chat_name  # Seleciona a nova aba

# Exibe mensagens do histórico da aba selecionada
if selected_chat in st.session_state.conversations:
    messages = st.session_state.conversations[selected_chat]
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Caixa de entrada para o usuário
if user_input := st.chat_input("Você:"):
    st.session_state.conversations[selected_chat].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Chama a função com o input do usuário
    response = run_chain(user_input)
    
    # Exibe a resposta do assistente e a adiciona ao histórico
    with st.chat_message("assistant"):
        st.markdown(response)
        st.session_state.conversations[selected_chat].append({"role": "assistant", "content": response})  # Adiciona resposta ao histórico