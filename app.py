import os
import json
import openai
import gradio as gr
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load .env lokal
load_dotenv()

# API Key OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("API key OpenAI tidak ditemukan! Pastikan OPENAI_API_KEY sudah diset.")

# Riwayat percakapan
HISTORY_FILE = "chat_history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        chat_history = json.load(f)
else:
    chat_history = [{"role": "system", "content": "Kamu adalah AI single-user yang menjawab semua pertanyaan dengan jelas, ramah, profesional, bisa menganalisis teks, gambar, emoji, dan menambahkan sticker atau GIF sesuai mood percakapan. Gunakan balon chat Messenger style."}]

def save_chat_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)

# Chat teks
def chat_with_gpt(message):
    chat_history.append({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=chat_history
    )
    answer = response['choices'][0]['message']['content']
    chat_history.append({"role": "assistant", "content": answer})
    save_chat_history()
    
    # Tambahkan sticker/GIF otomatis jika kata tertentu muncul
    sticker = None
    lower = answer.lower()
    if "senang" in lower or "hebat" in lower:
        sticker = "🎉"
    elif "sedih" in lower:
        sticker = "😢"
    elif "lucu" in lower:
        sticker = "😂"
    return answer, sticker

# Chat gambar
def process_image(image):
    if image is None:
        return "Tidak ada gambar yang diunggah.", None
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    chat_history.append({"role": "user", "content": "[GAMBAR DIUPLOAD] Analisis gambar dan gabungkan dengan konteks percakapan."})
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=chat_history
    )
    answer = response['choices'][0]['message']['content']
    chat_history.append({"role": "assistant", "content": answer})
    save_chat_history()

    # Sticker otomatis berdasarkan mood kata di caption
    sticker = None
    lower = answer.lower()
    if "senang" in lower or "hebat" in lower:
        sticker = "🎉"
    elif "sedih" in lower:
        sticker = "😢"
    elif "lucu" in lower:
        sticker = "😂"
    
    return answer, sticker

# Fungsi utama chat teks
def respond(message, chat_gradio):
    reply, sticker = chat_with_gpt(message)
    if sticker:
        chat_gradio.append((message, f"{reply} {sticker}"))
    else:
        chat_gradio.append((message, reply))
    return chat_gradio, ""

def clear_chat():
    global chat_history
    chat_history = [{"role": "system", "content": "Kamu adalah AI single-user yang menjawab semua pertanyaan dengan jelas, ramah, profesional, bisa menganalisis teks, gambar, emoji, dan menambahkan sticker atau GIF sesuai mood percakapan. Gunakan balon chat Messenger style."}]
    save_chat_history()
    return []

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 💬 Chatbot AI Messenger Ultimate (Teks + Gambar + Emoji + Sticker/GIF)")
    
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Kamu", placeholder="Ketik pesan di sini...")
    image_input = gr.Image(type="pil", label="Unggah Gambar")
    clear = gr.Button("Clear Chat")

    # Emoji tombol
    with gr.Row():
        emoji_buttons = [gr.Button(e) for e in ["😀", "🎉", "❤️", "👍", "😂", "😎"]]
        for b in emoji_buttons:
            b.click(lambda e, c: respond(e, c), [b, chatbot], [chatbot, msg])

    # Quick reply tombol
    with gr.Row():
        quick_buttons = [gr.Button(opt) for opt in ["Ya", "Tidak", "Mungkin", "Bisa Jadi"]]
        for b in quick_buttons:
            b.click(lambda o, c: respond(o, c), [b, chatbot], [chatbot, msg])

    # Event submit textbox & image upload
    msg.submit(respond, [msg, chatbot], [chatbot, msg])
    image_input.change(process_image, [image_input], chatbot)
    clear.click(clear_chat, None, chatbot)

demo.launch()
