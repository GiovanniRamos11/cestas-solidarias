# Cestas Solidárias

MVP de controle de entrega de cestas básicas e estoque para uma associação comunitária.

## Problema
A associação controla entregas e estoque em cadernos diferentes. Não se sabe com segurança quem já recebeu a cesta no mês nem quanto resta de cada item.
## Solução
Sistema web, usado pelo celular, que registra uma entrega por família por mês, avisa sobre duplicidade e dá baixa automática no estoque.
## ODS
ODS 2 (Fome Zero e Agricultura Sustentável), meta 2.1.
## Tecnologias
Python, Django 5.2 LTS, Bootstrap 5.3, PostgreSQL (psycopg 3), Gunicorn e WhiteNoise.

## Como executar
1. Clone o repositório.
2. Crie e ative o ambiente virtual: `python -m venv .venv`
3. Instale as dependências: `pip install -r requirements.txt`
4. Copie `.env.example` para `.env` e preencha as variáveis.
5. Aplique as migrações: `python manage.py migrate`
6. Inicie o servidor: `python manage.py runserver`

## Testes
`python manage.py test`

## Aviso
Todos os dados de exemplo são fictícios.
