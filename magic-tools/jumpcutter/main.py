import streamlit as st
import base64
import moviepy.editor as mpy
from jump_cutter import jump_cutter # let's assume that we've moved your code into a function inside this module

st.title("corto de silecios - Demo")
uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'avi'])

# Parameters for the jump_cutter function
#silent_threshold = st.slider("Silent threshold", min_value=0.0, max_value=1.0, value=0.03, step=0.01)
#sounded_speed = st.slider("Sounded speed", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
#silent_speed = st.slider("Silent speed", min_value=0.0, max_value=999999.0, value=5.0, step=1.0)
#frame_margin = st.slider("Frame margin", min_value=0, max_value=10, value=1)
#frame_rate = st.slider("Frame rate", min_value=0, max_value=60, value=30)

if st.button('Process'):
    # save the uploaded file to the local filesystem
    with open("input.mp4", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # call the function
    jump_cutter(
        input_file="input.mp4",
        output_file="output.mp4",
    )



    # prepare the file for download
