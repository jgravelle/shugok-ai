# Shugok-AI: AI Research Papers Simplified

Shugok-AI is a Streamlit-based web application that makes AI research papers from arXiv more accessible by simplifying their academic language into clear, everyday terms. The application uses a local LLM to transform complex academic writing into concise, easy-to-understand summaries.

## Features

- **Real-time arXiv Scraping**: Fetches the latest papers from arXiv's CS.AI category
- **Automatic Simplification**: Uses a local LLM to convert academic language into plain English
- **Smart Caching**: Stores processed articles to avoid redundant processing
- **Search Functionality**: Search through both new and previously processed articles
- **PDF Access**: Direct links to original PDF papers on arXiv
- **User-Friendly Interface**: Clean, responsive Streamlit interface with real-time updates

## Requirements

- Python 3.7+
- Local LLM server running on port 1234 (compatible with OpenAI API format)
- Required Python packages listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/shugok-ai.git
cd shugok-ai
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Ensure your local LLM server is running on http://127.0.0.1:1234

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. The application will automatically start fetching and processing recent AI papers

4. Use the search box to filter articles based on titles and summaries

## How It Works

1. **Data Collection**: The application scrapes recent papers from arXiv's CS.AI category
2. **Processing Pipeline**:
   - Extracts titles and abstracts from arXiv
   - Sends text to local LLM for simplification
   - Ensures summaries are exactly two sentences long
   - Stores processed articles in JSON format
3. **Caching System**: 
   - Maintains a record of processed articles
   - Avoids reprocessing previously simplified papers
   - Enables quick search through historical entries

## Project Structure

- `app.py`: Main Streamlit application and arXiv scraping logic
- `local_llm.py`: LLM integration for text simplification
- `processed_articles.json`: Cache of processed articles
- `requirements.txt`: Python package dependencies

## Technical Details

- Uses BeautifulSoup4 for HTML parsing
- Implements rate limiting for arXiv's robot policy
- Handles connection errors and malformed responses
- Provides real-time processing status updates
- Supports concurrent user sessions

## Notes

- The application requires a running local LLM server that's compatible with the OpenAI API format
- Processing time depends on the LLM server's performance and arXiv's response time
- Respects arXiv's robot policy with appropriate delays between requests
- Stores processed articles locally for faster subsequent access

## Error Handling

The application includes comprehensive error handling for:
- Failed arXiv connections
- LLM server issues
- Malformed responses
- Rate limiting
- Invalid article formats

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
