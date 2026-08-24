# Presentation Slide & Audio Aligner

An AI-powered local web application that automatically aligns static presentation slides with an audio recording of a talk. It uses the Gemini API to analyze the transcript and speaker notes, generates timing options, and exports a perfectly aligned Final Cut Pro XML (FCP XML) ready for Adobe Premiere Pro.

## Features
- **AI Audio Alignment**: Uses Gemini 3.5 Flash to read a WebVTT transcript and a PDF of slides (including speaker notes) to intelligently guess when the speaker transitions to each slide.
- **Interactive Web UI**: Review Gemini's guesses, see alternative timing options with reasoning, and watch a live preview of the slides perfectly synced with the audio player and subtitles.
- **Premiere Pro Export**: Automatically updates a template FCP XML file with frame-accurate timings (25 FPS default) and absolute file paths, allowing you to import a fully cut sequence directly into Premiere Pro with zero manual syncing.
- **Smart Caching**: API responses are cached locally to save time and API tokens during reloads.

## Folder Structure
To use the tool, you must place your source files into the following specific directories:

- `audio-recording/` - Place your source audio file here (e.g., `audio.aac`, `audio.wav`, `audio.mp3`).
- `transcript/` - Place your WebVTT transcript here (e.g., `audio.vtt`). The AI uses speaker tags (like `<v Alan>`) to ignore audience chatter.
- `presentation-slides-pdf-with-notes/` - Place the PDF of your presentation here. The AI will extract the text and speaker notes.
- `presentation-slides-png/` - Export your slides as individual PNGs and place them here. Ensure they are sequentially named (e.g., `slide_Page_01.png`, `slide_Page_02.png`).
- `edl-in/` - Place a template FCP XML file here (e.g., `slides.xml`) exported from Premiere Pro containing your slides in order.
- `edl-out/` - The final, time-aligned `aligned_sequence.xml` will be saved here when you click Export.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/webziggy/slides-to-video-with-recordedvoiceover.git
   cd slides-to-video-with-recordedvoiceover
   ```

2. **Set up a Python Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key:**
   Copy the example environment file and add your Google Gemini API key.
   ```bash
   cp .env.example .env
   # Open .env and add your GEMINI_API_KEY
   ```

## Usage

1. Start the Flask server:
   ```bash
   python3 app.py
   ```
2. Open your web browser and navigate to `http://127.0.0.1:5000`
3. Click **Run AI Alignment**.
4. Review the timeline on the right. If the AI's primary guess is slightly off, click one of the alternative radio buttons to instantly update the timeline.
5. Click **Export FCP XML**.
6. Open Adobe Premiere Pro and go to `File > Import`. Select the `edl-out/aligned_sequence.xml` file. Your perfectly synced sequence will appear in your project bin!
