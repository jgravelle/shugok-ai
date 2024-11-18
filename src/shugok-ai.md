# app.py

```python
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import os
import json
import requests
from datetime import datetime
from local_llm import LocalLLMProvider
from ftplib import FTP

# Initialize Local LLM Provider
llm = LocalLLMProvider()

# FTP Configuration
FTP_HOST = "ftp.gravelle.us"
FTP_USER = "xxxxxxxxx"
FTP_PASS = "yyyyyyyyy"

def upload_to_ftp(local_file):
    """Upload the generated HTML file to FTP server."""
    try:
        with FTP(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)
            
            # Upload the file in binary mode
            with open(local_file, 'rb') as file:
                ftp.storbinary(f'STOR {os.path.basename(local_file)}', file)
            
            return True
    except Exception as e:
        st.error(f"FTP upload failed: {str(e)}")
        return False

def scrape_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def extract_arxiv_id(url):
    match = re.search(r'/([^/]+)(?:\.pdf)?$', url)
    return match.group(1) if match else None

def generate_html_output(articles):
    # Read our template files
    with open('template.html', 'r') as f:
        html_template = f.read()
    
    # Generate articles HTML
    articles_html = []
    for article in articles:
        article_html = f"""
            <div class="article">
                <div class="original-title"><a href="{article['pdf_link']}" class="pdf-link" target="_blank">arXiv PDF</a>("{article['original_title']}")</div>
                <h2 class="simplified-title">{article['simplified_title']}</h2>
                <p class="summary">{article['simplified_summary']}</p>
            </div>
        """
        articles_html.append(article_html)
    
    # Insert articles into template
    html_content = html_template.replace('{{ARTICLES}}', '\n'.join(articles_html))
    
    # Write to file
    output_file = 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

def process_articles():
    arxiv_url = 'https://arxiv.org/list/cs.AI/new'
    st.write("Fetching arXiv data...")
    
    try:
        html_content = scrape_url(arxiv_url)
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch arXiv data: {e}")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    entries = soup.find_all('dt')
    total_entries = len(entries)
    
    processed_articles = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, dt in enumerate(entries):
        progress = (i + 1) / total_entries
        progress_bar.progress(progress)
        status_text.text(f"Processing article {i+1} of {total_entries}...")
        
        dd = dt.find_next_sibling('dd')
        if not dd:
            continue

        link_tag = dt.find('a', title='Abstract')
        if not link_tag:
            continue
            
        link = f"https://arxiv.org{link_tag['href']}"
        pdf_link = link.replace('/abs/', '/pdf/') + '.pdf'

        title_tag = dd.find('div', class_='list-title mathjax')
        if not title_tag:
            continue
        original_title = title_tag.get_text(strip=True).replace('Title:', '').strip()

        try:
            abstract_html = scrape_url(link)
            abstract_soup = BeautifulSoup(abstract_html, 'html.parser')
            abstract_tag = abstract_soup.find('blockquote', class_='abstract mathjax')
            if not abstract_tag:
                continue
            summary = abstract_tag.get_text(strip=True).replace('Abstract:', '', 1).strip()

            # Simplify the text using local LLM
            simplified_title, simplified_summary = llm.simplify_text(original_title, summary)
            
            processed_articles.append({
                'original_title': original_title,
                'simplified_title': simplified_title,
                'pdf_link': pdf_link,
                'simplified_summary': simplified_summary,
                'timestamp': datetime.now().isoformat()
            })

            # Show the current article being processed with proper styling
            st.markdown(f"""
                <div class="article-card">
                    <div class="article-header">
                        <a href="{pdf_link}" target="_blank" class="pdf-link">arXiv PDF</a>
                        <span class="original-title">"{original_title}"</span>
                    </div>
                    <h3 class="simplified-title">{simplified_title}</h3>
                    <div class="summary-content">{simplified_summary}</div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.warning(f'Failed to retrieve summary for {link}: {e}')
            continue

        # Delay for arXiv's robot policy
        time.sleep(3)
    
    status_text.text("Generating HTML output...")
    output_file = generate_html_output(processed_articles)
    
    # Upload to FTP
    status_text.text("Uploading to FTP server...")
    if upload_to_ftp(output_file):
        st.success(f"Successfully generated and uploaded {output_file} to FTP server!")
    else:
        st.warning(f"Generated {output_file} but FTP upload failed. File is available locally.")
    
    # Show a sample of the generated HTML
    with open(output_file, 'r', encoding='utf-8') as f:
        st.code(f.read()[:1000] + '...\n[truncated]', language='html')

# Create template.html if it doesn't exist
if not os.path.exists('template.html'):
    template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Papers Simplified</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: var(--background-color, #f5f5f5);
            color: var(--text-color, #2c3e50);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #1e1e1e;
                --text-color: #e0e0e0;
                --card-background: #2d2d2d;
                --card-border: #3d3d3d;
                --link-color: #64b5f6;
            }
        }
        @media (prefers-color-scheme: light) {
            :root {
                --background-color: #f5f5f5;
                --text-color: #2c3e50;
                --card-background: #ffffff;
                --card-border: #e0e0e0;
                --link-color: #3498db;
            }
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            background: var(--card-background);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--card-border);
        }
        .article {
            background: var(--card-background);
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid var(--card-border);
        }
        .original-title {
            font-size: 1.0em;
            font-style: italic;
            color: var(--text-color);
            opacity: 0.8;
            margin-bottom: 0px;
        }
        .simplified-title {
            font-size: 1.4em;
            font-weight: 600;
            color: var(--text-color);
            margin: 10px 0;
        }
        .pdf-link {
            display: inline-block;
            margin: 10px 0;
            color: var(--link-color);
            text-decoration: none;
        }
        .pdf-link:hover {
            text-decoration: underline;
        }
        .summary {
            color: var(--text-color);
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Sh*t U Gotta Know!</h1>
        <p>Latest AI Papers from arXiv, Explained Simply</p>
    </div>
    
    {{ARTICLES}}
</body>
</html>"""
    with open('template.html', 'w', encoding='utf-8') as f:
        f.write(template_content)

# Add custom CSS for Streamlit display
st.markdown("""
    <style>
    .article-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .article-header {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .pdf-link {
        color: #0366d6;
        text-decoration: none;
    }
    .original-title {
        color: #666;
        font-style: italic;
    }
    .simplified-title {
        font-size: 1.25rem;
        margin: 0.75rem 0;
        color: #1a1a1a;
    }
    .summary-content {
        line-height: 1.6;
        color: #24292e;
    }
    </style>
    """, unsafe_allow_html=True)

# Build the Streamlit app
st.title('ArXiv Paper Processor')
st.write('This tool will generate a static HTML page of simplified arXiv papers.')

if st.button('Process Articles'):
    process_articles()
```

