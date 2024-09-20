# Importações necessárias
import pandas as pd
import openai
import json
from pandasql import sqldf
import sys

from openai_api_key import KEY

# Configuração da API da OpenAI
openai.api_key = KEY
# Carregar os dados CSVs e unir com base nas colunas 'client', 'server' e 'timestamp'
bitrate_data = pd.read_csv('bitrate_train.csv')
latency_data = pd.read_csv('rtt_train.csv')

merged_data = pd.merge(bitrate_data, latency_data, on=['client', 'server', 'timestamp'])

# Normalizar os dados de Bitrate e Latência usando Min-Max Scaling
def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min())

merged_data['Bitrate_Normalized'] = min_max_normalize(merged_data['bitrate'])
merged_data['Latency_Normalized'] = min_max_normalize(merged_data['rtt'])

# Calcular a QoE para cada entrada
merged_data['QoE'] = merged_data['Bitrate_Normalized'] / (merged_data['Latency_Normalized'] + 0.000001)

# Funções para serem chamadas pelo modelo, representando passos do raciocínio
def calculate_qoe_mean_by_client():
    qoe_mean = merged_data.groupby('client')['QoE'].mean().to_dict()
    return json.dumps(qoe_mean)

def find_client_with_min_qoe(qoe_mean_dict):
    qoe_mean = json.loads(qoe_mean_dict)
    worst_client = min(qoe_mean, key=qoe_mean.get)
    return json.dumps({"worst_client": worst_client, "worst_qoe": qoe_mean[worst_client]})

def calculate_qoe_variance_by_server():
    qoe_variance = merged_data.groupby('server')['QoE'].var().to_dict()
    return json.dumps(qoe_variance)

def find_server_with_min_variance(qoe_variance_dict):
    qoe_variance = json.loads(qoe_variance_dict)
    most_consistent_server = min(qoe_variance, key=qoe_variance.get)
    return json.dumps({"most_consistent_server": most_consistent_server, "lowest_variance": qoe_variance[most_consistent_server]})

def calculate_best_server_for_client(client):
    client_data = merged_data[merged_data['client'] == client]
    server_qoe = client_data.groupby('server')['QoE'].mean().to_dict()
    return json.dumps(server_qoe)

def find_server_with_max_qoe(server_qoe_dict):
    server_qoe = json.loads(server_qoe_dict)
    best_server = max(server_qoe, key=server_qoe.get)
    return json.dumps({"best_server": best_server, "best_qoe": server_qoe[best_server]})

def calculate_qoe_impact(client, latency_increase_percentage):
    client_data = merged_data[merged_data['client'] == client].copy()
    client_data['Latency_Normalized_Increased'] = client_data['Latency_Normalized'] * (1 + latency_increase_percentage / 100)
    client_data['New_QoE'] = client_data['Bitrate_Normalized'] / (client_data['Latency_Normalized_Increased']+0.000001)
    original_qoe = client_data['QoE'].mean()
    new_qoe = client_data['New_QoE'].mean()
    impact = ((new_qoe - original_qoe) / original_qoe) * 100
    
    result = {
        "original_qoe": original_qoe,
        "new_qoe": new_qoe,
        "impact_percentage": impact
    }
    return json.dumps(result)

def sql_query(query):
    return f"{sqldf(query, {'bitrate': bitrate_data, 'latency': latency_data})}"
    

# Mapeamento de funções para serem chamadas
available_functions = {
    "calculate_qoe_mean_by_client": calculate_qoe_mean_by_client,
    "find_client_with_min_qoe": find_client_with_min_qoe,
    "calculate_qoe_variance_by_server": calculate_qoe_variance_by_server,
    "find_server_with_min_variance": find_server_with_min_variance,
    "calculate_best_server_for_client": calculate_best_server_for_client,
    "find_server_with_max_qoe": find_server_with_max_qoe,
    "calculate_qoe_impact": calculate_qoe_impact,
    "sql_query": sql_query
}

