# Sistema de Presença e Turmas

Este projeto é um sistema web para controle de presença e seleção de turmas, desenvolvido em Python com Flask.

## Funcionalidades
- Página inicial com botão Bem-vindo
- Seleção automática de turmas pelo horário atual
- Página para bater cartinha após seleção de turma
- Registro de presença com integração Google Sheets e CSV

## Como rodar localmente
1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
2. Execute o servidor:
   ```
   python app.py
   ```
3. Acesse `http://localhost:10000/inicio` no navegador.

## Deploy no Render
- O projeto já possui `requirements.txt` e `Procfile`.
- Use o comando:
  ```
  gunicorn app:app
  ```
  conforme definido no Procfile.

## Estrutura
- `app.py`: Código principal
- `requirements.txt`: Dependências
- `Procfile`: Configuração para deploy
- `PRESENÇA.csv`: Registro local de presença

## Observações
- Configure o arquivo de credenciais do Google Sheets corretamente.
- O sistema filtra turmas pelo horário e dia atual.

---

Qualquer dúvida ou ajuste, entre em contato!
