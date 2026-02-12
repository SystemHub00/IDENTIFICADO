
import os
import threading
import csv
import cv2
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tkinter as tk
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

CAMINHO_CREDENCIAL = r"C:\Users\lucas\OneDrive\Documentos\IDENTIFICADO\presenca.csv"
PLANILHA_ID = "1z4IoxPNgEnL0hLgC5eriOkINmHfcjm99lsZRoE2UYq0"
NOME_ABA_DESTINO = "PRESENÇAS CONFIRMADAS - PAUTAS"

# Cores
COR_AZUL_ESCURO = "#0A1E3F"
COR_VERMELHO_ESCURO = "#7A0B0B"
COR_VERMELHO_HOVER = "#9C1A1A"
COR_BRANCO = "#FFFFFF"

# Estado global simples
_scan_thread = None
_scanning = False


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
	pass  # Não faz nada, envio para planilha removido


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


def _scan_loop(root, btn):
	global _scanning
	ids_validos = carregar_ids()
	cap = cv2.VideoCapture(0)
	# Aumenta a resolução para melhorar a leitura do QR
	cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
	if not cap.isOpened():
		print("Não foi possível acessar a câmera.")
		root.after(0, lambda: _finalizar_scan_ui(btn))
		return

	id_encontrado_valido = None
	detector = cv2.QRCodeDetector()

	while _scanning:
		ret, frame = cap.read()
		if not ret:
			break

		achou = False
		# 1) Tenta detecção múltipla do OpenCV
		retval, decoded_info, points, _ = detector.detectAndDecodeMulti(frame)
		if retval and decoded_info is not None:
			for i, text in enumerate(decoded_info):
				if not text:
					continue
				id_lido = text.strip()
				cor = (0, 255, 0) if id_lido in ids_validos else (0, 0, 255)
				if points is not None and len(points) > i and points[i] is not None:
					pts = np.array(points[i], dtype=np.int32).reshape((-1, 1, 2))
					cv2.polylines(frame, [pts], True, cor, 2)
				if id_lido in ids_validos:
					id_encontrado_valido = id_lido
					achou = True
					break

		# 2) Se não achou, tenta detecção simples do OpenCV
		if not achou:
			text, points, _ = detector.detectAndDecode(frame)
			if text:
				id_lido = text.strip()
				cor = (0, 255, 0) if id_lido in ids_validos else (0, 0, 255)
				if points is not None and len(points) > 0:
					pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
					cv2.polylines(frame, [pts], True, cor, 2)
				if id_lido in ids_validos:
					id_encontrado_valido = id_lido
					achou = True

		# 3) Se ainda não achou, tenta pyzbar (se disponível)
		if not achou and HAS_PYZBAR:
			for qr in zbar_decode(frame):
				id_lido = qr.data.decode('utf-8').strip()
				cor = (0, 255, 0) if id_lido in ids_validos else (0, 0, 255)
				try:
					pts = np.array([[p.x, p.y] for p in qr.polygon], dtype=np.int32).reshape((-1, 1, 2))
					cv2.polylines(frame, [pts], True, cor, 2)
				except Exception:
					pass
				if id_lido in ids_validos:
					id_encontrado_valido = id_lido
					achou = True
					break

		# 4) Se ainda não achou, tenta Pharmacode
		if not achou:
			valor_pharma, bbox = _tentar_pharmacode(frame)
			if valor_pharma is not None:
				cor = (0, 255, 0) if valor_pharma in ids_validos else (0, 0, 255)
				if bbox is not None:
					x,y,w,h = bbox
					cv2.rectangle(frame, (x,y), (x+w, y+h), cor, 2)
				if valor_pharma in ids_validos:
					id_encontrado_valido = valor_pharma
					achou = True

		cv2.imshow('', frame)

		# Fecha com ESC
		k = cv2.waitKey(1) & 0xFF
		if k == 27:  # ESC
			break

		if achou:
			break

	_scanning = False
	cap.release()
	cv2.destroyAllWindows()

	if id_encontrado_valido:
		salvar_presenca_local(id_encontrado_valido)
		enviar_linha_para_planilha('SIM', id_encontrado_valido)

	root.after(0, lambda: _finalizar_scan_ui(btn))


def _finalizar_scan_ui(btn):
	btn.config(state=tk.NORMAL, text="INICIALIZAR", bg=COR_VERMELHO_ESCURO, activebackground=COR_VERMELHO_ESCURO, cursor="hand2")


def iniciar_scan(root, btn):
	global _scan_thread, _scanning
	if _scanning:
		return
	_scanning = True
	btn.config(state=tk.DISABLED, text="LENDO...", bg="#444444", activebackground="#444444", cursor="wait")
	_scan_thread = threading.Thread(target=_scan_loop, args=(root, btn), daemon=True)
	_scan_thread.start()


