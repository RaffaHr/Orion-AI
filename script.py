import pandas as pd

# Load the Excel file
file_path = 'db_process.xlsx'  # Use the correct file path
xls = pd.ExcelFile(file_path)

# Check the sheet names to locate the "process" sheet
print(xls.sheet_names)

# Define the new table structure with process-related Q&A
data = {
    'prompt': [
        "Esqueci como verificar a falta de mercadoria, como devo proceder?", 
        "O que preciso fazer quando o pedido de um cliente foi extraviado?", 
        "Qual é o fluxo para processar um reembolso em caso de extravio total de mercadoria?",
        "Como funciona o processo de busca de mercadoria? Qual o prazo que devo passar ao cliente?", 
        "O cliente me informou que o pagamento foi recusado. Como devo orientá-lo?", 
        "Esqueci como lidar com pagamentos recusados via Mercado Pago. Qual é o procedimento correto?", 
        "Quais são as formas de pagamento que posso informar ao cliente?", 
        "Como devo proceder no fluxo de emissão da Nota Fiscal de Devolução após uma devolução?", 
        "Como proceder quando o cliente deseja devolver apenas um item de um kit de filtros?", 
        "Qual é o processo de análise de garantia para mercadorias devolvidas?"
    ],
    'completions': [
        "Quando há uma falta de mercadoria, siga este fluxo: 1. Solicite uma análise interna para verificar se as peças foram enviadas corretamente. 2. Entre em contato com a transportadora para iniciar uma investigação sobre a falta. 3. Aguarde o retorno de ambas as partes antes de concluir a tratativa com o cliente.",
        "Se o pedido foi extraviado, siga o seguinte fluxo: 1. Cobrar uma posição oficial da transportadora para confirmação do extravio. 2. Após a confirmação, informe o cliente e inicie o processo de reembolso. 3. Garanta que o reembolso seja processado dentro de 5 dias úteis.",
        "O fluxo para processar um reembolso em caso de extravio total é: 1. Confirme o extravio com a transportadora. 2. Inicie o processo de reembolso ao cliente. 3. Garanta que o reembolso seja finalizado em até 5 dias úteis, após a confirmação do extravio.",
        "O processo de busca de mercadoria segue o seguinte fluxo: 1. A partir da data de início, o prazo para a transportadora concluir a busca é de 7 dias úteis. 2. No final desse período, cobre a transportadora por uma posição final. 3. Informe o cliente sobre o resultado da busca.",
        "Se o cliente reportou que o pagamento foi recusado, siga este fluxo: 1. Oriente o cliente a verificar com a operadora do cartão. 2. Caso a operadora aprove o pagamento, informe que o problema pode ser com o Mercado Pago. 3. Instrua o cliente a tentar o pagamento novamente ou usar outro método de pagamento disponível.",
        "O processo para lidar com pagamentos recusados via Mercado Pago é: 1. Verifique se a transação foi rejeitada pela operadora do cartão ou pelo próprio Mercado Pago. 2. Oriente o cliente a entrar em contato com a operadora do cartão ou tentar outro método de pagamento, como PIX ou boleto.",
        "As formas de pagamento aceitas no site incluem: 1. Cartão de crédito. 2. PIX. 3. Boleto bancário. Todos os pagamentos são processados via Mercado Pago.",
        "Após a devolução de produtos, siga este fluxo para emitir a Nota Fiscal de Devolução: 1. Confirme que todos os itens foram devolvidos conforme solicitado. 2. Gere a Nota Fiscal de Devolução (NFD) e envie uma cópia ao cliente. 3. Inicie o processo de reembolso imediatamente após a emissão da NFD.",
        "Se o cliente deseja devolver apenas um item de um kit, siga este fluxo: 1. Explique ao cliente que a devolução parcial de um kit não é permitida. 2. Solicite a devolução do kit completo. 3. Após a devolução, processe o reembolso total do valor pago pelo kit.",
        "Para análise de garantia, o fluxo é o seguinte: 1. Receba a mercadoria devolvida e envie para análise interna. 2. Se necessário, envie a mercadoria ao fabricante para análise técnica. 3. Após a confirmação da garantia, emita a Nota Fiscal de Devolução e inicie o reembolso ou troca dentro de 7 dias úteis."
    ]
}

# Convert the data into a DataFrame
new_df = pd.DataFrame(data)

# Write the new data into the "process" sheet, replacing the existing content
with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
    new_df.to_excel(writer, sheet_name='process', index=False)

print("Data written to 'process' sheet successfully.")
