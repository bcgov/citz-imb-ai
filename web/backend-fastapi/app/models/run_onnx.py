import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
import psutil
from optimum.onnxruntime import ORTModelForQuestionAnswering
import os

#check if onnx/model.onnx exists
if not os.path.exists("onnx/all-MiniLM-L6-v2_onnx/model.onnx"):
    print("Model not found")

# Load the tokenizer and models
model_name = "onnx/all-MiniLM-L6-v2_onnx/"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Configure session options to use multiple threads
sess_options = ort.SessionOptions()
sess_options.intra_op_num_threads = psutil.cpu_count(logical=True)  # Use all available logical CPUs

# Load the ONNX model with session options
ort_session = ort.InferenceSession("onnx/all-MiniLM-L6-v2_onnx/model.onnx", sess_options)
model = ORTModelForQuestionAnswering.from_pretrained(model_name)

#run inference
def embed_query(text):
    inputs = tokenizer(text, return_tensors="np")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    ort_inputs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask
    }
    ort_outs = ort_session.run(None, ort_inputs)
    return ort_outs[0][0][0]