import os
import json
from PIL import Image
from io import BytesIO
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model open-source GPT4All-J
model_name = "nomic-ai/gpt4all-j"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Riwayat percakapan
HISTORY_FILE = "chat_history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        chat_history = json.load(f)
else:
    chat_history = [{"role": "system", "content": "Kamu adalah AI single-user premium, gratis, ramah, bisa menganalisis teks, gambar, video, audio, membuat sticker/GIF custom, dan menyediakan menu interaktif kompleks. Gunakan balon chat Messenger style."}]

def save_chat_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)

# Fungsi chat teks
def chat_with_gpt(message):
    chat_history.append({"role": "user", "content": message})
    inputs = tokenizer(message, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=250)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    chat_history.append({"role": "assistant", "content": answer})
    save_chat_history()

    # Sticker/GIF otomatis berdasarkan konteks
    sticker = None
    lower = answer.lower()
    if any(x in lower for x in ["senang", "hebat", "mantap"]):
        sticker = "🎉"
    elif any(x in lower for x in ["sedih", "galau", "menangis"]):
        sticker = "😢"
    elif any(x in lower for x in ["lucu", "haha", "tertawa"]):
        sticker = "😂"
    elif any(x in lower for x in ["oke", "baik", "sip"]):
        sticker = "👍"
    return answer, sticker

# Fungsi upload media
def process_media(media):
    if media is None:
        return "Tidak ada media yang diunggah.", None
    
    if isinstance(media, Image.Image):
        info = f"Gambar: ukuran {media.size}, mode {media.mode}."
        sticker = "🖼️"
    elif hasattr(media, "name") and media.name.endswith((".mp4", ".mov")):
        info = f"Video: {media.name}"
        sticker = "🎬"
    elif hasattr(media, "name") and media.name.endswith((".mp3", ".wav")):
        info = f"Audio: {media.name}"
        sticker = "🎵"
    else:
        info = "Media tidak dikenali."
        sticker = None
    
    # Menyimpan ke riwayat
    chat_history.append({"role": "user", "content": f"[MEDIA DIUPLOAD] {info}"})
    chat_history.append({"role": "assistant", "content": info})
    save_chat_history()
    return f"{info} {sticker}" if sticker else info, sticker

# Fungsi menu interaktif (multi-level)
def menu_action(choice, chat_gradio):
    response = f"Kamu memilih opsi: {choice}"
    chat_gradio.append(("Menu", response))
    return chat_gradio

# Fungsi utama chat
def respond(message, chat_gradio):
    reply, sticker = chat_with_gpt(message)
    if sticker:
        chat_gradio.append((message, f"{reply} {sticker}"))
    else:
        chat_gradio.append((message, reply))
    return chat_gradio, ""

def clear_chat():
    global chat_history
    chat_history = [{"role": "system", "content": "Kamu adalah AI single-user premium, gratis, ramah, bisa menganalisis teks, gambar, video, audio, membuat sticker/GIF custom, dan menyediakan menu interaktif kompleks. Gunakan balon chat Messenger style."}]
    save_chat_history()
    return []

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 💬 Chatbot AI Final Premium Ultra-Realistis (Teks + Media + Emoji + Sticker/GIF + Menu Multi-Level)")

    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Kamu", placeholder="Ketik pesan di sini...")
    image_input = gr.Image(type="pil", label="Unggah Gambar")
    media_input = gr.File(label="Unggah Video/Audio")
    clear = gr.Button("Clear Chat")

    # Emoji tombol
    with gr.Row():
        emoji_buttons = [gr.Button(e) for e in ["😀","🎉","❤️","👍","😂","😎","😢","😡"]]
        for b in emoji_buttons:
            b.click(lambda e, c: respond(e, c), [b, chatbot], [chatbot, msg])

    # Quick reply / menu multi-level
    with gr.Row():
        quick_buttons = [gr.Button(opt) for opt in ["Ya","Tidak","Mungkin","Bisa Jadi","Oke"]]
        for b in quick_buttons:
            b.click(lambda o, c: menu_action(o, c), [b, chatbot], [chatbot])

    # Event submit textbox & media upload
    msg.submit(respond, [msg, chatbot], [chatbot, msg])
    image_input.change(process_media, [image_input], chatbot)
    media_input.change(process_media, [media_input], chatbot)
    clear.click(clear_chat, None, chatbot)

demo.launch()
