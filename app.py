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
	creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
	client = gspread.authorize(creds)
	sheet = client.open_by_key('1modnQG15Cdz0Ubu9TDqsbLybzhINmLfyg4CdKl4DGW0')
	ws = sheet.worksheet('TURMAS')
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
