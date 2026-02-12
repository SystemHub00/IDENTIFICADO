import os
import csv

def salvar_presenca_local(id_encontrado):
	csv_path = r"C:\Users\lucas\OneDrive\Documentos\IDENTIFICADO\PRESENÇA.csv"
	# Garante cabeçalho
	if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
		with open(csv_path, 'w', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow(['PRESENTE', 'ID'])
	with open(csv_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerow(['SIM', id_encontrado])
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML_INDEX = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
	<meta charset="UTF-8">
	<title>Registro de Presença</title>
	<style>
		body { background: #0A1E3F; color: #fff; font-family: Arial, sans-serif; text-align: center; }
		.container { margin-top: 80px; }
		button { background: #7A0B0B; color: #fff; border: none; padding: 20px 40px; font-size: 2em; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
		button:hover { background: #9C1A1A; }
		#resultado { margin-top: 40px; font-size: 1.5em; }
		video { margin-top: 30px; border: 4px solid #7A0B0B; border-radius: 8px; }
	</style>
</head>
<body>
	<div class="container">
		<h1>Registro de Presença</h1>
		<video id="video" width="640" height="480" autoplay></video>
		<form id="form-presenca" method="post" action="/registrar">
			<input type="hidden" name="id" id="id-input">
			<button type="submit" style="display:none">Registrar</button>
		</form>
		<div id="resultado"></div>
	</div>

	<script src="https://unpkg.com/@zxing/library@latest"></script>
	<script>
		const codeReader = new ZXing.BrowserQRCodeReader(); // Apenas QR Code
		const video = document.getElementById('video');
		const resultado = document.getElementById('resultado');
		const idInput = document.getElementById('id-input');
		const form = document.getElementById('form-presenca');

		const CODIGO_ESPERADO = '123456789101';

		function startCamera() {
			codeReader.decodeFromVideoDevice(null, 'video', (result, err) => {
				if (result) {
					console.log('Valor lido pelo QR Code:', result.text);
					if (result.text === CODIGO_ESPERADO) {
						codeReader.reset();
						resultado.innerText = `Valor lido: "${result.text}" (QR Code autorizado! Enviando...)`;
						idInput.value = result.text;
						enviarPresenca(result.text);
					} else {
						resultado.innerText = `Valor lido: "${result.text}" (QR Code não autorizado). Aproxime o QR Code correto.`;
						// Permite nova leitura imediatamente
						codeReader.reset();
						setTimeout(() => startCamera(), 1500);
					}
				}
			});
		}

		function enviarPresenca(codigo) {
			fetch('/registrar', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ id: codigo })
			})
			.then(res => res.json())
			.then(data => {
				if (data.sucesso) {
					resultado.innerText = data.mensagem;
				} else {
					resultado.innerText = data.mensagem || 'Erro ao registrar.';
				}
			})
			.catch(() => {
				resultado.innerText = 'Erro ao registrar.';
			});
		}

		window.onload = () => {
			startCamera();
		};
	</script>
</body>
</html>
'''

@app.route('/')
def home():
	return render_template_string(HTML_INDEX)

@app.route('/registrar', methods=['POST'])
def registrar():
	data = request.get_json()
	id_encontrado = data.get('id') if data else None
	if not id_encontrado:
		return jsonify({'sucesso': False, 'mensagem': 'ID não informado.'})
	print(f'Valor recebido do QR Code: {id_encontrado}')
	if id_encontrado != '123456789101':
		return jsonify({'sucesso': False, 'mensagem': 'QR Code não autorizado.'}), 403
	try:
		salvar_presenca_local(id_encontrado)
		return jsonify({'sucesso': True, 'mensagem': 'Presença registrada com sucesso!'}), 200
	except Exception as e:
		return jsonify({'sucesso': False, 'mensagem': f'Erro ao registrar: {e}'}), 500

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=10000)
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML_INDEX = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
	<meta charset="UTF-8">
	<title>Registro de Presença</title>
	<style>
		body { background: #0A1E3F; color: #fff; font-family: Arial, sans-serif; text-align: center; }
		.container { margin-top: 80px; }
		button { background: #7A0B0B; color: #fff; border: none; padding: 20px 40px; font-size: 2em; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
		button:hover { background: #9C1A1A; }
		#resultado { margin-top: 40px; font-size: 1.5em; }
	</style>
</head>
<body>
	<div class="container">
		<h1>Registro de Presença</h1>
		<form id="form-presenca" method="post" action="/registrar">
			<input type="text" name="id" placeholder="Digite o ID" required style="font-size:1.2em;padding:10px;">
			<button type="submit">Registrar</button>
		</form>
		<div id="resultado">{{ resultado }}</div>
	</div>
	<script>
		const form = document.getElementById('form-presenca');
		form.onsubmit = async function(e) {
			e.preventDefault();
			document.getElementById('resultado').innerText = 'Registrando...';
			const formData = new FormData(form);
			const res = await fetch('/registrar', { method: 'POST', body: formData });
			const data = await res.json();
			if (data.sucesso) {
				document.getElementById('resultado').innerText = data.mensagem;
			} else {
				document.getElementById('resultado').innerText = data.mensagem || 'Erro ao registrar.';
			}
		}
	</script>
</body>
</html>
'''

@app.route('/')
def home():
	return render_template_string(HTML_INDEX, resultado='')

@app.route('/registrar', methods=['POST'])
def registrar():
	id_encontrado = request.form.get('id')
	if not id_encontrado:
		return jsonify({'sucesso': False, 'mensagem': 'ID não informado.'})
	try:
		enviar_linha_para_planilha('SIM', id_encontrado)
		return jsonify({'sucesso': True, 'mensagem': 'Presença registrada com sucesso! (Sheets ou CSV)'}), 200
	except Exception as e:
		return jsonify({'sucesso': False, 'mensagem': f'Erro ao registrar: {e}'}), 500

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=10000)

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

CAMINHO_CREDENCIAL = "C:/Users/lucas/OneDrive/Documentos/GitHub/F10-Software/Banco-De-Dados/Banco-De-Dados/Luziânia/n8n-credenciais-459013-b4f1ae5dd3c4.json"
PLANILHA_ID = "1z4IoxPNgEnL0hLgC5eriOkINmHfcjm99lsZRoE2UYq0"
NOME_ABA_DESTINO = "PRESENÇAS CONFIRMADAS - PAUTAS"

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


def salvar_presenca_local(id_encontrado):
	csv_path = r"C:\Users\lucas\OneDrive\Documentos\IDENTIFICADO\PRESENÇA.csv"
	# Garante cabeçalho
	if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
		with open(csv_path, 'w', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow(['PRESENTE', 'ID'])
	with open(csv_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerow(['SIM', id_encontrado])


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
		# Envia linha de presença
		sheet.append_row([presente, id_encontrado], value_input_option='RAW')
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
