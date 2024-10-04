import streamlit as st
import openai
import requests
import time
import base64

# Function to convert voice to text using OpenAI
def convert_voice_to_text(api_key, audio_data):
    openai.api_key = api_key
    # Sending the audio data to OpenAI for transcription
    audio_bytes = base64.b64decode(audio_data.split(',')[1])  # decode base64 audio
    response = openai.Audio.transcribe(model="whisper-1", file=audio_bytes)
    return response['text']

# Function to send text to server API
def send_text_to_server(api_url, text):
    response = requests.post(api_url, json={"converted_text": text})
    return response.status_code

# Streamlit App Layout
st.title("Voice to Text Converter")
st.write("Convert your voice to text using OpenAI Whisper")

# OpenAI API Key input
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

# Button to start recording voice
st.markdown("""
    <h3>Record your voice:</h3>
    <button id="recordButton" style="background-color: #4CAF50; color: white; padding: 10px 24px; border-radius: 5px;">Record</button>
    <button id="stopButton" style="background-color: #f44336; color: white; padding: 10px 24px; border-radius: 5px;" disabled>Stop</button>
    <p id="status">Status: Ready to record...</p>
    <audio id="audioPlayback" controls style="display:none;"></audio>
    <script>
        let recordButton = document.getElementById('recordButton');
        let stopButton = document.getElementById('stopButton');
        let status = document.getElementById('status');
        let audioPlayback = document.getElementById('audioPlayback');
        let mediaRecorder;
        let audioChunks = [];

        recordButton.onclick = async () => {
            let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            status.textContent = 'Status: Recording...';
            recordButton.disabled = true;
            stopButton.disabled = false;
            audioChunks = [];
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
        };

        stopButton.onclick = () => {
            mediaRecorder.stop();
            stopButton.disabled = true;
            recordButton.disabled = false;
            status.textContent = 'Status: Processing audio...';

            mediaRecorder.onstop = () => {
                let audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                let audioUrl = URL.createObjectURL(audioBlob);
                audioPlayback.src = audioUrl;
                audioPlayback.style.display = 'block';

                // Convert blob to base64
                let reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    let base64AudioMessage = reader.result;
                    fetch('/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ audio_data: base64AudioMessage })
                    }).then(response => response.json())
                      .then(data => {
                          status.textContent = 'Status: ' + data['message'];
                          if (data['text']) {
                              let textarea = document.createElement('textarea');
                              textarea.value = data['text'];
                              textarea.rows = 10;
                              textarea.cols = 40;
                              document.body.appendChild(textarea);
                          }
                      });
                };
            };
        };
    </script>
    """, unsafe_allow_html=True)

# Streamlit server logic to handle audio processing
st.write("Recording Section:")

# Handle audio data when received from the frontend
if 'audio_data' in st.session_state:
    audio_data = st.session_state['audio_data']

    if audio_data and api_key:
        st.write("Processing your audio...")
        try:
            # Convert audio to text
            converted_text = convert_voice_to_text(api_key, audio_data)
            st.write("Converted Text:")
            st.text_area("Transcribed Text", value=converted_text, height=200)

            # Share with API on server
            api_url = st.text_input("Enter the server API URL to send text:")
            if api_url:
                status = send_text_to_server(api_url, converted_text)
                if status == 200:
                    st.success("Text successfully sent to server!")
                else:
                    st.error(f"Failed to send text. Server responded with status code: {status}")
        except Exception as e:
            st.error(f"Error converting audio: {e}")
