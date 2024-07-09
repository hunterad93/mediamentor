import streamlit as st
from utils import stream_generator, ensure_single_thread_id

assistants = {
    "guru-ttd-facebook-google-tapclicks(4o)": "asst_i2G0tKzk078avpQRVDHaBSCn",
    "scraped data partners": "asst_hmypwVa6RzvlH4ovziVE74RU",
    "guru-ttd-facebook-google-tapclicks(3.5)": "asst_bHqLo2kUeOx52Q7WEDeDZU4r",
    "ttd API bot": "asst_mW3LJwfjrAza1EVuiSuQKMk2",
    "perplexity": "perplexity",
    "perplexity docs kb": "asst_RMBAw1nL3elM34fJHnKYsLuP",
    "Capability Coach": "asst_Z2RpUC1WeJqIGnq3EvjZ8GgN"

}
# Streamlit interface
st.set_page_config(page_icon="📖")
st.title("Capability Coach Chatbot - discuss Pathlabs knowledge bases with ChatGPT")
st.subheader("The chatbot uses knowledge from Guru cards and documentation from The Trade Desk, Google Ads, Facebook Ads, and Tapclicks. Ask questions about the capabilities of Pathlabs (e.g. can Pathlabs do cross device targeting?)")

# Dropdown to select the assistant
selected_assistant_id = assistants["Capability Coach"]

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter your message")
if prompt:
    thread_id = ensure_single_thread_id()
    with st.chat_message("user"):
        st.write(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        for chunk in stream_generator(prompt, thread_id, selected_assistant_id):
            full_response += chunk + " "
            response_container.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response.strip()})