# local_llm.py

```python
import requests
import json
import re

class LocalLLMProvider:
    def __init__(self, api_url="http://127.0.0.1:1234"):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json"
        }
        self.cleanup_patterns = [
            r"Note:.*$",
            r"I've.*$",
            r"Here's.*$",
            r"This summary.*$",
            r"In this simplified version.*$",
            r"<[^>]+>",  # Remove HTML tags
            r"\[.*?\]",  # Remove square brackets
            r"\{.*?\}",  # Remove curly braces
            r"I made the following changes.*$",
            r"I simplified.*$",
            r"To make this accessible.*$"
        ]

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=-1):
        """Generate text using the local LLM."""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": "llama-3.2-3b-instruct",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to local LLM: {str(e)}")
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid response from local LLM: {str(e)}")

    def clean_output(self, text):
        """Clean up LLM output by removing unwanted patterns."""
        cleaned = text
        for pattern in self.cleanup_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE|re.DOTALL)
        return cleaned.strip()

    def simplify_text(self, title, summary):
        """Use the local LLM to simplify academic text into concise, layman's terms."""
        system_prompt = """You are an expert at simplifying complex academic language into clear, everyday terms.
Your response must follow this exact format:
TITLE: [concise title in plain language]
SUMMARY: [clear explanation of the research]

Rules:
1. Remove ALL technical jargon and academic terminology
2. Use simple, everyday language a high school student would understand
3. Make titles clear, direct, and under 12 words
4. Never use phrases like "this paper" or "the authors"
5. Focus on what was done and what was found
6. Do not tell readers to imagine anything or what to think
7. Keep the original meaning intact while making it accessible
8. Make the text engaging and informative
9. Never add explanations about the changes made or your process
10. Never use HTML tags or special formatting
11. Use active voice and present tense
12. Write directly about the research, not about the paper"""
        
        prompt = f"""Rewrite this title and summary for a general audience without being condescending.
Assume the audience can understand complex ideas if explained clearly.

Original Title: {title}
Original Summary: {summary}

Your simplified version:"""
        
        response = self.generate(prompt, system_prompt=system_prompt, temperature=0.3)
        
        title_match = re.search(r'TITLE:\s*(.*?)(?=SUMMARY:|$)', response, re.DOTALL)
        summary_match = re.search(r'SUMMARY:\s*(.*?)$', response, re.DOTALL)
        
        if not title_match or not summary_match:
            response = self.cleanup_response(title, summary, response)
            title_match = re.search(r'TITLE:\s*(.*?)(?=SUMMARY:|$)', response, re.DOTALL)
            summary_match = re.search(r'SUMMARY:\s*(.*?)$', response, re.DOTALL)
        
        simplified_title = title_match.group(1).strip() if title_match else title
        simplified_summary = summary_match.group(1).strip() if summary_match else summary
        
        # Clean both outputs
        simplified_title = self.clean_output(simplified_title)
        simplified_summary = self.clean_output(simplified_summary)
        
        # Title length check
        if len(simplified_title.split()) > 12:
            simplified_title = self.shorten_title(simplified_title)
        
        return simplified_title, simplified_summary

    def cleanup_response(self, original_title, original_summary, response):
        """Force cleanup of malformed response."""
        cleanup_prompt = """Format this text exactly as shown:
TITLE: [single line title]
SUMMARY: [explanation in plain language]

Text to format:
{response}"""
        
        cleaned = self.generate(cleanup_prompt, temperature=0.1)
        if 'TITLE:' not in cleaned or 'SUMMARY:' not in cleaned:
            return f"TITLE: {original_title}\nSUMMARY: {original_summary}"
        return cleaned

    def shorten_title(self, title):
        """Shorten a title that's too long."""
        shorten_prompt = f"Make this title shorter and simpler while keeping the main point:\n{title}"
        shortened = self.generate(shorten_prompt, temperature=0.1)
        return self.clean_output(shortened)
```

