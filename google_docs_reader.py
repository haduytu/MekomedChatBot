from googleapiclient.discovery import build
from google.oauth2 import service_account

# Định nghĩa phạm vi API
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
SERVICE_ACCOUNT_FILE = "credentials.json"

# Tạo credentials từ file JSON
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# ID của tài liệu Google Docs (lấy từ URL)
DOCUMENT_ID = "YOUR_GOOGLE_DOC_ID"

# Kết nối với Google Docs API
service = build("docs", "v1", credentials=creds)
doc = service.documents().get(documentId=DOCUMENT_ID).execute()

# Trích xuất nội dung văn bản
def extract_text_from_google_doc(doc):
    text = []
    for content in doc["body"]["content"]:
        if "paragraph" in content:
            for element in content["paragraph"]["elements"]:
                if "textRun" in element:
                    text.append(element["textRun"]["content"])
    return "\n".join(text)

# Gọi hàm để lấy nội dung
google_docs_text = extract_text_from_google_doc(doc)
print(google_docs_text)  # Hiển thị nội dung tài liệu Google Docs
