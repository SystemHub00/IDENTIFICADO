import os
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify, render_template, redirect, url_for, session


app = Flask(__name__)


# Função para registrar presença na planilha PAUTAS (POST)
def salvar_presenca_google(id_encontrado, turma):
	import datetime
	hora = datetime.datetime.now().strftime('%H:%M:%S')
	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
	cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'identificador-488615-c1ab55e9b31b.json')
	if not os.path.exists(cred_path):
		creds_content = os.environ.get('GOOGLE_SHEETS_CREDS_CONTENT')
		if creds_content:
			with open(cred_path, 'w') as f:
				f.write(creds_content)
	creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
	client = gspread.authorize(creds)
	sheet = client.open_by_key('1modnQG15Cdz0Ubu9TDqsbLybzhINmLfyg4CdKl4DGW0')
	aba_pautas = os.environ.get('GOOGLE_SHEETS_TAB_PAUTAS', 'PAUTAS')
	ws = sheet.worksheet(aba_pautas)
	# Garante que a presença será registrada sempre na primeira linha vazia abaixo dos dados existentes
	valores = ws.get_all_values()
	ultima_linha = len(valores) + 1
	if ultima_linha < 2:
		ultima_linha = 2
	ws.insert_row(['SIM', id_encontrado, hora, turma], ultima_linha)

# API para registrar presença
@app.route('/registrar', methods=['POST'])
def registrar():
	data = request.get_json()
	id_encontrado = data.get('id') if data else None
	if not id_encontrado:
		return jsonify({'sucesso': False, 'mensagem': 'ID não informado.'})
	aluno = alunos.get(id_encontrado)
	if not aluno:
		return jsonify({'sucesso': False, 'mensagem': 'Aluno não encontrado.'})
	turma = aluno['curso']
	salvar_presenca_google(id_encontrado, turma)
	return jsonify({'sucesso': True, 'mensagem': f'Presença registrada para o curso: {turma}'}), 200
import os
import csv
alunos = {
	"123456789101": {"nome": "lucas", "curso": "administração"}
}
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'chave-secreta-para-session'

# Página inicial
@app.route('/', methods=['GET'])
def pagina_inicial():
	return render_template('bemvindo.html')


def buscar_turmas_google_sheet():
	# Lê as turmas da planilha Google correta
	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
	cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'identificador-488615-c1ab55e9b31b.json')
	# Se não existir o arquivo, cria a partir da variável de ambiente GOOGLE_SHEETS_CREDS_CONTENT
	if not os.path.exists(cred_path):
		creds_content = os.environ.get('GOOGLE_SHEETS_CREDS_CONTENT')
		if creds_content:
			with open(cred_path, 'w') as f:
				f.write(creds_content)
	creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
	client = gspread.authorize(creds)
	sheet = client.open_by_key('1modnQG15Cdz0Ubu9TDqsbLybzhINmLfyg4CdKl4DGW0')
	aba_turmas = os.environ.get('GOOGLE_SHEETS_TAB_TURMAS', 'TURMAS')
	ws = sheet.worksheet(aba_turmas)
	dados = ws.get('A3:F20')
	colunas = ['CURSOS', 'INICIO', 'FIM', 'HORÁRIO', 'LOCAL', 'OBSERVAÇÃO']
	turmas = []
	for row in dados:
		if len(row) < 6:
			# Preenche campos faltantes com vazio
			row += [''] * (6 - len(row))
		turma = dict(zip(colunas, row))
		turmas.append(turma)
	return turmas


@app.route('/turmas', methods=['GET'])
def escolher_turma():
	turmas = buscar_turmas_google_sheet()
	return render_template('selecionar_turma.html', turmas=turmas)

# Recebe turma escolhida e redireciona para registro
@app.route('/selecionar_turma', methods=['POST'])
def selecionar_turma():
	turma = request.form.get('turma')
	if not turma:
		return redirect(url_for('escolher_turma'))
	session['turma'] = turma
	return redirect(url_for('pagina_cartinha'))

@app.route('/cartinha', methods=['GET'])
def pagina_cartinha():
	return render_template('ler_qrcode.html')
	for _ in range(60):  # tenta por até ~2 segundos
		ret, frame = cap.read()
		if not ret:
			continue
		# 1) OpenCV QRCode
		retval, decoded_info, points, _ = detector.detectAndDecodeMulti(frame)
		if retval and decoded_info is not None:
			for text in decoded_info:
				if text and text.strip() in ids_validos:
					id_encontrado_valido = text.strip()
					break
		if id_encontrado_valido:
			break
		# 3) pyzbar
		if not id_encontrado_valido and HAS_PYZBAR:
			for qr in zbar_decode(frame):
				id_lido = qr.data.decode('utf-8').strip()
				if id_lido in ids_validos:
					id_encontrado_valido = id_lido
					break
