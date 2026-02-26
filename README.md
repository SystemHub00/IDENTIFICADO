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

1. Faça upload de todos os arquivos do projeto, exceto o .venv e arquivos locais.
2. No painel do Render, crie um novo serviço Web e aponte para este repositório.
3. O Render detecta automaticamente o `requirements.txt` e o `Procfile`.
4. Adicione a chave de credenciais JSON (identificador-488615-c1ab55e9b31b.json) como um arquivo no projeto. **Nunca exponha publicamente em repositórios públicos!**
5. Se preferir, use variáveis de ambiente para o caminho da chave JSON e o ID da planilha:
    - Exemplo no Render: `GOOGLE_APPLICATION_CREDENTIALS=identificador-488615-c1ab55e9b31b.json`
    - Exemplo no código:
       ```python
       cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'identificador-488615-c1ab55e9b31b.json')
       creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
       ```
6. O comando de start já está correto: `gunicorn app:app`
7. O serviço ficará disponível em uma URL fornecida pelo Render.

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
