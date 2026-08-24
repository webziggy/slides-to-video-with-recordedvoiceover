import os
import json
import webvtt
import logging
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AlignmentEngine:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set.")
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3.5-flash')
        self.fps = 25
        # We store the cache at the root of the project
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timings_cache.json')

    def extract_pdf_text(self, pdf_path):
        logger.info(f"Extracting text from PDF: {os.path.basename(pdf_path)}")
        reader = PdfReader(pdf_path)
        slides_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            slides_text.append({
                "slide_number": i + 1,
                "text": text.strip() if text else ""
            })
        logger.info(f"Extracted text for {len(slides_text)} slides.")
        return slides_text

    def parse_vtt(self, vtt_path):
        logger.info(f"Parsing VTT transcript: {os.path.basename(vtt_path)}")
        captions = []
        for caption in webvtt.read(vtt_path):
            captions.append({
                "start": caption.start,
                "end": caption.end,
                "text": caption.text.strip(),
                "start_seconds": caption.start_in_seconds,
                "end_seconds": caption.end_in_seconds
            })
        logger.info(f"Parsed {len(captions)} caption blocks.")
        return captions

    def align(self, pdf_path, vtt_path, ordered_slide_names):
        logger.info("Starting AI alignment process...")
        
        # --- CACHE CHECK ---
        if os.path.exists(self.cache_file):
            cache_mtime = os.path.getmtime(self.cache_file)
            pdf_mtime = os.path.getmtime(pdf_path)
            vtt_mtime = os.path.getmtime(vtt_path)
            
            if cache_mtime > pdf_mtime and cache_mtime > vtt_mtime:
                logger.info("Found valid cached timings from previous run. Loading 'timings_cache.json' to save time & API usage.")
                try:
                    with open(self.cache_file, "r") as f:
                        cached_timings = json.load(f)
                    return cached_timings
                except Exception as e:
                    logger.warning(f"Failed to read cache file, re-running AI alignment. Error: {e}")
            else:
                logger.info("Cached timings found, but PDF or VTT files have been modified since. Re-running AI alignment.")
        
        slides_text = self.extract_pdf_text(pdf_path)
        captions = self.parse_vtt(vtt_path)
        
        prompt = f"""
You are an expert video editor and presentation aligner. 
I have a presentation with {len(ordered_slide_names)} slides.
I am providing you with the text/speaker notes for each slide extracted from a PDF, and a WebVTT transcript of the audio recording of the presentation.

Your task is to determine the exact timestamp (in seconds) when the speaker transitions to each slide. 
Note: The speaker in the transcript is labelled as <v Alan Ogilvie>. You can ignore chatter from <v Other> (the audience).
There may be long periods of silence or audience interaction where a single slide stays on screen for a long time.

Here are the slide names you must map to:
{json.dumps(ordered_slide_names, indent=2)}

Here is the extracted slide text/notes:
{json.dumps(slides_text, indent=2)}

Here is the VTT Transcript:
{json.dumps(captions, indent=2)}

CRITICAL: You must output ONLY a valid JSON array of objects. Do not include markdown formatting like ```json. Just the raw JSON.
The array must contain exactly {len(ordered_slide_names)} objects, one for each slide in order.
Each object must have exactly these keys:
- "name": The exact filename of the slide (e.g., "slide_Page_01.png")
- "options": An array of 2 to 3 objects representing possible start times for when this slide should appear. Order them from highest confidence to lowest confidence.
  Each option object must have:
  - "time": The start time in seconds (float). The first slide's options must just be [{{"time": 0.0, "reason": "First slide"}}].
  - "reason": A brief explanation of why you chose this timestamp.
- "notes": A string where you can leave a note for the user. (e.g. "Speaker mentioned this topic early, but ordinal order forced a later choice.")

RULES:
1. Slides MUST appear in their ordinal order. Assume the presenter never physically moves back to a previous slide on the screen.
2. If the speaker mentions a topic from a previous slide later in the presentation, ignore it for timing purposes, but you can flag it in the "notes" field.
3. Ensure you provide plausible alternative timings in the options array.

Output only the raw JSON array.
"""
        
        logger.info("Sending data to Gemini API for alignment... (this may take a minute depending on transcript length)")
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.2)
            )
            
            logger.info("Received response from Gemini API. Parsing JSON...")
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            timings = json.loads(raw_text.strip())
            logger.info(f"Successfully mapped timings for {len(timings)} slides.")
            
            # Ensure every slide has a notes field for the UI, and validate options
            for slide in timings:
                if "notes" not in slide:
                    slide["notes"] = ""
                # Ensure options is an array
                if "options" not in slide or not isinstance(slide["options"], list):
                    logger.warning(f"Slide {slide.get('name')} is missing 'options' array. Injecting fallback.")
                    slide["options"] = [{"time": 0.0, "reason": "Fallback - Gemini failed to provide options"}]
                else:
                    for opt in slide["options"]:
                        # Convert times to float just in case
                        try:
                            opt["time"] = float(opt.get("time", 0.0))
                        except (ValueError, TypeError):
                            opt["time"] = 0.0
                        if "reason" not in opt:
                            opt["reason"] = "No reason provided."
            
            # --- SAVE CACHE ---
            try:
                with open(self.cache_file, "w") as f:
                    json.dump(timings, f, indent=2)
                logger.info("Saved timings to timings_cache.json for future use.")
            except Exception as e:
                logger.warning(f"Failed to save timings cache: {e}")
            
            return timings
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            if 'response' in locals():
                logger.error(f"Raw Response snippet: {response.text[:500]}...")
            raise e
