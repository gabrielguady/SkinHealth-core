# C:\Users\Obeller\PycharmProjects\SkinHealth-core\data\ai_service\app.py

from flask import Flask, request, jsonify
import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import requests

from model_architecture import CustomEfficientNet

app = Flask(__name__)

# --- Configurações do Modelo de CLASSIFICAÇÃO ---
CLASSIFIER_MODEL_PATH = 'models/my_lesion_classifier_trained_v1.pth'
CLASSIFIER_DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
classifier_model = None

NUM_CLASSES = 3
CLASSIFIER_CLASS_NAMES = ['melanoma', 'nevus', 'seborrheic_keratosis']

try:
    print(f"Tentando carregar modelo: {CLASSIFIER_MODEL_PATH}")

    classifier_model = CustomEfficientNet(num_classes=NUM_CLASSES)

    state_dict = torch.load(CLASSIFIER_MODEL_PATH, map_location=CLASSIFIER_DEVICE)

    corrected_state_dict = {}
    for k, v in state_dict.items():
        # Adiciona 'base_model.' como prefixo a todas as chaves
        prefixed_key = f'base_model.{k}'

        if "classifier" in k:
            print(f"Pulando chave do classificador: {k} (pois o modelo tem {NUM_CLASSES} classes)")
            continue

        corrected_state_dict[prefixed_key] = v

    classifier_model.load_state_dict(corrected_state_dict, strict=False)

    classifier_model.eval()
    classifier_model.to(CLASSIFIER_DEVICE)
    print(
        f"Modelo Classificador '{CLASSIFIER_MODEL_PATH}' (com cabeça de {NUM_CLASSES} classes) carregado no dispositivo: {CLASSIFIER_DEVICE}")

except Exception as e:
    print(f"Erro ao carregar o modelo Classificador: {e}")
    import traceback

    traceback.print_exc()
    classifier_model = None

classifier_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
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
        response.raise_for_status()

        img_pil = Image.open(io.BytesIO(response.content)).convert('RGB')

        input_tensor_classifier = classifier_transforms(img_pil).unsqueeze(0)

        with torch.no_grad():
            classifier_output = classifier_model(input_tensor_classifier.to(CLASSIFIER_DEVICE))
            classifier_probabilities = torch.nn.functional.softmax(classifier_output, dim=1)[0]
            predicted_class_idx = torch.argmax(classifier_probabilities).item()
            classifier_confidence = round(classifier_probabilities[predicted_class_idx].item(), 4)
            classifier_result_text = CLASSIFIER_CLASS_NAMES[predicted_class_idx]

        return jsonify({
            "status": "success",
            "prediction": classifier_result_text,
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
    app.run(host='0.0.0.0', port=5000, debug=True)