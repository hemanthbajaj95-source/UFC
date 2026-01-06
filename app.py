import streamlit as st
import os
import pandas as pd
from markitdown import MarkItDown
from pdfminer.high_level import extract_text

# --- Configuration ---
st.set_page_config(
    page_title="Universal Document Reader",
    page_icon="📄",
    layout="wide"
)

# Initialize Engine
md_engine = MarkItDown()

# --- Helper Functions ---

def format_size(size_in_bytes):
    """Converts bytes to readable 'KB' or 'MB' strings."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def convert_file_stream(uploaded_file):
    """
    Robust converter with PDF fallback logic.
    """
    temp_filename = f"temp_{uploaded_file.name}"
    
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        # Attempt 1: MarkItDown
        try:
            result = md_engine.convert(temp_filename)
            if result.text_content.strip():
                return result.text_content
        except Exception:
            pass
        
        # Attempt 2: PDF Fallback
        if temp_filename.lower().endswith(".pdf"):
            try:
                raw_text = extract_text(temp_filename)
                if raw_text.strip():
                    return f"**Note: Extracted using PDF Fallback**\n\n{raw_text}"
            except Exception as pdf_err:
                raise ValueError(f"PDF Fallback failed: {pdf_err}")
        
        raise ValueError("Could not extract text content.")

    except Exception as e:
        raise ValueError(f"Conversion failed: {str(e)}")
        
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# --- Main Application ---

def main():
    st.title("📄 Universal Document Reader")
    st.markdown("""
    **Upload your documents** (`.docx`, `.xlsx`, `.pptx`, `.pdf`, `.html`) below. 
    The app will extract the text and tables into clean Markdown.
    """)

    uploaded_files = st.file_uploader(
        "Drag and drop files here", 
        accept_multiple_files=True,
        type=['docx', 'xlsx', 'pptx', 'pdf', 'html', 'zip', 'csv']
    )

    if uploaded_files:
        st.divider()
        st.subheader("📝 Processed Output")

        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                
                with st.spinner(f"Reading {uploaded_file.name}..."):
                    try:
                        # 1. Perform Conversion
                        converted_text = convert_file_stream(uploaded_file)
                        
                        # 2. Calculate Sizes
                        original_size = uploaded_file.size
                        # Estimate converted size (UTF-8 bytes)
                        converted_size = len(converted_text.encode('utf-8'))
                        
                        # Calculate reduction percentage
                        if original_size > 0:
                            reduction = ((original_size - converted_size) / original_size) * 100
                        else:
                            reduction = 0

                        # 3. Create Tabs (Preview vs Stats)
                        tab_preview, tab_stats = st.tabs(["👁️ Preview", "📊 File Size Comparison"])

                        # --- Tab 1: Text Preview ---
                        with tab_preview:
                            st.text_area(
                                "Content:",
                                value=converted_text,
                                height=300,
                                label_visibility="collapsed",
                                key=f"preview_{uploaded_file.id}"
                            )

                            # Download Buttons
                            base_name = os.path.splitext(uploaded_file.name)[0]
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    label="⬇️ Download Markdown (.md)",
                                    data=converted_text,
                                    file_name=f"{base_name}_converted.md",
                                    mime="text/markdown",
                                    key=f"dl_md_{uploaded_file.id}"
                                )
                            with col2:
                                st.download_button(
                                    label="⬇️ Download Text (.txt)",
                                    data=converted_text,
                                    file_name=f"{base_name}_converted.txt",
                                    mime="text/plain",
                                    key=f"dl_txt_{uploaded_file.id}"
                                )

                        # --- Tab 2: File Size Comparison ---
                        with tab_stats:
                            st.markdown("### Efficiency Metrics")
                            
                            # Create Data for Table
                            data = {
                                "Metric": ["Original File Size", "Converted .txt Size"],
                                "Value": [format_size(original_size), format_size(converted_size)]
                            }
                            df = pd.DataFrame(data)

                            # Show Table
                            st.table(df)

                            # Show Highlight Metric
                            if reduction > 0:
                                st.success(f"🚀 **Text version is {reduction:.1f}% smaller!**")
                            else:
                                st.info(f"ℹ️ Text version is about the same size ({abs(reduction):.1f}% change).")

                    except Exception as e:
                        st.error(f"⚠️ Could not read {uploaded_file.name}. Please check the format.")
                        print(f"Error processing {uploaded_file.name}: {e}")

if __name__ == "__main__":
    main()
