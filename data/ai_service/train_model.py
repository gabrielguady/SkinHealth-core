import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import torchvision.transforms as transforms
import timm
import os
import copy
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import numpy as np

# Importe a arquitetura do seu modelo
from model_architecture import CustomEfficientNet

# --- Configurações de Treinamento ---
# Caminho para a pasta raiz dos seus dados (SkinHealth-core/data/dermatology)
# CORREÇÃO DEFINITIVA: 'ai_service' e 'dermatology' são IRMÃS DENTRO DA PASTA 'data'
DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dermatology')


# Caminhos específicos para as pastas de treino, validação e teste com as subpastas aninhadas
TRAIN_DIR = os.path.join(DATA_ROOT, 'training', 'train')
VAL_DIR = os.path.join(DATA_ROOT, 'validation', 'valid')
TEST_DIR = os.path.join(DATA_ROOT, 'test', 'test')

# Caminho para o seu arquivo .pth original (está na mesma pasta 'models')
CLASSIFIER_MODEL_PATH = 'models/tf_efficientnet_b0_aa-827b6e33.pth'

# Onde o modelo treinado será salvo (dentro da pasta 'models')
MODEL_SAVE_PATH = 'models/my_lesion_classifier_trained_v1.pth'

NUM_CLASSES = 3 # Agora são 3 classes: melanoma, nevus, seborrheic_keratosis
BATCH_SIZE = 32
NUM_EPOCHS = 30 # Ajuste conforme necessário
LEARNING_RATE_CLASSIFIER = 0.001
LEARNING_RATE_FINE_TUNE = 0.00001

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# --- Adicionar esta linha para proteger a execução principal ---
if __name__ == '__main__':
    # --- 1. Definição das Transformações da Imagem ---
    train_transforms = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_test_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # --- 2. Carregamento dos Dados ---
    try:
        train_dataset = ImageFolder(TRAIN_DIR, transform=train_transforms)
        val_dataset = ImageFolder(VAL_DIR, transform=val_test_transforms)
        test_dataset = ImageFolder(TEST_DIR, transform=val_test_transforms)

        # Define as classes com base no dataset de treinamento
        CLASS_NAMES = train_dataset.classes
        print(f"Classes encontradas: {CLASS_NAMES}")
        # Verifique a ordem das classes. ImageFolder ordena alfabeticamente:
        # ['melanoma', 'nevus', 'seborrheic_keratosis']
        # Confirme qual índice corresponde a 'melanoma'. Se for 'melanoma' a classe 0, use pos_label=0

        # Determinar o índice da classe 'melanoma' para métricas binárias
        if 'melanoma' in CLASS_NAMES:
            MELANOMA_CLASS_IDX = CLASS_NAMES.index('melanoma')
        else:
            print("Aviso: 'melanoma' não encontrada nas classes do dataset. Verifique a estrutura.")
            MELANOMA_CLASS_IDX = None # Não poderá calcular métricas binárias específicas para melanoma


        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=os.cpu_count() // 2 or 1)
        val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=os.cpu_count() // 2 or 1)
        test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=os.cpu_count() // 2 or 1)

    except Exception as e:
        print(f"Erro ao carregar datasets: {e}")
        print("Verifique se as pastas de dados existem e estão na estrutura correta (data/dermatology/training/train/melanoma, etc.).")
        exit() # Interrompe o script se os dados não puderem ser carregados

    # --- 3. Carregamento e Preparação do Modelo ---
    model = CustomEfficientNet(num_classes=NUM_CLASSES) # Instancia com 3 classes

    try:
        state_dict_original = torch.load(CLASSIFIER_MODEL_PATH, map_location='cpu')

        new_state_dict = {}
        for k, v in state_dict_original.items():
            if not (k.startswith('classifier.') or k.startswith('base_model.classifier.')):
                if not k.startswith('base_model.'):
                    new_state_dict['base_model.' + k] = v
                else:
                    new_state_dict[k] = v
        model.load_state_dict(new_state_dict, strict=False)

        print(f"Base do modelo '{CLASSIFIER_MODEL_PATH}' carregada com sucesso.")

    except Exception as e:
        print(f"Erro ao carregar a base do modelo pré-treinado: {e}")
        print("Certifique-se de que o arquivo .pth está em 'ai_service/models/'.")
        print("Continuando com EfficientNet_B0 totalmente inicializado aleatoriamente (não recomendado, a menos que seja um treinamento do zero).")

    model.to(DEVICE)

    # --- 4. Função de Perda ---
    criterion = nn.CrossEntropyLoss()

    # --- 5. Loop de Treinamento ---
    best_val_accuracy = 0.0
    best_model_wts = copy.deepcopy(model.state_dict())

    # FASE 1: Treinar apenas o classificador (Camada linear final)
    print("\n--- Iniciando Treinamento da Camada Classificadora ---")
    for param in model.base_model.parameters():
        param.requires_grad = False
    for param in model.base_model.classifier.parameters():
        param.requires_grad = True

    optimizer_classifier = optim.Adam(model.base_model.classifier.parameters(), lr=LEARNING_RATE_CLASSIFIER)

    for epoch in range(NUM_EPOCHS // 2):
        model.train()
        running_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            optimizer_classifier.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer_classifier.step()
            running_loss += loss.item() * inputs.size(0)

        epoch_loss = running_loss / len(train_dataset)
        print(f"Época {epoch+1}/{NUM_EPOCHS} (Classificador) - Loss: {epoch_loss:.4f}")

        # Validação
        model.eval()
        all_labels = []
        all_preds = []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                all_labels.extend(labels.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
        val_accuracy = accuracy_score(all_labels, all_preds) # Usando accuracy_score do sklearn
        print(f"Val Accuracy (Classificador): {val_accuracy:.4f}")

        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            best_model_wts = copy.deepcopy(model.state_dict())
            print(f"Melhor modelo (Classificador) salvo com acurácia: {best_val_accuracy:.4f}")

    model.load_state_dict(best_model_wts)

    # FASE 2: Fine-tuning do Modelo Completo
    print("\n--- Iniciando Fine-tuning do Modelo Completo ---")
    for param in model.parameters():
        param.requires_grad = True

    optimizer_fine_tune = optim.Adam(model.parameters(), lr=LEARNING_RATE_FINE_TUNE)

    for epoch in range(NUM_EPOCHS // 2, NUM_EPOCHS):
        model.train()
        running_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            optimizer_fine_tune.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer_fine_tune.step()
            running_loss += loss.item() * inputs.size(0)

        epoch_loss = running_loss / len(train_dataset)
        print(f"Época {epoch+1}/{NUM_EPOCHS} (Fine-tuning) - Loss: {epoch_loss:.4f}")

        # Validação
        model.eval()
        all_labels = []
        all_preds = []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                all_labels.extend(labels.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
        val_accuracy = accuracy_score(all_labels, all_preds)
        print(f"Val Accuracy (Fine-tuning): {val_accuracy:.4f}")

        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            best_model_wts = copy.deepcopy(model.state_dict())
            print(f"Melhor modelo (Fine-tuning) salvo com acurácia: {best_val_accuracy:.4f}")

    # --- 6. Salvar o Melhor Modelo Treinado ---
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"\nTreinamento concluído! Melhor modelo salvo em: {MODEL_SAVE_PATH}")

    # --- 7. Avaliação Final no Conjunto de Teste ---
    print("\n--- Avaliação Final no Conjunto de Teste ---")
    model.eval()
    all_labels = []
    all_preds = []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())

    y_true = np.array(all_labels)
    y_pred = np.array(all_preds)

    final_accuracy = accuracy_score(y_true, y_pred)
    conf_matrix = confusion_matrix(y_true, y_pred)

    print(f"Acurácia Final no Teste: {final_accuracy:.4f}")
    print("\nMatriz de Confusão Final:")
    print(conf_matrix)
    print(f"  {CLASS_NAMES[0]} Predito | {CLASS_NAMES[1]} Predito | {CLASS_NAMES[2]} Predito")
    print(f"{CLASS_NAMES[0]} Real    | {conf_matrix[0,0]}          | {conf_matrix[0,1]}          | {conf_matrix[0,2]}")
    print(f"{CLASS_NAMES[1]} Real    | {conf_matrix[1,0]}          | {conf_matrix[1,1]}          | {conf_matrix[1,2]}")
    print(f"{CLASS_NAMES[2]} Real    | {conf_matrix[2,0]}          | {conf_matrix[2,1]}          | {conf_matrix[2,2]}")


    # Métricas BINÁRIAS (Melanoma vs. Outros)
    if MELANOMA_CLASS_IDX is not None:
        # Criar rótulos binários: 1 para melanoma, 0 para outros
        y_true_binary = (y_true == MELANOMA_CLASS_IDX).astype(int)
        y_pred_binary = (y_pred == MELANOMA_CLASS_IDX).astype(int)

        final_precision_melanoma = precision_score(y_true_binary, y_pred_binary, average='binary', pos_label=1)
        final_recall_melanoma = recall_score(y_true_binary, y_pred_binary, average='binary', pos_label=1)
        final_f1_melanoma = f1_score(y_true_binary, y_pred_binary, average='binary', pos_label=1)

        print(f"\n--- Métricas Específicas para 'Melanoma' (vs. Outros) ---")
        print(f"Precisão Final (Melanoma) no Teste: {final_precision_melanoma:.4f}")
        print(f"Recall Final (Sensibilidade a Melanoma) no Teste: {final_recall_melanoma:.4f}")
        print(f"F1-Score Final (Melanoma) no Teste: {final_f1_melanoma:.4f}")
    else:
        print("\nNão foi possível calcular métricas binárias específicas para 'melanoma' (classe não encontrada).")