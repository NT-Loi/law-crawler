# Law Data Crawler

This project contains tools to crawl, parse, and structure Vietnamese legal data from the "Bộ Pháp điển" and "Văn bản pháp luật" (VBPL) sources.

## Project Structure

*   **`phapdien_crawler.py`**: The main script to parse local "Bộ Pháp điển" data.
    *   Reads `jsonData.js` for structure (`jdChuDe`, `jdDeMuc`, `jdAllTree`).
    *   Parses HTML files in `phap_dien/demuc/` to extract Chapters (`Chương`) and Articles (`Điều`).
    *   Extracts legal references (`VBQPPL`) and related items (`LienQuan`).
    *   Outputs: `phap_dien/Chuong.json`, `phap_dien/Dieu.json`, `phap_dien/LienQuan.json`.
    *   **Features**: Progress bars (tqdm), checkpointing (every 10 files), and resume capability.
*   **`document_crawler.py`**: A crawler for external legal documents referenced in the Phap Dien data.
    *   Reads links from `phap_dien/Dieu.json` and `phap_dien/LienQuan.json`.
    *   Crawls full text from `vbpl.vn`.
    *   Parses structure based on the Table of Contents ("Mục lục văn bản").
    *   Outputs: Individual JSON files in `crawled_docs/{ItemID}.json`.
*   **`utils.py`**: Utility functions for Roman numeral conversion, HTML table parsing, and data extraction.
*   **`main.py`**: (Deprecated) Predecessor to `phapdien_crawler.py`.

## Setup

1.  **Environment**: Ensure you have Python installed.
2.  **Dependencies**: Install required packages:
    ```bash
    pip install beautifulsoup4 requests tqdm
    ```
    *(Note: Using a virtual environment is recommended)*

## Usage

### 1. Crawl Phap Dien Data

This step processes the local HTML and JS files to build the core dataset.

```bash
python phapdien_crawler.py
```

*   **Logs**: Check `phapdien_crawler.log` for detailed status and errors.
*   **Checkpoints**: The script saves progress every 10 processed files. If interrupted, run it again to resume from the last checkpoint.

### 2. Crawl External Documents

After generating the Phap Dien data, use this script to fetch the full text of related legal documents.

```bash
python document_crawler.py
```

*   **Logs**: Check `document_crawler.log` for crawling status.
*   **Output**: JSON files will be saved in `crawled_docs/`.

## Output Data Structure

*   **`Dieu.json`**: Contains details of every Article (Điều).
    *   `MAPC`: Unique Identifier.
    *   `TEN`: Article Title.
    *   `NoiDung`: Full text content.
    *   `VBQPPL`: References to source legal documents.
    *   `ChuongMAPC`: ID of the containing Chapter.
*   **`LienQuan.json`**: Relationships between Articles and other documents/articles.
    *   `source_MAPC`: The Article ID.
    *   `target_MAPC`: The related Article ID.
    *   `link`: External URL (if applicable).
*   **`crawled_docs/`**: JSON files for full legal documents.
    *   `sections`: List of sections corresponding to the TOC, with full text content.
