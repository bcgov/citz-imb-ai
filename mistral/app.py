import gradio as gr
import time
from ctransformers import AutoModelForCausalLM

path = "../media/mistral-7b-instruct-v0.2.Q8_0.gguf"

model = AutoModelForCausalLM.from_pretrained(
    model_path_or_repo_id=path,
    model_type="mistral",
    gpu_layers=0,
)


def llm_function(message, chat_history):
    response = model(message, echo=false, temperature=0.7, max_tokens=2000, device="cpu")
    return response


title = "BC law buddy 🗨️"
description = "A large language model that can help you find information about BC laws. Ask it a question and it will find the most relevant information for you. 📚🔍🗨️"

gr.ChatInterface(llm_function, title=title, description=description).launch(server_name="0.0.0.0", server_port=8080)