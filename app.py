import streamlit as st
import os
import requests
from markitdown import MarkItDown

# --- Configuration ---
st.set_page_config(
    page_title="Universal Document Reader",
    page_icon="📄",
    layout="wide"
)

# Initialize the MarkItDown Engine
# Note: MarkItDown handles most office/web formats natively
md_engine = MarkItDown()

# --- Helper Functions ---

def convert_file_stream(uploaded_file):
    """
    Converts an uploaded Streamlit file object into Markdown text.
    Uses a temporary file approach because MarkItDown (and many underlying libs)
    often requires a physical file path rather than a memory stream.
    """
    # Create a safe temp filename to avoid conflicts
    temp_filename = f"temp_{uploaded_file.name}"
    
    # Save the uploaded bytes to disk temporarily
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        # [1] The Engine: MarkItDown handles detection & conversion
        result = md_engine.convert(temp_filename)
        return result.text_content
        
    except Exception as e:
        # Pass the error up to be handled by the UI
        raise ValueError(f"Engine failed: {str(e)}")
        
    finally:
        # [3] Resilience: Always clean up temp files, even if conversion fails
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# --- Main Application ---

def main():
    st.title("📄 Universal Document Reader")
    st.markdown("""
    **Upload your documents** (`.docx`, `.xlsx`, `.pptx`, `.pdf`, `.html`) below. 
    The app will extract the text and tables into clean Markdown.
    """)

    # [2] Interface: Upload Area
    uploaded_files = st.file_uploader(
        "Drag and drop files here", 
        accept_multiple_files=True,
        type=['docx', 'xlsx', 'pptx', 'pdf', 'html', 'zip', 'csv', 'json', 'xml']
    )

    if uploaded_files:
        st.divider()
        st.subheader("📝 Processed Output")

        for uploaded_file in uploaded_files:
            # Create a distinct container for each file
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                
                # Visual feedback while processing
                with st.spinner(f"Reading {uploaded_file.name}..."):
                    try:
                        # Perform Conversion
                        converted_text = convert_file_stream(uploaded_file)
                        
                        # [2] Interface: Instant Preview
                        st.text_area(
                            "Preview content:",
                            value=converted_text,
                            height=300,
                            key=f"preview_{uploaded_file.id}"
                        )
                        
                        # [4] Technical Constraints: Naming logic
                        base_name = os.path.splitext(uploaded_file.name)[0]
                        md_filename = f"{base_name}_converted.md"
                        txt_filename = f"{base_name}_converted.txt"

                        # [2] Interface: Download Options
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.download_button(
                                label="⬇️ Download as Markdown (.md)",
                                data=converted_text,
                                file_name=md_filename,
                                mime="text/markdown",
                                key=f"dl_md_{uploaded_file.id}"
                            )
                        
                        with col2:
                            st.download_button(
                                label="⬇️ Download as Text (.txt)",
                                data=converted_text,
                                file_name=txt_filename,
                                mime="text/plain",
                                key=f"dl_txt_{uploaded_file.id}"
                            )

                    except Exception as e:
                        # [3] Resilience: Polite error message
                        st.error(f"⚠️ Could not read {uploaded_file.name}. Please check the format.")
                        # Log the specific error to console for the developer
                        print(f"Error processing {uploaded_file.name}: {e}")

if __name__ == "__main__":
    main()
