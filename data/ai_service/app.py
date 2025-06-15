# C:\Users\Obeller\PycharmProjects\SkinHealth-core\data\ai_service\app.py

from flask import Flask, request, jsonify
import torch
import torchvision.transforms as transforms
from PIL import Image
import io # Usar 'io' em vez de 'BytesIO' diretamente para consistência, mas BytesIO também funciona
import os
import requests

# Importe a classe do modelo CustomEfficientNet
from model_architecture import CustomEfficientNet

app = Flask(__name__)

# --- Configurações do Modelo de CLASSIFICAÇÃO ---
# CORREÇÃO 1: Caminho para o SEU arquivo de modelo treinado
CLASSIFIER_MODEL_PATH = 'models/my_lesion_classifier_trained_v1.pth'
CLASSIFIER_DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
classifier_model = None

# CORREÇÃO 2: Número de classes deve ser 3, como o seu modelo foi treinado
NUM_CLASSES = 3

# CORREÇÃO 3: As classes na ordem correta, como ImageFolder as detectou
CLASSIFIER_CLASS_NAMES = ['melanoma', 'nevus', 'seborrheic_keratosis']

try:
    # Cria uma instância do seu CustomEfficientNet com o número correto de classes
    classifier_model = CustomEfficientNet(num_classes=NUM_CLASSES)

    # Carrega o state_dict do seu modelo JÁ TREINADO
    # Não precisamos do remapeamento complexo aqui, pois o .pth já está no formato correto
    classifier_model.load_state_dict(torch.load(CLASSIFIER_MODEL_PATH, map_location=CLASSIFIER_DEVICE))

    classifier_model.eval() # Coloca o modelo em modo de avaliação
    classifier_model.to(CLASSIFIER_DEVICE)
    print(f"Modelo Classificador '{CLASSIFIER_MODEL_PATH}' carregado no dispositivo: {CLASSIFIER_DEVICE}")
except Exception as e:
    print(f"Erro ao carregar o modelo Classificador: {e}")
    import traceback
    traceback.print_exc() # Isso imprime a pilha de chamadas para depuração
    classifier_model = None # Garante que o modelo é None se houver falha no carregamento

# --- Transformações da Imagem para o Classificador (DEVE SER IGUAL À VALIDAÇÃO/TESTE) ---
classifier_transforms = transforms.Compose([
    transforms.Resize((224, 224)), # Tamanho de entrada esperado pelo EfficientNet_B0
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

@app.route('/')
def home():
    return "API de Inferência de IA (Classificação de Lesões) está funcionando!"

@app.route('/predict', methods=['POST'])
def predict():
    if classifier_model is None:
        return jsonify({"error": "Modelo de IA não foi carregado. Verifique os logs do servidor."}), 500

    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({"error": "Nenhuma URL de imagem fornecida. Esperado {'image_url': '...'}"}), 400

    image_url = data['image_url']
    print(f"Recebendo requisição para imagem: {image_url}")

    try:
        response = requests.get(image_url)
        response.raise_for_status() # Levanta um erro para códigos de status HTTP 4xx/5xx

        # Usar io.BytesIO para ler os bytes como um arquivo
        img_pil = Image.open(io.BytesIO(response.content)).convert('RGB')

        input_tensor_classifier = classifier_transforms(img_pil).unsqueeze(0) # Adiciona dimensão do batch

        with torch.no_grad(): # Desativa o cálculo de gradientes para otimizar a inferência
            classifier_output = classifier_model(input_tensor_classifier.to(CLASSIFIER_DEVICE))
            classifier_probabilities = torch.nn.functional.softmax(classifier_output, dim=1)[0] # [0] para pegar o primeiro item do batch
            predicted_class_idx = torch.argmax(classifier_probabilities).item()
            classifier_confidence = round(classifier_probabilities[predicted_class_idx].item(), 4)
            classifier_result_text = CLASSIFIER_CLASS_NAMES[predicted_class_idx]

        return jsonify({
            "status": "success",
            "prediction": classifier_result_text, # Mudei 'result' para 'prediction' para clareza
            "confidence": classifier_confidence,
            "model_version": "efficientnet_classifier_v1.0"
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar imagem da URL '{image_url}': {e}")
        return jsonify({"error": f"Erro ao baixar imagem: {str(e)}"}), 400
    except Image.UnidentifiedImageError:
        print(f"Não foi possível identificar a imagem da URL: {image_url}")
        return jsonify({"error": "Formato de imagem inválido ou corrompido."}), 400
    except Exception as e:
        print(f"Erro inesperado durante a predição: {e}")
        return jsonify({"error": f"Erro interno do servidor de IA: {str(e)}"}), 500

if __name__ == '__main__':
    # Certifique-se de que Flask está instalado: pip install Flask
    # Para desenvolvimento, debug=True é útil. Para produção, defina como False.
    app.run(host='0.0.0.0', port=5000, debug=True)