
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

# Página de escanear carteirinha
@app.route('/cartinha', methods=['GET'])
def pagina_cartinha():
	return render_template('ler_qrcode.html')


# Página de registro de presença (desativada, só escaneamento agora)


# API para registrar presença (usada pelo JS)
@app.route('/registrar', methods=['POST'])
def registrar():
	data = request.get_json()
	id_encontrado = data.get('id') if data else None
	if not id_encontrado:
		return jsonify({'sucesso': False, 'mensagem': 'ID não informado.'})
	aluno = alunos.get(id_encontrado)
	if not aluno:
		return jsonify({'sucesso': False, 'mensagem': 'Aluno não encontrado.'}), 
	# Não busca mais turmas, apenas registra presença no Sheets
	turma = aluno['curso']
	salvar_presenca_local(id_encontrado, turma)
	return jsonify({'sucesso': True, 'mensagem': f'Presença registrada para o curso: {turma}'}), 200


import os
import threading
import csv
import cv2
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
try:
	from pyzbar.pyzbar import decode as zbar_decode
	HAS_PYZBAR = True
except Exception:
	HAS_PYZBAR = False

# Caminhos e constantes
BASE_DIR = r"c:\Users\lucas\Downloads\INDENTIFICADOR\Reconhecimento"
IDS_CSV = os.path.join(BASE_DIR, "IDS.csv")
PRESENCAS_CSV = os.path.join(BASE_DIR, "IDS-presenças.csv")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

CAMINHO_CREDENCIAL = "plated-field-474017-b8-e00d977b2612.json"
PLANILHA_ID = "1M4p8VgUiqvER8PPb0wttqKl7VfxEy7qtShKEWUbVx8M"
NOME_ABA_DESTINO = "presença"

# Cores
COR_AZUL_ESCURO = "#0A1E3F"
COR_VERMELHO_ESCURO = "#7A0B0B"
COR_VERMELHO_HOVER = "#9C1A1A"
COR_BRANCO = "#FFFFFF"


def carregar_ids():
	try:
		with open(IDS_CSV, newline='', encoding='utf-8') as f:
			return set(linha.strip() for linha in f if linha.strip())
	except FileNotFoundError:
		return set()


def garantir_cabecalho_csv():
	cabecalho = ['PRESENTE', 'ID']
	if not os.path.exists(PRESENCAS_CSV) or os.path.getsize(PRESENCAS_CSV) == 0:
		with open(PRESENCAS_CSV, 'w', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow(cabecalho)


def salvar_presenca_local(id_encontrado, turma):
	import datetime
	hora = datetime.datetime.now().strftime('%H:%M:%S')
	# Salvar presença diretamente no Google Sheets correto
	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
	cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'identificador-488615-c1ab55e9b31b.json')
	creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
	client = gspread.authorize(creds)
	sheet = client.open_by_key('1modnQG15Cdz0Ubu9TDqsbLybzhINmLfyg4CdKl4DGW0')
	ws = sheet.worksheet('PAUTAS')
	# Sempre lançar a partir da linha 2 (após o cabeçalho)
	ultima_linha = len(ws.get_all_values()) + 1
	if ultima_linha < 2:
		ultima_linha = 2
	ws.insert_row(['SIM', id_encontrado, hora, turma], ultima_linha)


def enviar_linha_para_planilha(presente, id_encontrado):
	try:
		scope = [
			"https://spreadsheets.google.com/feeds",
			"https://www.googleapis.com/auth/drive",
			"https://www.googleapis.com/auth/spreadsheets"
		]
		creds = ServiceAccountCredentials.from_json_keyfile_name(CAMINHO_CREDENCIAL, scope)
		client = gspread.authorize(creds)
		sheet = client.open_by_key(PLANILHA_ID).worksheet(NOME_ABA_DESTINO)
		# Garante cabeçalho na planilha
		try:
			primeira = sheet.acell('A1').value
		except Exception:
			primeira = None
		if not primeira:
			sheet.update('A1:B1', [['PRESENTE', 'ID']])
		# Encontra próxima linha vazia
		values = sheet.get_all_values()
		next_row = len(values) + 1
		sheet.update(f'A{next_row}:B{next_row}', [[presente, id_encontrado]])
		print('PRESENÇA LANÇADA NO GOOGLE SHEETS')
	except Exception as e:
		print(f'Não foi possível gravar no Google Sheets: {e}')
		print('Salvando presença localmente no CSV...')
		salvar_presenca_local(id_encontrado)
		print('Presença salva no arquivo CSV local.')


def _tentar_pharmacode(frame):
	"""Tentativa simples de detectar um padrão tipo Pharmacode.
	Retorna (valor_str, (x,y,w,h)) ou (None, None).
	Heurística: detectar região de alto contraste com barras verticais pretas separadas.
	"""
	try:
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		# Binariza com OTSU
		_, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
		# Fechamento para unir pequenas falhas
		kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
		closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)
		contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		candidatos = []
		for c in contours:
			x,y,w,h = cv2.boundingRect(c)
			area = w*h
			if area < 800 or h < 25 or w < 40:
				continue
			aspect = w / float(h)
			if aspect < 0.8:  # pharmacode é mais largo que alto normalmente
				continue
			candidatos.append((area, (x,y,w,h)))
		if not candidatos:
			return None, None
		# escolhe maior região candidata
		candidatos.sort(reverse=True)
		_, (x,y,w,h) = candidatos[0]
		roi = th[y:y+h, x:x+w]
		# Projeta nas colunas para identificar barras
		col_sum = roi.sum(axis=0)
		# Normaliza
		col_sum = (col_sum - col_sum.min()) / (col_sum.ptp() + 1e-6)
		# Limiar para decidir barras ativas
		mask = col_sum > 0.5
		# Agrupa sequências de True como barras
		barras = []
		start = None
		for i,val in enumerate(mask):
			if val and start is None:
				start = i
			elif not val and start is not None:
				barras.append((start, i-1))
				start = None
		if start is not None:
			barras.append((start, len(mask)-1))
		if len(barras) < 2:
			return None, None
		# Calcula larguras relativas (codificação simplificada, NÃO padrão oficial)
		larguras = [b[1]-b[0]+1 for b in barras]
		min_l = min(larguras)
		if min_l == 0:
			return None, None
		ratio = [round(l/min_l) for l in larguras]
		# Gera uma string representando o padrão ex: "1-2-1-3"
		valor = "-".join(str(r) for r in ratio[:12])  # limita tamanho
		return valor, (x,y,w,h)
	except Exception:
		return None, None


# Função para identificar código sem interface gráfica
def identifica():
	ids_validos = carregar_ids()
	cap = cv2.VideoCapture(0)
	cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
	detector = cv2.QRCodeDetector()
	id_encontrado_valido = None
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
		# 4) Pharmacode
		if not id_encontrado_valido:
			valor_pharma, _ = _tentar_pharmacode(frame)
			if valor_pharma and valor_pharma in ids_validos:
				id_encontrado_valido = valor_pharma
		if id_encontrado_valido:
			break
		cv2.waitKey(30)
	cap.release()
	cv2.destroyAllWindows()
	if id_encontrado_valido:
		salvar_presenca_local(id_encontrado_valido)
		enviar_linha_para_planilha('SIM', id_encontrado_valido)
		return id_encontrado_valido
	return None


if __name__ == "__main__":
	app.run(debug=True)
