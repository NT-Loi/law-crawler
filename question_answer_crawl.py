import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re # Thư viện xử lý chuỗi nâng cao

# --- CẤU HÌNH ---
INPUT_FILE = 'all_question_links.csv'  # File link từ bước 2
OUTPUT_JSON = 'du_lieu_luat_dataset.json' # File kết quả
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def extract_legal_reference(text):
    """
    Hàm trích xuất Reference V6.1 (Fix lỗi SyntaxWarning):
    - Sử dụng rf-string (raw f-string) để xử lý đúng các ký tự regex \s, \b.
    """
    import re # Đảm bảo đã import re

    # 1. Làm sạch: Biến xuống dòng thành khoảng trắng, xóa ký tự lạ
    clean_text = re.sub(r'\s+', ' ', text).strip()
    references = []

    # Danh sách tên loại văn bản
    doc_types = r"(?:Luật|Bộ luật|Nghị định|Thông tư|Quyết định|Nghị quyết|Hiến pháp|Pháp lệnh)"

    # Regex cho số hiệu: Số (1, 20), La Mã (I, IV), hoặc chữ cái đơn (a, b, đ)
    valid_number = r"(?:số\s+)?[0-9]+|[IVX]+|[a-đA-Đ]\b"
    
    # Regex cho tên đơn vị
    unit_name = r"(?:Điều|Khoản|Điểm|Mục|Phần|Chương|Phụ lục|Tiểu mục)"
    
    # --- SỬA LỖI TẠI ĐÂY ---
    # Thay f"..." thành rf"..." để Python hiểu \s là regex, không phải lỗi cú pháp
    valid_unit_block = rf"{unit_name}\s+(?:{valid_number})"

    # --- MẪU REGEX CHÍNH ---
    pattern = (
        r'\b('                                     # Bắt đầu Group 1
        r'(?:' + valid_unit_block + r'[\s,]+)+?'   # Lặp lại các cụm Unit Block
        r')'                                       # Kết thúc Group 1
        r'(?:và\s+)?'                              # Chữ 'và'
        r'(?:của|tại|thuộc|trong|theo|về)?\s*'     # Từ nối
        r'(' + doc_types + r')'                    # Group 2: Loại văn bản
        r'(?:\s+số)?\s+'                           # Chữ "số"
        r'([0-9]+/[\w\-/]+|[^0-9\.\,]*?\d{4})'     # Group 3: Số hiệu hoặc Năm
    )

    matches = re.finditer(pattern, clean_text, re.IGNORECASE)
    
    for match in matches:
        raw_ref = match.group(1).strip()
        doc_type = match.group(2).strip()
        doc_id = match.group(3).strip()

        # Làm sạch raw_ref
        clean_prefix = re.sub(r'[,]+$', '', raw_ref).strip()
        clean_prefix = re.sub(r'\s+(của|tại|trong|thuộc|theo)$', '', clean_prefix).strip()
        
        full_ref = f"{clean_prefix} {doc_type} {doc_id}"
        references.append(full_ref)

    # --- MẪU DỰ PHÒNG ---
    if not references:
        simple = r'(Điều\s+\d+)\s+(?:của|tại)?\s*(Luật|Bộ luật)\s+([A-ZÀ-Ỹ][\w\s]+?)(?=\s+(?:bởi|tại|theo|quy định|thì|năm|\.|\,|$))'
        matches_simple = re.findall(simple, clean_text)
        for m in matches_simple:
            references.append(f"{m[0]} {m[1]} {m[2]}".strip())

    return list(set(references))
def get_detail_content_json(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. LẤY TIÊU ĐỀ
        title_tag = soup.find('h1', class_='the-article-title')
        question = title_tag.get_text(strip=True) if title_tag else ""
        
        # 2. LẤY NỘI DUNG TRẢ LỜI
        body_div = soup.find('div', class_='the-article-body')
        
        answer = ""
        extracted_refs = []
        
        if body_div:
            # Xử lý xóa 2 thẻ p cuối (như yêu cầu cũ)
            p_tags = body_div.find_all('p')
            if len(p_tags) >= 2:
                p_tags[-1].decompose()
                p_tags[-2].decompose()
            elif len(p_tags) == 1:
                p_tags[-1].decompose()

            # Lấy text sạch
            answer = body_div.get_text(separator='\n', strip=True)
            
            # --- BƯỚC MỚI: TRÍCH XUẤT REFERENCE TỪ ANSWER ---
            # Chúng ta quét text của câu trả lời để tìm luật
            extracted_refs = extract_legal_reference(answer)
            
        return {
            "question": question,
            "answer": answer,
            "reference": extracted_refs, # Trả về danh sách các điều luật tìm thấy
            "url": url
        }

    except Exception as e:
        print(f"Lỗi URL {url}: {e}")
        return None

def main():
    # 1. Đọc danh sách link
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"Đã đọc {len(df)} link.")
    except:
        print("Chưa có file csv link!")
        return

    all_data = []
    
    # 2. Duyệt link
    total = len(df)
    for index, row in df.iterrows():
        url = row['url']
        print(f"[{index+1}/{total}] Xử lý: {url}")
        
        data_item = get_detail_content_json(url)
        
        if data_item and data_item['answer']:
            # Nếu tiêu đề trong bài trống, lấy từ CSV
            if not data_item['question']:
                data_item['question'] = row['title']
                
            all_data.append(data_item)
        
        # Lưu file JSON định kỳ (mỗi 20 bài) để an toàn
        if len(all_data) % 20 == 0:
            with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"--> Đã lưu tạm {len(all_data)} mục vào JSON.")
            
        time.sleep(random.uniform(1, 2))

    # 3. Lưu file cuối cùng
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print(f"\nHOÀN THÀNH! File kết quả: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()