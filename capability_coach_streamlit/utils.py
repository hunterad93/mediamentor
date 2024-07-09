import streamlit as st
import requests
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def send_perplexity_message(message, conversation_history):
    url = "https://api.perplexity.ai/chat/completions"
    
    conversation_history.append({"role": "user", "content": message})
    
    payload = {
        "model": "llama-3-sonar-large-32k-online",
        "messages": [
            {"role": "system", "content": "Try to be specific in your responses. Conclude your response with a list of URLS used from your search."}
        ] + conversation_history
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {st.secrets['PPLX_API_KEY']}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        ai_response = response_data['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    else:
        return "Error: Unable to get a response from the API"

def ensure_single_thread_id():
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    return st.session_state.thread_id

def get_filename(file_id):
    print('getting filename')
    try:
        file_metadata = client.files.retrieve(file_id)
        filename = file_metadata.filename
        return filename
    except Exception as e:
        print(f"Error retrieving file: {e}")
        return None
    
def format_citation(annotation):
    print('formatting citation')
    file_id = annotation.file_citation.file_id
    filename = get_filename(file_id)
    if filename:
        # Normalize the filename to a URL-like string
        file_url = filename.replace('---', '/').replace('.pdf', '').replace('.md', '').replace('.json', '').replace('.txt', '')
        file_url = file_url.replace('/v3/content/docs', '')

        # Check if the URL is already a valid HTTP URL
        if file_url.startswith('http://') or file_url.startswith('https://'):
            citation_info = f" ({file_url}) "
        else:
            # Check if the URL looks like a domain name
            if '.' in file_url:
                file_url = 'https://' + file_url
            else:
                # Assume it's a relative path needing a base URL
                file_url = 'https://app.getguru.com/card/' + file_url
            citation_info = f" ({file_url}) "
    else:
        citation_info = "[Citation from an unknown file]"
    return citation_info

def stream_generator(prompt, thread_id, assistant_id):
    if assistant_id == "perplexity":
        if "perplexity_history" not in st.session_state:
            st.session_state.perplexity_history = []
        response = send_perplexity_message(prompt, st.session_state.perplexity_history)
        # Split the response into lines to preserve markdown formatting
        lines = response.split('\n')
        for line in lines:
            yield line + '\n'
    else:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
        content=prompt
        )

        with st.spinner("Wait... Generating response..."):
            stream = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                stream=True,
                max_prompt_tokens=12000          
            )
            partial_response = ""
            for event in stream:
                if event.data.object == "thread.message.delta":
                    for content in event.data.delta.content:
                        if content.type == 'text':
                            text_value = content.text.value
                            annotations = content.text.annotations
                            if annotations:
                                for annotation in annotations:
                                    citation_info = format_citation(annotation)
                                    indexes = f"from index {annotation.start_index} to {annotation.end_index}]"
                                    text_value = f"{citation_info}"
                            partial_response += text_value
                            words = partial_response.split(' ')
                            for word in words[:-1]:
                                yield word + ' '
                            partial_response = words[-1]
                else:
                    pass
            if partial_response:
                yield partial_response