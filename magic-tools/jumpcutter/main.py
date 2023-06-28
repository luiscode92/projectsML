import streamlit as st
import base64
import moviepy.editor as mpy
from jump_cutter import jump_cutter

st.title("Cortar silencios - Demo")
uploaded_file = st.file_uploader("Cargar video en")
silent_threshold = st.slider("Sensibilidad del corte en el video", min_value=0.0, max_value=1.0, value=0.05, step=0.01)

if uploaded_file is not None:
    # Get the file extension
    file_extension = uploaded_file.name.split(".")[-1]

if st.button('Cortar video'):
    # save the uploaded file to the local filesystem with the correct extension
    input_file = f"input.{file_extension}"
    with open(input_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # call the function with the correct extension for the output
    jump_cutter(
        input_file=input_file,
        output_file=f"output.{file_extension}",
        silent_threshold=silent_threshold,
    )

# Add a lot of space before the footer
for _ in range(25):
    st.write("\n")

# Then, add your footer
st.markdown(
    """
    <hr/>
    <p style='text-align: center; color: grey;'>This demo was made for Ana Coral & Jonathan Rengifo, created by <a href='https://luiscode92.github.io/#/' target='_blank'><b>Luis Sanjuan</b></a>.</p>
    <p style='text-align: center; color: grey;'>Feel free to reach out to me for any queries or feedback.</p>
    <p style='text-align: center; color: grey;'><small>MIT License</small></p>
    """,
    unsafe_allow_html=True,
)
