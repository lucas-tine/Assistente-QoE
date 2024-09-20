# Assistente-QoE
Esta é a Lista 6 da disciplina CPS769 - Tópicos Especiais em Aprendizado de Máquina e Aprendizagem Generativa; 2024.2 - PEE - Coppe/ UFRJ

---

## O que é? 

Esta é uma aplicação que aceite perguntas em linguagem natural, no contexto de QoE de tranmissões de vídeos,
e que fornece respostas em linguagem natural utilizando raciocínio CoT e function calling, através da 
API openai.

## Pré-Requisitos

para a execução, é necessário a instalação das seguintes bibliotecas:

* pandas 
* pandasql 
* openai (versão 0.28)

adicionalmente, para a interface gráfica, precisaremos de:

* tkinter (nativo do python)
* PIL

Além disso é necessário um arquivo, chamado "openai_api_key.py" apenas para definir
sua chave de acesso à openai. 

Este arquivo deve apenas definir uma única variável, "KEY", que será sua chave de acesso.

## Utilização 

Podemos utilizar o arquivo "Pergunta_LLM.py" para fazer uma pergunta em linguagem natural
no contexto do trabalho, utilizando linha de comando.

Por exemplo:

> python pergunta_LLM.py "Qual cliente tem a pior qualidade na aplicação de vídeo streaming?"

Qualquer pergunta pode ser feita através do primeiro argumento de linha de comando.

Ao invés de se utilizar linha de comando, o usuário poderá também executar "gui.py", para
então abrir uma pequena interface gráfica, que apenas facilita a digitação de perguntas 
em linguagem natural e o recebimento de respostas.  

## Exemplos

Alguns exemplos de perguntas são feitos no notebook jupyter "exemplos.ipynb".