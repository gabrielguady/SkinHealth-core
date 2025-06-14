import torch.nn as nn
import timm

class CustomEfficientNet(nn.Module):
    def __init__(self, num_classes=2):
        super(CustomEfficientNet, self).__init__()
        # Carrega o EfficientNet_b0 usando timm.create_model
        # pretrained=False porque vamos carregar os pesos do seu arquivo .pth separadamente
        self.base_model = timm.create_model('tf_efficientnet_b0_ns', pretrained=False)

        # Opcional: Congelar os parâmetros do modelo base, se você treinou apenas o classificador.
        # Se você fez fine-tuning, o ideal é congelar o base_model antes de treinar,
        # e talvez descongelar as últimas camadas depois.
        # Para inferência, é seguro mantê-los congelados.
        for param in self.base_model.parameters():
            param.requires_grad = False

        # Substitui a camada classificadora final para as 2 classes da sua tarefa.
        # O 'classifier' é o nome padrão do classificador em muitos modelos timm.
        # Pegamos o número de features de entrada da camada classificadora original.
        num_ftrs = self.base_model.classifier.in_features
        self.base_model.classifier = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.base_model(x)