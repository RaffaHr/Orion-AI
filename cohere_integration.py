import streamlit as st
import json
import os
import re
import time
from dotenv import load_dotenv
import requests
import cohere

# Carregar as variáveis de ambiente
load_dotenv()

# Inicializa o cliente Cohere usando a chave de API do arquivo .env
api_key = os.getenv("COHERE_API_KEY")
if api_key is None:
    st.error("API key da Cohere não encontrada. Verifique seu arquivo .env.")
else:
    co = cohere.ClientV2(api_key)

# Função para chamar a API do Cohere e verificar se a completions tem relação com a pergunta
def check_response_with_cohere(question, completion):
    prompt = f"Pergunta do usuário: {question}\nResposta sugerida: {completion}\n\nA resposta sugerida está relacionada com a pergunta? Responda apenas 'sim' ou 'não'."
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'command-xlarge-nightly',
        'prompt': prompt,
        'max_tokens': 40,
        'temperature': 0.2
    }
    
    response = requests.post('https://api.cohere.ai/generate', headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if 'text' in result:
            return result['text'].strip().lower() == 'sim'
        else:
            st.error("Erro ao verificar relação da resposta: 'text' não encontrado.")
            return False
    else:
        st.error(f"Erro ao verificar relação da resposta: {response.status_code} - {response.text}")
        return False

# Função para carregar os dados do arquivo JSON
@st.cache_resource
def load_json_data():
    try:
        with open('db_process.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Erro ao carregar os dados do JSON: {e}")
        return None

# Carregar a base de dados JSON
data = load_json_data()
if data is None:
    st.stop()

def extract_keywords(user_input):
    keywords = ["prazo", "acareação", "acareaçao", "transportadora", "protheus", "nota fiscal", "cce", "cc", "cc-e", "baixar", "emitir nf", "baixar nf", "imprimir nf", "nf", "emitir", "gerar", "jadlog", "generoso", "solistica", "correios", "favorita", "comprovante de entrega", "comprovante"]
    found_keywords = [word for word in keywords if re.search(r'\b' + re.escape(word) + r'\b', user_input.lower())]
    return found_keywords

def run_chain(user_input):
    data = load_json_data()
    keywords = extract_keywords(user_input)
    
    response = None

    if keywords:
        for empresa in data["transportadoras"]:
            transportadora_nome = empresa["transportadora"]["nome"].upper()
            if transportadora_nome in user_input.upper():
                for key in keywords:
                    for sub_key, content in empresa["transportadora"].items():
                        if key in sub_key.lower():
                            possible_response = content.get("completions", "")
                            if possible_response:
                                response = possible_response
                            break
                if response:
                    break

        if not response:
            for sistema in data["sistemas"]:
                protheus = sistema["sistema"].get("Protheus", {})
                for key in keywords:
                    for sub_key, content in protheus.items():
                        if key.lower() in sub_key.lower():
                            possible_response = content.get("completions", "")
                            if possible_response:
                                response = possible_response
                            break
                if response:
                    break

    return response if response else "Desculpe, não tenho informações suficientes para responder a essa pergunta no momento."

# Função para detectar palavras-chave de reformulação
def detect_reformulation_keywords(user_input):
    reformulation_keywords = ["keep", "reformule", "formule", "reformular"]
    return any(keyword in user_input.lower() for keyword in reformulation_keywords)

# Função para reformular o texto usando a API Cohere
def reformulate_text_with_cohere(text):
    prompt = f"Você agora é um profissional no atendimento, e visa sempre pela empatia ao cliente, e sempre fala visando na qualidade do atendimento e com palavras fáceis e claras de se entender, com base nisso, você vai reformular o seguinte texto e retorna-lo em markdonw e formate o texto para que tenha uma boa visibilidade, sem retornar tópicos, não faça titulos, opniões, ou assuntos externos, retorne somente o texto reformulado, não retorne frases comoo Espero ter ajudado com a reformulação ou algo do tipo; Caso o texto tenha uma assinatura mantenha a mesma do texto original, no mesmo formato!!; Sempre mantenha saudação como Bom dia, Boa tarde; Se for passado o nome de quem está se direcionando o texto, mantenha o direcionamento também para a pessoa citada: {text}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'command-xlarge-nightly',
        'prompt': prompt,
        'max_tokens': 350,
        'temperature': 0.7
    }
    
    response = requests.post('https://api.cohere.ai/generate', headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if 'text' in result:
            return result['text'].strip()
        else:
            st.error("Erro ao reformular o texto: 'text' não encontrado.")
            return None
    else:
        st.error(f"Erro ao chamar a API Cohere: {response.status_code} - {response.text}")
        return None

# Função principal para lidar com a interação do usuário
def handle_chat(user_input):
    if detect_reformulation_keywords(user_input):
        reformulation_text = re.sub(r'\b(keep|reformule|formule|reformular)\b', '', user_input, flags=re.IGNORECASE).strip()
        
        if reformulation_text:
            reformulated_response = reformulate_text_with_cohere(reformulation_text)
            
            if reformulated_response:
                return reformulated_response
            else:
                return "Não foi possível reformular o texto."
        else:
            return "Nenhum texto encontrado para reformular."
    else:
        return run_chain(user_input)

# Função para simular a digitação da resposta
def simulate_typing(text):
    response_placeholder = st.empty()
    
    displayed_text = ""
    for char in text:
        time.sleep(0.005)
        displayed_text += char
        response_placeholder.markdown(displayed_text)

# Inicializar sessão de conversas
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'selected_chat' not in st.session_state:
    st.session_state.selected_chat = ""

# Sidebar para exibir conversas
st.sidebar.title("Conversas")
chat_names = list(st.session_state.conversations.keys())

if st.sidebar.button("Iniciar Nova Conversa"):
    st.session_state.selected_chat = ""

for chat_name in chat_names:
    if st.sidebar.button(chat_name):
        st.session_state.selected_chat = chat_name

selected_chat = st.session_state.selected_chat
if selected_chat and selected_chat in st.session_state.conversations:
    messages = st.session_state.conversations[selected_chat]
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if user_input := st.chat_input("Você:", max_chars=2000):
    if selected_chat:
        st.session_state.conversations[selected_chat].append({"role": "user", "content": user_input})
    else:
        st.session_state.conversations[user_input[:50]] = [{"role": "user", "content": user_input}]
        st.session_state.selected_chat = user_input[:50]

    with st.chat_message("user"):
        st.markdown(user_input)

    # Exibir loader enquanto a IA busca a resposta
    with st.spinner("Aguarde enquanto a IA processa sua solicitação..."):
        response = handle_chat(user_input)

    # Exibe o "skeleton loader" com animação enquanto processa
    with st.chat_message("assistant"):
        assistant_message_placeholder = st.empty()
        assistant_message_placeholder.markdown(
            """
            <style>
                @keyframes move {
                    0% {
                        background-color: #f0f0f0;
                        transform: translateX(-100%);
                    }
                    50% {
                        background-color: #e0e0e0;
                    }
                    100% {
                        background-color: #f0f0f0;
                        transform: translateX(100%);
                    }
                }
                .skeleton {
                    height: 30px;
                    width: 80%;
                    border-radius: 5px;
                    margin: 8px 0;
                    overflow: hidden;
                    position: relative;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }
                .skeleton::before {
                    content: '';
                    position: absolute;
                    height: 100%;
                    width: 100%;
                    background-color: #f0f0f0;
                    animation: move 1.5s infinite;
                    z-index: 1;
                }
            </style>
            <div class="skeleton"></div>
            """,
            unsafe_allow_html=True
        )

        time.sleep(1.2)

        assistant_message_placeholder.empty()
        simulate_typing(response)

    st.session_state.conversations[st.session_state.selected_chat].append({"role": "assistant", "content": response})