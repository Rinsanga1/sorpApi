import timm
import torch
import torchvision
from torch import nn
from torchvision import transforms
from PIL import Image
from pathlib import Path
import io
from PIL import Image

class_names = ['Pattern', 'Solid']
device = 'cuda' if torch.cuda.is_available() else 'cpu'


def init_model():
    model = torch.jit.load(Path('model224jit.pt'))
    model.to(device)
    model.eval()
    return model

def process_image(image):

    transformation = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.CenterCrop(384),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])


    image_tensor = transformation(image).unsqueeze(0)
    image_tensor = image_tensor.to(device)
    return image_tensor

def predictit(image, model):
    image_tensor = process_image(image)
    output = model(image_tensor)

    probabilities = torch.nn.functional.softmax(output, dim=1)
    probabilities = probabilities.detach().cpu().numpy()[0]

    class_index = probabilities.argmax()
    predicted_class = class_names[class_index]
    probability = probabilities[class_index]

    class_probs = list(zip(class_names, probabilities))
    class_probs.sort(key=lambda x: x[1], reverse=True)

    return str(probability), str(predicted_class)
