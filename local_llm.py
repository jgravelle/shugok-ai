import requests
import json
import re

class LocalLLMProvider:
    def __init__(self, api_url="http://127.0.0.1:1234", local_llm_type="local_llm"):
        self.api_url = api_url
        self.local_llm_type = local_llm_type
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

    def generateLocal(self, prompt, system_prompt=None, temperature=0.7, max_tokens=-1):
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
    def generateOllama(self, prompt, system_prompt=None, temperature=0.7, max_tokens=-1):
        """Generate text using the local LLM via Ollama."""
        data = {
            "model": "llama3.2",  # Adjust model name as needed
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            data["system"] = system_prompt
        
        # Add max_tokens if specified (Ollama uses 'num_predict')
        if max_tokens > 0:
            data["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["response"]
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
        
        response = ""
        if self.local_llm_type == "local_llm":
            response = self.generateLocal(prompt, system_prompt=system_prompt, temperature=0.3)
        else:
            response = self.generateOllama(prompt, system_prompt=system_prompt, temperature=0.3)

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
        
        cleaned = ""
        if self.local_llm_type == "local_llm":
            cleaned = self.generateLocal(cleanup_prompt, temperature=0.1)
        else:
            cleaned = self.generateOllama(cleanup_prompt, temperature=0.1)
        if 'TITLE:' not in cleaned or 'SUMMARY:' not in cleaned:
            return f"TITLE: {original_title}\nSUMMARY: {original_summary}"
        return cleaned

    def shorten_title(self, title):
        """Shorten a title that's too long."""
        shorten_prompt = f"Make this title shorter and simpler while keeping the main point:\n{title}"
        shortened = ""
        if  self.local_llm_type == "local_llm":
            shortened = self.generateLocal(shorten_prompt, temperature=0.1)
        else:
            shortened = self.generateOllama(shorten_prompt, temperature=0.1)
        return self.clean_output(shortened)