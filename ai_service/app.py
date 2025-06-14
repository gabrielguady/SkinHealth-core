import os
import torch
import torchvision.transforms as transforms
from PIL import Image
from flask import Flask, request, jsonify
from io import BytesIO
import requests

# Importe a classe do modelo CustomEfficientNet
from model_architecture import CustomEfficientNet

app = Flask(__name__)

# --- Configurações do Modelo de CLASSIFICAÇÃO ---
# Caminho para o seu arquivo de modelo EfficientNet
CLASSIFIER_MODEL_PATH = 'models/tf_efficientnet_b0_aa-827b6e33.pth' # <--- Seu arquivo .pth
CLASSIFIER_DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
classifier_model = None

try:
    # Carrega o state_dict bruto do arquivo .pth
    state_dict = torch.load(CLASSIFIER_MODEL_PATH, map_location=CLASSIFIER_DEVICE)

    new_state_dict = {}
    for k, v in state_dict.items():
        # Lógica de remapeamento e ignorar chaves do classificador original:
        # Se a chave *não* começa com 'classifier.' (indicando a camada classificadora do modelo timm original)
        # E se a chave *não* começa com 'base_model.classifier.' (apenas por segurança, se o .pth tivesse esse prefixo)
        if not (k.startswith('classifier.') or k.startswith('base_model.classifier.')):
            # Se a chave não tem o prefixo 'base_model.', adicionamos.
            # Isso é para alinhar com 'self.base_model' na sua CustomEfficientNet.
            if not k.startswith('base_model.'):
                new_state_dict['base_model.' + k] = v
            else:
                new_state_dict[k] = v
        # As chaves que começam com 'classifier.' ou 'base_model.classifier.' são ignoradas,
        # pois a arquitetura do seu CustomEfficientNet já define um novo classificador.

    # Cria uma instância do seu CustomEfficientNet
    # O classificador para 2 classes já é definido aqui.
    classifier_model = CustomEfficientNet(num_classes=2)

    # Carrega o state_dict ajustado (apenas para as camadas do modelo base).
    # strict=False é ESSENCIAL aqui porque estamos intencionalmente faltando as chaves
    # do classificador original do .pth (já que substituímos no CustomEfficientNet).
    classifier_model.load_state_dict(new_state_dict, strict=False)

    classifier_model.eval() # Coloca o modelo em modo de avaliação
    print(f"Modelo Classificador '{CLASSIFIER_MODEL_PATH}' carregado no dispositivo: {CLASSIFIER_DEVICE}")
except Exception as e:
    print(f"Erro ao carregar o modelo Classificador: {e}")
    import traceback
    traceback.print_exc() # Isso imprime a pilha de chamadas para depuração
    classifier_model = None

# --- Transformações da Imagem para o Classificador ---
classifier_transforms = transforms.Compose([
    transforms.Resize((224, 224)), # Tamanho de entrada esperado pelo EfficientNet_B0
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# As classes que seu modelo classifica (ajuste se necessário)
CLASSIFIER_CLASS_NAMES = ["benign", "malignant"]

@app.route('/')
def home():
    return "API de Inferência de IA (Classificação de Lesões) está funcionando!"

@app.route('/predict', methods=['POST'])
def predict():
    if classifier_model is None:
        return jsonify({"error": "Modelo de IA não foi carregado. Verifique os logs."}), 500

    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({"error": "Nenhuma URL de imagem fornecida. Esperado {'image_url': '...'}"}), 400

    image_url = data['image_url']
    print(f"Recebendo requisição para imagem: {image_url}")

    try:
        response = requests.get(image_url)
        response.raise_for_status()

        img_pil = Image.open(BytesIO(response.content)).convert('RGB')

        input_tensor_classifier = classifier_transforms(img_pil).unsqueeze(0)

        with torch.no_grad():
            classifier_output = classifier_model(input_tensor_classifier.to(CLASSIFIER_DEVICE))
            classifier_probabilities = torch.nn.functional.softmax(classifier_output, dim=1)[0]
            predicted_class_idx = torch.argmax(classifier_probabilities).item()
            classifier_confidence = round(classifier_probabilities[predicted_class_idx].item(), 4)
            classifier_result_text = CLASSIFIER_CLASS_NAMES[predicted_class_idx]

        return jsonify({
            "status": "success",
            "result": classifier_result_text,
            "confidence": classifier_confidence,
            "model_version": "efficientnet_classifier_v1.0"
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar imagem da URL '{image_url}': {e}")
        return jsonify({"error": f"Erro ao baixar imagem: {e}"}), 400
    except Image.UnidentifiedImageError:
        print(f"Não foi possível identificar a imagem da URL: {image_url}")
        return jsonify({"error": "Formato de imagem inválido ou corrompido."}), 400
    except Exception as e:
        print(f"Erro inesperado durante a predição: {e}")
        return jsonify({"error": f"Erro interno do servidor de IA: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)