# Definição das funções para o modelo usando JSON Schema
functions = [
    {
        "name": "calculate_qoe_mean_by_client",
        "description": "Calcula a média de QoE para cada cliente.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "find_client_with_min_qoe",
        "description": "Encontra o cliente com a menor média de QoE.",
        "parameters": {
            "type": "object",
            "properties": {
                "qoe_mean_dict": {
                    "type": "string",
                    "description": "Um dicionário JSON com a média de QoE por cliente."
                }
            },
            "required": ["qoe_mean_dict"]
        }
    },
    {
        "name": "calculate_qoe_variance_by_server",
        "description": "Calcula a variância de QoE para cada servidor.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "find_server_with_min_variance",
        "description": "Encontra o servidor com a menor variância de QoE.",
        "parameters": {
            "type": "object",
            "properties": {
                "qoe_variance_dict": {
                    "type": "string",
                    "description": "Um dicionário JSON com a variância de QoE por servidor."
                }
            },
            "required": ["qoe_variance_dict"]
        }
    },
    {
        "name": "calculate_best_server_for_client",
        "description": "Calcula a média de QoE por servidor para um cliente específico.",
        "parameters": {
            "type": "object",
            "properties": {
                "client": {
                    "type": "string",
                    "description": "Par de letras minúsculas que representa o cliente."
                }
            },
            "required": ["client"]
        }
    },
    {
        "name": "find_server_with_max_qoe",
        "description": "Encontra o servidor com a maior QoE média.",
        "parameters": {
            "type": "object",
            "properties": {
                "server_qoe_dict": {
                    "type": "string",
                    "description": "Um dicionário JSON com a média de QoE por servidor."
                }
            },
            "required": ["server_qoe_dict"]
        }
    },
    {
        "name": "calculate_qoe_impact",
        "description": "Calcula o impacto na QoE de um cliente dado um aumento na latência.",
        "parameters": {
            "type": "object",
            "properties": {
                "client": {
                    "type": "string",
                    "description": "Par de letras minúsculas que representa o cliente."
                },
                "latency_increase_percentage": {
                    "type": "number",
                    "description": "Percentual de aumento na latência."
                }
            },
            "required": ["client", "latency_increase_percentage"]
        }
    },
    {
        "name": "sql_query",
        "description": '''
        Realiza consultas nos dados disponíveis, dispostos em duas tabelas: "latency" (campos: client, server, timestamp e rtt) e 
        "bitrate" (campos: client, server, timestamp e rtt).''',
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "query SQL em versão SQLite"
                }
            },
            "required": ["query"]
        }

    }
]

# Função principal para processar a pergunta usando Chain of Thought com Function Calling
def process_question(question):
    messages = [
        {"role": "system", "content": """
        Você é um assistente que responde perguntas sobre QoE em transmissões de vídeo. 
        Ao responder, você deve usar uma cadeia de raciocínio passo a passo, chamando funções conforme necessário para obter as informações.

        Quedas na média de bitrate, ou valores médios anormalmente altos em rtt indicam problemas temporários na rede,
        e podem ser verificados nos dados por consultas SQL,
        acessível pela tool 'sql_query' 
        """},
        {"role": "user", "content": question}
    ]

    # Loop para permitir múltiplas chamadas de função (Chain of Thought)
    while True:

        #print(f'messages:\n{messages}')

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini", 
            messages=messages,
            functions=functions,
            function_call="auto"
        )
        message = response['choices'][0]['message']
        messages.append(message)

        if 'function_call' in message:
            function_name = message['function_call']['name']
            function_args = message['function_call'].get('arguments', '{}')
            function_args = json.loads(function_args)
            function_to_call = available_functions.get(function_name)

            # print(f'chamada de função: {function_name}({function_args})')

            if function_to_call:
                function_response = function_to_call(**function_args)
                # Envia a resposta da função de volta ao modelo
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": function_response
                })
            else:
                # Se a função não existir, informar o usuário
                return f"Desculpe, a função {function_name} não está disponível."
        else:
            # Se não houver mais chamadas de função, retornar a resposta final
            final_answer = message['content']
            return final_answer

if __name__ == "__main__":

    question1 = sys.argv[1]

    answer1 = process_question(question1)
    print("Pergunta:", question1)
    print("Resposta:", answer1)