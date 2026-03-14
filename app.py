import streamlit as st

from performance_dashboard import render_performance_dashboard


st.set_page_config(page_title="EduBridge AI", layout="wide")


@st.cache_resource
def get_edu_agent():
    from core.agent import EduAgent

    return EduAgent()


@st.cache_resource
def get_doc_processor():
    from processors.doc_processor import DocProcessor

    return DocProcessor()


@st.cache_resource
def get_image_processor():
    from processors.image_processor import ImageProcessor

    return ImageProcessor()


@st.cache_resource
def get_voice_processor():
    from processors.voice_processor import VoiceProcessor

    return VoiceProcessor()


@st.cache_resource
def get_file_handler():
    from utils.file_handler import FileHandler

    return FileHandler()


def render_ai_assistant_page():
    st.title("EduBridge AI")
    st.write("AI assistant for early childhood education")

    try:
        agent = get_edu_agent()
        doc_processor = get_doc_processor()
        image_processor = get_image_processor()
        voice_processor = get_voice_processor()
        file_handler = get_file_handler()
    except Exception as exc:
        st.error(f"AI Assistant initialization failed: {exc}")
        st.info(
            "If this is a Pinecone setup issue, remove `pinecone-client`, install `pinecone`, "
            "and make sure `PINECONE_API_KEY` and `PINECONE_INDEX` are set in `.env`."
        )
        return

    role = st.selectbox(
        "Select your role",
        ["parent", "teacher", "admin"],
    )

    uploaded_file = st.file_uploader(
        "Upload a document / image / audio",
        type=["pdf", "png", "jpg", "jpeg", "wav", "mp3"],
    )

    if uploaded_file:
        safe_name = uploaded_file.name.replace(" ", "_")
        file_path = file_handler.save_file(uploaded_file, f"uploads/{safe_name}")
        file_handler.save_file(uploaded_file, file_path)

        if uploaded_file.type == "application/pdf":
            text = doc_processor.read_pdf(file_path)
            agent.add_knowledge(text, uploaded_file.name)
            st.success("Document added to knowledge base")

        elif "image" in uploaded_file.type:
            text = image_processor.extract_text(file_path)
            agent.add_knowledge(text, uploaded_file.name)
            st.success("Image text extracted and added")

        elif "audio" in uploaded_file.type or uploaded_file.name.lower().endswith((".mp3", ".wav", ".m4a")):
            st.write("Saved audio path:", file_path)
            text = voice_processor.transcribe(file_path)
            st.session_state["voice_query"] = text
            agent.add_knowledge(text, uploaded_file.name)

            st.success(f"Audio transcribed and added: {uploaded_file.name}")
            st.write("Transcribed voice:")
            st.write(text)

    question = st.text_input(
        "Ask a question",
        value=st.session_state.get("voice_query", ""),
    )

    if st.button("Ask AI"):
        response = agent.ask(question, role)
        st.write("### AI Response")
        st.write(response)
        st.session_state["voice_query"] = ""

    if st.button("Clear Knowledge Base"):
        agent.clear_knowledge()
        st.success("Knowledge base cleared successfully")


def main():
    with st.sidebar:
        st.title("EduBridge AI")
        page = st.radio(
            "Choose a section",
            ["AI Assistant", "Student Performance Dashboard"],
        )

    if page == "AI Assistant":
        render_ai_assistant_page()
    else:
        render_performance_dashboard()


if __name__ == "__main__":
    main()
