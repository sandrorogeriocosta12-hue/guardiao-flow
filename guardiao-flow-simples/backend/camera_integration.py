import requests
import cv2
import numpy as np
import pytesseract
import re
import os
from datetime import datetime
from models import db, PlacaReconhecida

# Configurações da câmera Hikvision (substitua pelos dados da sua câmera)
CAMERA_IP = "192.168.1.100"
CAMERA_USER = "admin"
CAMERA_PASSWORD = "senha"
CAMERA_CHANNEL = 1

def capturar_imagem():
    """Captura um frame da câmera Hikvision via HTTP."""
    url = f"http://{CAMERA_IP}/ISAPI/Streaming/channels/{CAMERA_CHANNEL}/picture"
    try:
        response = requests.get(url, auth=(CAMERA_USER, CAMERA_PASSWORD), timeout=5)
        if response.status_code == 200:
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
    except Exception as e:
        print(f"Erro ao capturar imagem: {e}")
    return None

def reconhecer_placa(imagem):
    """Aplica OCR para encontrar placas no padrão brasileiro (ABC1234 ou ABC1D23)."""
    # Pré-processamento simples
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Configurar Tesseract para reconhecer apenas caracteres alfanuméricos
    custom_config = r'--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    texto = pytesseract.image_to_string(thresh, config=custom_config)
    
    # Limpar e validar padrão de placa
    placa = re.sub(r'[^A-Z0-9]', '', texto.upper())
    # Padrão antigo: 3 letras + 4 números
    if re.match(r'^[A-Z]{3}[0-9]{4}$', placa):
        return placa
    # Padrão Mercosul: 3 letras + 1 número + 1 letra + 2 números
    elif re.match(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', placa):
        return placa
    return None

def verificar_entrada_saida():
    """Função que pode ser chamada periodicamente para capturar e reconhecer placas."""
    imagem = capturar_imagem()
    if imagem is None:
        return
    placa = reconhecer_placa(imagem)
    if placa:
        # Salvar imagem em disco
        filename = f"static/placas/{placa}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        cv2.imwrite(filename, imagem)
        
        # Registrar no banco
        registro = PlacaReconhecida(
            placa=placa,
            imagem_path=filename,
            camera_id=CAMERA_IP
        )
        db.session.add(registro)
        db.session.commit()
        
        # Aqui você pode associar a placa a uma visita ativa, por exemplo
        print(f"Placa reconhecida: {placa}")
    else:
        print("Nenhuma placa identificada.")
