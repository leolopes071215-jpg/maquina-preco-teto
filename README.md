# Máquina de Preço-Teto

Ferramenta educacional em Python + Streamlit para estimar preço-teto de ações com base em lucro líquido sustentável, fluxo de caixa livre, múltiplos justos e margem de segurança.

## Objetivo do projeto

O objetivo da Máquina de Preço-Teto é ajudar investidores a organizar premissas de valuation de forma clara, visual e racional.

A ferramenta calcula um preço justo estimado e um preço-teto conservador, considerando:

* lucro líquido sustentável;
* fluxo de caixa livre;
* quantidade de ações;
* EPS normalizado;
* FCF por ação;
* múltiplo justo de EPS;
* múltiplo justo de FCF;
* pesos entre EPS e FCF;
* margem de segurança;
* preço atual;
* status automático: compra, neutro ou aguarde.

## Aviso importante

Esta ferramenta é apenas educacional.

Ela não representa recomendação de compra, venda ou manutenção de investimentos. Os resultados dependem diretamente das premissas inseridas pelo usuário.

Antes de tomar qualquer decisão financeira, é necessário estudar a empresa, os riscos, o setor, a qualidade dos lucros, a estrutura de capital, a gestão e o valuation com profundidade.

## Funcionalidades atuais

* Cálculo de EPS normalizado;
* Cálculo de FCF por ação;
* Cálculo de preço justo por EPS;
* Cálculo de preço justo por FCF;
* Cálculo de preço justo combinado;
* Cálculo de preço-teto com margem de segurança;
* Status automático: COMPRA, NEUTRO ou AGUARDE;
* Explicação automática do status;
* Cadastro de empresas e premissas;
* Tese qualitativa da empresa;
* Principais riscos;
* Fundamentos observados;
* Fonte das premissas;
* Histórico de análises em CSV;
* Download do histórico;
* Comparativo entre empresas;
* Moeda dinâmica: R$ ou US$;
* Interface visual em Streamlit.

## Empresas cadastradas

Atualmente, o projeto possui:

* Empresa Exemplo;
* Empresa de Qualidade;
* Empresa Cíclica;
* Mastercard;
* O'Reilly Automotive;
* Visa.

## Estrutura do projeto

maquina-preco-teto/
│
├── app.py
├── valuation.py
├── empresas.py
├── historico.py
├── comparativo.py
├── style.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── data/
└── historico_analises.csv

## Função de cada arquivo

### app.py

Arquivo principal da aplicação.

Responsável pela interface em Streamlit, campos de entrada, abas, botões, métricas e exibição dos resultados.

### valuation.py

Motor financeiro do projeto.

Contém as fórmulas para cálculo de EPS, FCF por ação, preço justo, preço-teto, status e explicação do status.

### empresas.py

Base de empresas cadastradas.

Armazena os dados financeiros, premissas, tese, riscos, fundamentos e fontes de cada empresa.

### historico.py

Responsável por salvar e carregar o histórico de análises em arquivo CSV.

### comparativo.py

Responsável por gerar a tabela comparativa entre as empresas cadastradas.

### style.py

Arquivo de estilo visual da aplicação.

Contém ajustes de aparência para deixar o app mais limpo e profissional.

### requirements.txt

Lista as bibliotecas necessárias para rodar o projeto.

### README.md

Documentação do projeto.

### .gitignore

Define os arquivos e pastas que não devem ser enviados ao GitHub.

## Como rodar o projeto localmente

### 1. Criar ambiente virtual

No terminal, dentro da pasta do projeto:

python -m venv .venv

### 2. Ativar ambiente virtual

No Windows PowerShell:

..venv\Scripts\activate

### 3. Instalar dependências

pip install -r requirements.txt

### 4. Rodar o app

python -m streamlit run app.py

Depois abra no navegador:

http://localhost:8501

## Comandos úteis de teste

Antes de rodar ou publicar o projeto, é recomendado testar os arquivos principais:

python -m py_compile app.py

python -m py_compile valuation.py

python -m py_compile empresas.py

python -m py_compile historico.py

python -m py_compile comparativo.py

python -m py_compile style.py

Se nenhum erro aparecer, os arquivos estão com a sintaxe correta.

## Lógica do status

### COMPRA

O preço atual está abaixo ou igual ao preço-teto calculado.

### NEUTRO

O preço atual está acima do preço-teto conservador, mas ainda abaixo ou próximo do preço justo estimado.

### AGUARDE

O preço atual está acima do preço justo estimado.

## Próximas melhorias planejadas

* Separar melhor dados financeiros, tese e fontes;
* Criar banco de dados mais robusto;
* Permitir cadastro de novas empresas pelo usuário;
* Criar login;
* Criar versão online;
* Criar filtros no comparativo;
* Adicionar gráficos;
* Criar página pública de análise por empresa;
* Automatizar parcialmente a atualização de dados;
* Criar plano gratuito e plano premium;
* Publicar o projeto na web.

## Status do projeto

MVP funcional em desenvolvimento.

O projeto já roda localmente, calcula valuation, salva histórico e compara empresas cadastradas.
