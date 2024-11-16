import requests
import json

class LocalLLMProvider:
    def __init__(self, api_url="http://127.0.0.1:1234"):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json"
        }

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

    def simplify_text(self, title, summary):
        """
        Use the local LLM to simplify academic text into concise, layman's terms.
        """
        system_prompt = """
        You are an expert at simplifying complex academic language into clear, everyday terms.
        Follow these rules strictly:
        1. Remove ALL technical jargon and academic terminology
        2. Use simple, everyday language a high school student would understand
        3. Make titles clear and direct
        4. Keep summaries to exactly two clear, concise sentences
        5. Do not use phrases like "this paper" or "the authors"
        6. Focus on what was done and what was found
        7. Do not tell readers to imagine anything or what to think
        8. Keep the original meaning intact while making it accessible
        """
        
        prompt = f"""
        Rewrite this title and summary in the simplest possible terms for a general audience.
        Give me just the simplified title and two-sentence summary with no extra text.
        
        Original Title: {title}
        Original Summary: {summary}

        Example response format:
        TITLE: How AI Can Learn from Its Mistakes
        SUMMARY: A new method helps AI systems understand and fix their own errors without human help. This improvement makes AI more reliable and reduces the need for constant human supervision.

        Your simplified version:
        """
        
        response = self.generate(prompt, system_prompt=system_prompt, temperature=0.3)
        
        # Extract simplified title and summary using the same format
        import re
        title_match = re.search(r'TITLE:\s*(.*?)(?=SUMMARY:|$)', response, re.DOTALL)
        summary_match = re.search(r'SUMMARY:\s*(.*?)$', response, re.DOTALL)
        
        if not title_match or not summary_match:
            # If the format isn't correct, try to force a clean-up
            response = self.cleanup_response(title, summary, response)
            title_match = re.search(r'TITLE:\s*(.*?)(?=SUMMARY:|$)', response, re.DOTALL)
            summary_match = re.search(r'SUMMARY:\s*(.*?)$', response, re.DOTALL)
        
        simplified_title = title_match.group(1).strip() if title_match else title
        simplified_summary = summary_match.group(1).strip() if summary_match else summary
        
        # Final validation and cleanup
        if len(simplified_title.split()) > 15:  # Title too long
            simplified_title = self.shorten_title(simplified_title)
            
        if len(simplified_summary.split('.')) > 2:  # Too many sentences
            simplified_summary = self.limit_sentences(simplified_summary)
        
        return simplified_title, simplified_summary

    def cleanup_response(self, original_title, original_summary, response):
        """Force cleanup of malformed response."""
        cleanup_prompt = f"""
        Reformat this simplified text into the exact format shown:
        TITLE: [single line title]
        SUMMARY: [exactly two sentences]

        Text to format:
        {response}
        """
        cleaned = self.generate(cleanup_prompt, temperature=0.1)
        if 'TITLE:' not in cleaned or 'SUMMARY:' not in cleaned:
            # If still malformed, fall back to original with markers
            return f"TITLE: {original_title}\nSUMMARY: {original_summary}"
        return cleaned

    def shorten_title(self, title):
        """Shorten a title that's too long."""
        shorten_prompt = f"""
        Make this title shorter and simpler while keeping the main point:
        {title}
        """
        return self.generate(shorten_prompt, temperature=0.1).strip()

    def limit_sentences(self, summary):
        """Ensure summary is exactly two sentences."""
        sentences = summary.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) <= 2:
            return summary
        
        combine_prompt = f"""
        Combine this information into exactly two clear sentences:
        {summary}
        """
        two_sentences = self.generate(combine_prompt, temperature=0.1)
        return two_sentences.strip()