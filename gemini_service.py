import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        # The user mentioned using API key from .env
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            # Fallback to check if it's passed via environment directly
            self.api_key = os.environ.get("GOOGLE_API_KEY")
            
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please ensure it is set in the .env file or environment variables.")
            
        genai.configure(api_key=self.api_key)
        
        # Dynamically detect available Flash models to avoid 404/429 issues
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Preference list: 1.5-flash, then 2.0-flash, then any flash
            if 'models/gemini-1.5-flash' in available_models:
                self.model_name = 'models/gemini-1.5-flash'
            elif 'models/gemini-2.0-flash' in available_models:
                self.model_name = 'models/gemini-2.0-flash'
            else:
                flash_models = [m for m in available_models if 'flash' in m]
                self.model_name = flash_models[0] if flash_models else 'models/gemini-1.5-flash'
            
            print(f"[+] Using Gemini model: {self.model_name}")
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            print(f"[-] Model detection failed: {e}. Defaulting to gemini-1.5-flash.")
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def translate_term(self, term, target_lang_name):
        """
        Translates a French concept into a target language using Gemini Flash.
        Includes retry logic for 429 errors.
        """
        prompt = (
            f"Translate the French word '{term}' into the {target_lang_name} language spoken in Congo-Brazzaville. "
            f"Provide only the translated word, no explanations."
        )
        system_instruction = "You are a linguist specializing in the languages of Congo-Brazzaville (Lingala, Kituba, Lari, Vili, Mbochi, English, Slovak)."
        
        # Robust retry for free-tier limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                full_prompt = f"{system_instruction}\n\n{prompt}"
                response = self.model.generate_content(full_prompt)
                if response and response.text:
                    return response.text.strip()
                return None
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    wait_time = 60 # 1 minute for safety
                    print(f"    [!] Quota exceeded. Sleeping {wait_time}s before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                print(f"API Error: {e}")
                break
        return None

def translate_term(term, target_lang_name):
    """Utility function for easy access."""
    try:
        service = GeminiService()
        return service.translate_term(term, target_lang_name)
    except Exception as e:
        print(f"Service Error: {e}")
        return None
