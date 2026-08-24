# Presentation Slide & Audio Aligner

An AI-powered local web application that automatically aligns static presentation slides with an audio recording of a talk. It uses the Gemini API to analyze the transcript and speaker notes, generates timing options, and exports a perfectly aligned Final Cut Pro XML (FCP XML) ready for Adobe Premiere Pro.

## The Full Workflow (From Stage to LinkedIn)
This tool was built to solve a real-world problem: turning a live stage presentation into a polished video for LinkedIn. Here is the complete workflow used to achieve the final result:
1. **Audio Enhancement:** The raw audio recording from the event was first run through an AI audio enhancer to remove background noise and clear up the voice recording.
2. **Transcription:** The enhanced audio was fed into MacWhisper (running locally) to generate a highly accurate WebVTT (`.vtt`) transcript with speaker detection.
3. **AI Alignment (This Tool):** We built this custom Python/Flask app to feed the `.vtt` transcript and the original PDF slide deck (including speaker notes) into the **Google Gemini 3.5 Flash** API. Gemini intelligently calculated the exact timestamp when the speaker transitioned to each slide.
4. **Visual Review:** Using the web interface, we reviewed the AI's timing choices, listening to the audio and watching the slides automatically update in real-time.
5. **Premiere Pro Assembly:** The tool exported a Final Cut Pro XML (FCP XML) file containing frame-accurate cuts. This was imported directly into Adobe Premiere Pro, instantly assembling the final video timeline with zero manual syncing required.

## Required Inputs & Formats
To use the tool, you must collate the following specific files and place them into their respective directories:

- `audio-recording/`
  - **Format:** `.aac`, `.wav`, `.m4a`, or `.mp3`
  - **Details:** Your primary audio recording of the presentation.
- `transcript/`
  - **Format:** WebVTT (`.vtt`)
  - **Details:** The transcript of your audio. We used MacWhisper to generate this. The AI can use speaker tags (like `<v Alan>`) to ignore audience chatter or Q&A sessions.
- `presentation-slides-pdf-with-notes/`
  - **Format:** `.pdf`
  - **Details:** An export of your presentation deck. It is highly recommended that this PDF includes your speaker notes, as the AI uses them to contextually match what you are saying to the correct slide.
- `presentation-slides-png/`
  - **Format:** `.png`
  - **Details:** Export your slides as individual image files. Ensure they are sequentially named (e.g., `slide_Page_01.png`, `slide_Page_02.png`). These are used for the web preview and are linked directly into Premiere Pro.
- `edl-in/`
  - **Format:** Final Cut Pro XML (`.xml`)
  - **Details:** Create a basic sequence in Premiere Pro containing your slides in order, and export it as an FCP XML (e.g., `slides.xml`). Our tool uses this exact file as a master template to preserve media links and sequence settings (like your framerate).
- `edl-out/`
  - **Format:** Final Cut Pro XML (`.xml`)
  - **Details:** Empty directory. The final, time-aligned `aligned_sequence.xml` will be saved here when you click Export.

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
