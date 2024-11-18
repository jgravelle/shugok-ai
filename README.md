# Shugok-AI: AI Research Papers Simplified

Shugok-AI is a Streamlit-based web application that makes AI research papers from arXiv more accessible by simplifying their academic language into clear, everyday terms. The application uses a local LLM to transform complex academic writing into concise, easy-to-understand summaries, and automatically publishes results to a static website.

![image](https://github.com/user-attachments/assets/f321a8e0-6c04-41f9-8271-94ca24a2bd0d)

## Features

- **Real-time arXiv Scraping**: Fetches the latest papers from arXiv's CS.AI category
- **Automatic Simplification**: Uses a local LLM to convert academic language into plain English
- **Smart Caching**: Stores processed articles to avoid redundant processing
- **Search Functionality**: Search through both new and previously processed articles
- **PDF Access**: Direct links to original PDF papers on arXiv
- **User-Friendly Interface**: Clean, responsive Streamlit interface with real-time updates
- **Automatic Publishing**: Generates and publishes a static HTML website via FTP
- **Responsive Design**: Mobile-friendly layout with dark mode support
- **Real-time Processing Updates**: Shows live progress as articles are processed

![image](https://github.com/user-attachments/assets/a65f8757-c9d2-44d4-b6b1-b836cf159572)

## Requirements

- Python 3.7+
- Local LLM server running on port 1234 (compatible with OpenAI API format)
- FTP server credentials for publishing
- Required Python packages listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jgravelle/shugok-ai.git
cd shugok-ai
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Ensure your local LLM server is running on http://127.0.0.1:1234

4. Configure FTP settings in app.py:
```python
FTP_HOST = "your.ftp.host"
FTP_USER = "your_username"
FTP_PASS = "your_password"
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Click "Process Articles" to start fetching and processing recent AI papers

4. The application will:
   - Fetch and process recent papers from arXiv
   - Generate a static HTML website
   - Automatically publish to your configured FTP server

## How It Works

1. **Data Collection**: The application scrapes recent papers from arXiv's CS.AI category
2. **Processing Pipeline**:
   - Extracts titles and abstracts from arXiv
   - Sends text to local LLM for simplification
   - Generates responsive HTML with dark mode support
   - Publishes results via FTP
3. **Caching System**: 
   - Maintains a record of processed articles
   - Avoids reprocessing previously simplified papers
   - Enables quick search through historical entries

## Project Structure

- `app.py`: Main Streamlit application, arXiv scraping, and FTP publishing logic
- `local_llm.py`: LLM integration for text simplification
- `template.html`: HTML template for generated static website
- `requirements.txt`: Python package dependencies

## Technical Details

- Uses BeautifulSoup4 for HTML parsing
- Implements rate limiting for arXiv's robot policy
- Handles connection errors and malformed responses
- Provides real-time processing status updates
- Supports concurrent user sessions
- Generates responsive HTML with dark mode detection
- Automated FTP publishing workflow

## Notes

- The application requires a running local LLM server that's compatible with the OpenAI API format
- Processing time depends on the LLM server's performance and arXiv's response time
- Respects arXiv's robot policy with appropriate delays between requests
- FTP credentials must be configured before publishing will work

## Error Handling

The application includes comprehensive error handling for:
- Failed arXiv connections
- LLM server issues
- Malformed responses
- Rate limiting
- Invalid article formats
- FTP connection and upload failures

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
