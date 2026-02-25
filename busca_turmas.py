import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Função para buscar dados da planilha Google

def buscar_turmas_google():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('plated-field-474017-b8-e00d977b2612 copy.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key('1L3__zibMom2PjBN0nloVq44sM45OURncv4sxh8V6FuY')
    ws = sheet.worksheet('CRONOGRAMA')
    # Busca linhas 7 a 51, colunas A a N
    dados = ws.get('A7:N51')
    df = pd.DataFrame(dados[1:], columns=dados[0])
    return df

if __name__ == '__main__':
    turmas = buscar_turmas_google()
    print(turmas.head())
