import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
import googleapiclient.errors

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

if "gcp_service_account" in st.secrets:
    service_account_info = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
        "universe_domain": st.secrets["gcp_service_account"]["universe_domain"]
    }
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
else:
    st.stop()

def get_google_docs_content(document_ids):
    service = build("docs", "v1", credentials=creds)
    all_text = []
    for document_id in document_ids:
        try:
            doc = service.documents().get(documentId=document_id).execute()
            text = []
            for content in doc.get("body", {}).get("content", []):
                if "table" in content:
                    for row in content["table"]["tableRows"]:
                        row_text = []
                        for cell in row["tableCells"]:
                            cell_text = " ".join(element["textRun"]["content"] for element in cell["content"][0]["paragraph"]["elements"] if "textRun" in element)
                            row_text.append(cell_text)
                        text.append("\t".join(row_text))
                elif "paragraph" in content:
                    for element in content["paragraph"].get("elements", []):
                        if "textRun" in element:
                            text.append(element["textRun"].get("content", ""))
            all_text.append("\n".join(text))
        except googleapiclient.errors.HttpError:
            pass
    return "\n\n".join(all_text)

# Hiển thị logo ở trên cùng, căn giữa
try:
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logo.png", use_container_width=True)
except Exception:
    pass

# Tùy chỉnh nội dung tiêu đề
title_content = "Ứng dụng ChatMekomed"
st.markdown(f"""
    <h1 style="text-align: center; font-size: 24px;">{title_content}</h1>
    """, unsafe_allow_html=True)

# Lấy OpenAI API key từ st.secrets.
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Tạo OpenAI client.
client = OpenAI(api_key=openai_api_key)

# Lấy nội dung training từ nhiều Google Docs
document_ids = [
    "1YUxUaW1zvM1HW_vEo4F8zaf7j2qyi7FfprwDzYWTW5M",
    "1l-nxSrYTs3lUuRaIQgZs8Gp0Twx47sbAKwZSfDFi7mY",
    "11BycSSW0otYOJcqRmKZEnFTmJfT3q7oj",
    "1p_6NrUADX8uMnrTce3RyCkrU5LPYS8ca"
]
training_content = get_google_docs_content(document_ids)

# Kiểm tra nội dung training
st.text_area("📄 Nội dung training từ Google Docs:", training_content, height=300)

INITIAL_SYSTEM_MESSAGE = {
    "role": "system",
    "content": f"""
    Bạn là một chatbot tư vấn y tế của Mekomed. Dưới đây là thông tin chi tiết từ tài liệu hướng dẫn:

    {training_content}

    📌 Nếu người dùng hỏi về dịch vụ, bảng giá hoặc các gói khám sức khỏe, hãy sử dụng thông tin từ trên để trả lời một cách chính xác nhất.
    """,
}

INITIAL_ASSISTANT_MESSAGE = {
    "role": "assistant",
    "content": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?",
}

if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    messages_with_training = [INITIAL_SYSTEM_MESSAGE] + st.session_state.messages
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": m["role"], "content": m["content"]} for m in messages_with_training],
        stream=True,
    )
    
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
