
import onnxruntime as ort
import numpy as np
from client.config import settings

def check_model():
    try:
        session = ort.InferenceSession(settings.onnx_model_path, providers=["CPUExecutionProvider"])
        inp = session.get_inputs()[0]
        out = session.get_outputs()[0]
        print(f"Input:  {inp.name} {inp.shape}")
        print(f"Output: {out.name} {out.shape}")
    except Exception as e:
        print(f"Error loading model: {e}")

if __name__ == "__main__":
