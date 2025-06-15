import torch.nn as nn
import timm

class CustomEfficientNet(nn.Module):
    def __init__(self, num_classes=2):
        super(CustomEfficientNet, self).__init__()
        self.base_model = timm.create_model('tf_efficientnet_b0_ns', pretrained=False)

        for param in self.base_model.parameters():
            param.requires_grad = False

        num_ftrs = self.base_model.classifier.in_features
        self.base_model.classifier = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.base_model(x)