def criar_interface():
	root = tk.Tk()
	root.title("")  # sem texto
	root.configure(bg=COR_BRANCO)
	# Tela cheia (Windows: zoomed; fallback: fullscreen)
	try:
		root.state('zoomed')
	except Exception:
		root.attributes('-fullscreen', True)
	root.resizable(False, False)

	# Define ícone da janela se possível
	try:
		if os.path.exists(LOGO_PATH):
			logo_img_icon = tk.PhotoImage(file=LOGO_PATH)
			root.iconphoto(False, logo_img_icon)
	except Exception:
		pass

	# Container central
	container = tk.Frame(root, bg=COR_BRANCO)
	container.pack(expand=True, fill="both")

	# Logo (sem texto)
	logo_img = None
	if os.path.exists(LOGO_PATH):
		try:
			logo_img = tk.PhotoImage(file=LOGO_PATH)
			logo_label = tk.Label(container, image=logo_img, bg=COR_BRANCO, borderwidth=0, highlightthickness=0)
			logo_label.image = logo_img  # manter referência
			logo_label.pack(pady=20)
		except Exception:
			# Se não carregar, apenas ignora
			pass

	# Botão de ativar estilizado
	btn = tk.Button(
		container,
		text="ATIVAR",
		bg=COR_VERMELHO_ESCURO,
		activebackground=COR_VERMELHO_ESCURO,
		fg=COR_BRANCO,
		borderwidth=0,
		highlightthickness=0,
		font=("Segoe UI", 16, "bold"),
		padx=24,
		pady=12,
		cursor="hand2",
		command=lambda: iniciar_scan(root, btn)
	)
	btn.pack(pady=20)

	# Efeito hover
	def _on_enter(e):
		if str(btn["state"]) == "normal":
			btn.configure(bg=COR_VERMELHO_HOVER, activebackground=COR_VERMELHO_HOVER)

	def _on_leave(e):
		if str(btn["state"]) == "normal":
			btn.configure(bg=COR_VERMELHO_ESCURO, activebackground=COR_VERMELHO_ESCURO)

	btn.bind("<Enter>", _on_enter)
	btn.bind("<Leave>", _on_leave)

	# Rodapé (faixa azul)
	rodape = tk.Frame(root, height=8, bg=COR_AZUL_ESCURO)
	rodape.pack(side="bottom", fill="x")

	return root



# Função para identificar código sem interface gráfica

def identifica():
	ids_validos = carregar_ids()
	cap = cv2.VideoCapture(0)
	cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
	detector = cv2.QRCodeDetector()
	id_encontrado_valido = None
	for _ in range(300):  # tenta por até ~10 segundos
		ret, frame = cap.read()
		if not ret:
			continue
		codigo_encontrado = None
		# 1) OpenCV QRCode
		retval, decoded_info, points, _ = detector.detectAndDecodeMulti(frame)
		if retval and decoded_info is not None:
			for text in decoded_info:
				print(f"[DEBUG] QRCodeDetector detectAndDecodeMulti: '{text}'", flush=True)
				if text and text.strip():
					codigo_encontrado = text.strip()
					break
		# 2) OpenCV simples
		if not codigo_encontrado:
			text, points, _ = detector.detectAndDecode(frame)
			print(f"[DEBUG] QRCodeDetector detectAndDecode: '{text}'", flush=True)
			if text and text.strip():
				codigo_encontrado = text.strip()
		# 3) pyzbar
		if not codigo_encontrado and HAS_PYZBAR:
			for qr in zbar_decode(frame):
				id_lido = qr.data.decode('utf-8').strip()
				print(f"[DEBUG] pyzbar: '{id_lido}'", flush=True)
				if id_lido:
					codigo_encontrado = id_lido
					break
		# 4) Pharmacode
		if not codigo_encontrado:
			valor_pharma, _ = _tentar_pharmacode(frame)
			print(f"[DEBUG] Pharmacode: '{valor_pharma}'", flush=True)
			if valor_pharma:
				codigo_encontrado = valor_pharma

		# Mostra a imagem da câmera
		cv2.imshow('Leitura do Código', frame)
		if cv2.waitKey(1) & 0xFF == 27:  # ESC para sair
			break

		if codigo_encontrado:
			cap.release()
			cv2.destroyAllWindows()
			return codigo_encontrado

	cap.release()
	cv2.destroyAllWindows()
	return None

# Função para marcar presença apenas no Google Sheets
def marcar_presenca_csv(_codigo):
	import gspread
	from oauth2client.service_account import ServiceAccountCredentials
	SHEET_ID = "1eCwTf7mSidxiOeN_F5Jvipu_96H-Js9goQbX27IwdyM"
	ABA = "Página1"
	CHAVE = r"C:\Users\lucas\OneDrive\Documentos\IDENTIFICADO\plated-field-474017-b8-e00d977b2612 copy.json"
	try:
		scope = [
			"https://spreadsheets.google.com/feeds",
			"https://www.googleapis.com/auth/drive",
			"https://www.googleapis.com/auth/spreadsheets"
		]
		creds = ServiceAccountCredentials.from_json_keyfile_name(CHAVE, scope)
		client = gspread.authorize(creds)
		sheet = client.open_by_key(SHEET_ID).worksheet(ABA)
		sheet.append_row(['presença', _codigo], value_input_option='RAW')
		print('PRESENÇA LANÇADA NO GOOGLE SHEETS')
	except Exception as e:
		print(f'Não foi possível gravar no Google Sheets: {e}')
		print('Salvando presença localmente no CSV...')
		salvar_presenca_local(_codigo)
		print('Presença salva no arquivo CSV local.')

if __name__ == "__main__":
	print("Iniciando leitura da câmera para código de barras...")
	codigo = identifica()
	if codigo:
		print(f"Código reconhecido: {codigo}")
		print("Lançando pauta...")
		marcar_presenca_csv(codigo)
		print("Processo concluído!")
	else:
		print("Nenhum código válido identificado.")
