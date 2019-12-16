from keras.models import model_from_json

def build_model():
    with open("model.json", 'r') as file: 
        loaded_model = model_from_json(file.read())
    return loaded_model
