import streamlit as st
from openai import OpenAI
import pymongo
import time
import io
import os
from datetime import datetime

# ---------------------------------------------------------
# CLOUD SERVICE #2: MONGODB ATLAS (Database)
# ---------------------------------------------------------
# We use st.secrets so you don't leak your database password on GitHub!
try:
    # It will look for MONGO_URI in your secrets file
    client_db = pymongo.MongoClient(st.secrets["MONGO_URI"])
    db = client_db["PhaenonDB"]
    chat_collection = db["chat_history"]
except Exception as e:
    st.warning(f"⚠️ Database error: {e}")
    chat_collection = None

# ---------------------------------------------------------
# CLOUD SERVICE #1: OPENROUTER (AI API)
# ---------------------------------------------------------
client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"], 
    base_url="https://openrouter.ai/api/v1"
)

st.set_page_config(
    page_title="Chat with Phaenon",
    page_icon=":brain:",
    layout="centered"
)

# 2. Improved Styling
# 2. Improved Styling
st.markdown(
    """
    <style>
    /* Targeting Streamlit chat message containers */
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    
    /* Hiding the Streamlit top menu, deploy button, and GitHub icons */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Phaenon, a helpful and intelligent AI assistant."}
    ]

def export_chat(format="txt"):
    buffer = io.StringIO()
    for msg in st.session_state.messages[1:]:
        role = msg["role"].capitalize()
        content = msg["content"]
        if format == "md":
            buffer.write(f"**{role}**:\n{content}\n\n---\n\n")
        else:
            buffer.write(f"{role}:\n{content}\n\n")
    return buffer.getvalue()

def main():
    # --- SIDEBAR UI ---
    st.sidebar.subheader("🤖 Phaenon - Chatbot")
    
    image_path = "phaenon.png"  
    
    if os.path.exists(image_path):
        st.sidebar.image(image_path, width=250, caption="Phaenon Bot")
    else:
        st.sidebar.warning(" image not found. Place it in the project folder!")

    if st.sidebar.button("🧹 Clear Chat History"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

    st.sidebar.info("Phaenon is an AI assistant built with Streamlit.")

    download_format = st.sidebar.selectbox("📄 Export Format", ["txt", "md"])
    st.sidebar.download_button(
        label="💾 Download Chat",
        data=export_chat(download_format),
        file_name=f"phaenon_chat.{download_format}",
        mime="text/plain" if download_format == "txt" else "text/markdown"
    )

    # --- MAIN CHAT INTERFACE ---
    for msg in st.session_state.messages[1:]:
        avatar = msg.get("avatar", "🤖" if msg["role"] == "assistant" else "👁️")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask Phaenon something...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "👁️"})
        with st.chat_message("user", avatar="👁️"):
            st.markdown(user_input)

        try:
            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                full_response = ""
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True
                )

                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)

            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response, 
                "avatar": "🤖"
            })
            
            # ---------------------------------------------------------
            # SAVE TO DATABASE
            # ---------------------------------------------------------
            if chat_collection is not None:
                chat_log = {
                    "timestamp": datetime.now(),
                    "user_query": user_input,
                    "ai_response": full_response
                }
                chat_collection.insert_one(chat_log)

        except Exception as e:
            st.error(f"API Error: {str(e)}")
            st.info("Try checking your OpenRouter credits or changing the model in the code.")

if __name__ == "__main__":
    main()