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

# Initialize Local LLM Provider
llm = LocalLLMProvider()

# File to store processed articles
PROCESSED_FILE = 'processed_articles.json'

def load_processed_articles():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    return {'articles': {}, 'last_update': None}

def save_processed_articles(processed_data):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed_data, f)

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

def process_and_display_articles(search_term=''):
    arxiv_url = 'https://arxiv.org/list/cs.AI/recent?skip=0&show=2000'
    
    # Create placeholders for dynamic content
    status_placeholder = st.empty()
    new_articles_header = st.empty()
    new_articles_container = st.empty()
    existing_articles_header = st.empty()
    existing_articles_container = st.empty()
    
    status_placeholder.text("Fetching arXiv data...")
    
    try:
        html_content = scrape_url(arxiv_url)
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch arXiv data: {e}")
        return
    
    # Load previously processed articles
    processed_data = load_processed_articles()
    processed_articles = processed_data['articles']
    
    soup = BeautifulSoup(html_content, 'html.parser')
    entries = soup.find_all('dt')
    total_entries = len(entries)
    
    new_articles_count = 0
    existing_articles_count = 0
    
    new_articles_header.subheader("")
    existing_articles_header.subheader("")
    
    new_articles_content = ""
    existing_articles_content = ""
    
    for i, dt in enumerate(entries):
        status_placeholder.text(f"Processing article {i+1} of {total_entries}...")
        
        dd = dt.find_next_sibling('dd')
        if not dd:
            continue

        link_tag = dt.find('a', title='Abstract')
        if not link_tag:
            continue
            
        link = f"https://arxiv.org{link_tag['href']}"
        arxiv_id = extract_arxiv_id(link)
        pdf_link = link.replace('/abs/', '/pdf/') + '.pdf'

        # Check if article matches search term before processing
        if arxiv_id in processed_articles:
            entry = processed_articles[arxiv_id]
            if search_term.lower() in entry['simplified_title'].lower() or \
               search_term.lower() in entry['simplified_summary'].lower():
                article_html = f"""
                #### {entry['simplified_title']}
                [Download PDF]({entry['pdf_link']})
                
                {entry['simplified_summary']}
                ___
                """
                existing_articles_content += article_html
                existing_articles_count += 1
                existing_articles_container.markdown(existing_articles_content)
            continue

        title_tag = dd.find('div', class_='list-title mathjax')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True).replace('Title:', '').strip()

        try:
            abstract_html = scrape_url(link)
            abstract_soup = BeautifulSoup(abstract_html, 'html.parser')
            abstract_tag = abstract_soup.find('blockquote', class_='abstract mathjax')
            if not abstract_tag:
                continue
            summary = abstract_tag.get_text(strip=True).replace('Abstract:', '', 1).strip()

            # Simplify the text using local LLM
            simplified_title, simplified_summary = llm.simplify_text(title, summary)
            
            entry = {
                'arxiv_id': arxiv_id,
                'original_title': title,
                'simplified_title': simplified_title,
                'pdf_link': pdf_link,
                'simplified_summary': simplified_summary,
                'timestamp': datetime.now().isoformat()
            }
            
            processed_articles[arxiv_id] = entry
            
            if search_term.lower() in simplified_title.lower() or \
               search_term.lower() in simplified_summary.lower():
                article_html = f"""
                #### {simplified_title}
                [Download PDF]({pdf_link})
                
                {simplified_summary}
                ___
                """
                new_articles_content += article_html
                new_articles_count += 1
                new_articles_container.markdown(new_articles_content)

        except Exception as e:
            st.warning(f'Failed to retrieve summary for {link}: {e}')
            continue

        # Save after each successful processing
        processed_data['articles'] = processed_articles
        processed_data['last_update'] = datetime.now().isoformat()
        save_processed_articles(processed_data)
        
        # Delay for arXiv's robot policy
        time.sleep(3)

    status_placeholder.empty()
    
    if new_articles_count == 0 and existing_articles_count == 0:
        st.write("No articles found matching your search criteria.")
    
    st.sidebar.markdown(f"""
    ### Current Session Stats
    - New articles: {new_articles_count}
    - Previous articles: {existing_articles_count}
    - Total shown: {new_articles_count + existing_articles_count}
    """)

# Build the Streamlit app
st.write('Sh*t U Gotta Know!  Its...')
st.title('Shugok-AI: AI Research Papers Simplified')
st.write('Latest AI scholarly articles from arXiv, explained in plain language')

# Search functionality
search_term = st.text_input('Search for articles:', '')

# Process and display articles
try:
    process_and_display_articles(search_term)
except Exception as e:
    st.error(f"Failed to retrieve data: {e}")

# Sidebar information
st.sidebar.markdown("""
### About This Feed
- New articles appear at the top
- Summaries are limited to two sentences
- Articles are processed only once
- Updates happen in real-time
""")