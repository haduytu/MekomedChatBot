import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
from google.oauth2 import service_account

api_key = st.secrets.get("OPENAI_API_KEY")

if api_key:
    st.success("✅ API Key đã được nhận diện thành công!")
else:
    st.error("❌ Lỗi: Không tìm thấy API Key trong secrets.")

def rfile(name_file):
    with open(name_file, "r", encoding="utf-8") as file:
        return file.read()

def get_google_docs_content(document_ids):
    SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
    
    # Sử dụng credentials từ file hoặc từ secrets
    if st.secrets.get("gcp_service_account") is None:
        SERVICE_ACCOUNT_FILE = "credentials.json"
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    else:
        service_account_info = json.loads(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

    service = build("docs", "v1", credentials=creds)
    all_text = []

    for document_id in document_ids:
        doc = service.documents().get(documentId=document_id).execute()
        
        text = []
        for content in doc["body"]["content"]:
            if "paragraph" in content:
                for element in content["paragraph"]["elements"]:
                    if "textRun" in element:
                        text.append(element["textRun"]["content"])
        all_text.append("\n".join(text))
    
    return "\n\n".join(all_text)


# Hiển thị logo ở trên cùng, căn giữa
try:
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logo.png", use_container_width=True)
except Exception:
    pass

# Tùy chỉnh nội dung tiêu đề
title_content = rfile("00.xinchao.txt")

st.markdown(
    f"""
    <h1 style="text-align: center; font-size: 24px;">{title_content}</h1>
    """,
    unsafe_allow_html=True,
)

# Lấy OpenAI API key từ st.secrets.
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Tạo OpenAI client.
client = OpenAI(api_key=openai_api_key)

# Lấy nội dung training từ nhiều Google Docs
document_ids = [
    "1YUxUaW1zvM1HW_vEo4F8zaf7j2qyi7FfprwDzYWTW5M", #HuanLuyenChatBot
    "1l-nxSrYTs3lUuRaIQgZs8Gp0Twx47sbAKwZSfDFi7mY", #GIỚI THIỆU Mekomed
    "11BycSSW0otYOJcqRmKZEnFTmJfT3q7oj", #bang gia
    "1p_6NrUADX8uMnrTce3RyCkrU5LPYS8ca" #Các gói khám sức khỏe
]  # Danh sách ID tài liệu Google Docs  # Thay thế bằng danh sách ID tài liệu Google Docs
training_content = get_google_docs_content(document_ids)

INITIAL_SYSTEM_MESSAGE = {
    "role": "system",
    "content": f"""
    {training_content}
    
    #📌 Trong cuộc trò chuyện này, khách hàng tên là từ thông tin khách hàng nhập vào. Hãy luôn xưng hô với họ theo quy tắc trên.
    #""",
}

INITIAL_ASSISTANT_MESSAGE = {
    "role": "assistant",
    "content": rfile("02.assistant.txt"),
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
    
    stream = client.chat.completions.create(
        model=rfile("module_chatgpt.txt").strip(),
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        stream=True,
    )
    
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
