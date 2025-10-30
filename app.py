import os
import json
import openai
import gradio as gr
from dotenv import load_dotenv

# Load environment variable lokal (jika ada)
load_dotenv()

# Ambil API key dari environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("API key OpenAI tidak ditemukan! Pastikan OPENAI_API_KEY sudah diset.")

# File penyimpanan riwayat
HISTORY_FILE = "chat_history.json"

# Load atau buat file history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        all_histories = json.load(f)
else:
    all_histories = {}

def get_user_history(user_id):
    """Ambil riwayat percakapan user, buat baru jika belum ada"""
    if user_id not in all_histories:
        all_histories[user_id] = [
            {"role": "system", "content": "Kamu adalah AI yang menjawab semua pertanyaan dengan jelas, tepat, dan ramah."}
        ]
    return all_histories[user_id]

def save_user_history():
    """Simpan semua riwayat ke file"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(all_histories, f, indent=4)

def chat_with_gpt(user_id, message):
    history = get_user_history(user_id)
    history.append({"role": "user", "content": message})
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=history
    )
    
    answer = response['choices'][0]['message']['content']
    history.append({"role": "assistant", "content": answer})
    
    save_user_history()
    
    return answer

# Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("## Chatbot AI Advanced & Aman (Multi-user + Simpan Riwayat)")
    
    user_id_input = gr.Textbox(label="User ID (misal: user1)")
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Kamu")
    clear = gr.Button("Clear Chat")
    
    def respond(user_id, message, chat_history_gradio):
        reply = chat_with_gpt(user_id, message)
        chat_history_gradio.append((message, reply))
        return chat_history_gradio, ""
    
    msg.submit(respond, [user_id_input, msg, chatbot], [chatbot, msg])
    
    def clear_chat(user_id):
        if user_id in all_histories:
            all_histories[user_id] = [
                {"role": "system", "content": "Kamu adalah AI yang menjawab semua pertanyaan dengan jelas, tepat, dan ramah."}
            ]
            save_user_history()
        return []
    
    clear.click(clear_chat, [user_id_input], chatbot)

demo.launch()
