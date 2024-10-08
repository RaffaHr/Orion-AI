# oraculo/run.py
import os
import subprocess

def main():
    # Executa o comando streamlit run no terminal
    subprocess.run(['streamlit', 'run', 'cohere_integration.py'], check=True)
