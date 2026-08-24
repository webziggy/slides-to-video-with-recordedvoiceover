from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import logging
from alignment_engine import AlignmentEngine
from fcp_xml_exporter import FCPXMLExporter

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", mode='w'), # overwrite log on restart
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Constants for directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, 'audio-recording')
TRANSCRIPT_DIR = os.path.join(BASE_DIR, 'transcript')
PNG_DIR = os.path.join(BASE_DIR, 'presentation-slides-png')
PDF_DIR = os.path.join(BASE_DIR, 'presentation-slides-pdf-with-notes')
EDL_IN_DIR = os.path.join(BASE_DIR, 'edl-in')
EDL_OUT_DIR = os.path.join(BASE_DIR, 'edl-out')

@app.route('/media/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

@app.route('/media/transcript/<filename>')
def serve_transcript(filename):
    return send_from_directory(TRANSCRIPT_DIR, filename)

@app.route('/media/slides/<filename>')
def serve_slides(filename):
    return send_from_directory(PNG_DIR, filename)

@app.route('/')
def index():
    logger.info("Serving Index HTML")
    # Support multiple common audio formats
    valid_exts = ('.wav', '.mp3', '.aac', '.m4a')
    audio_file = next((f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(valid_exts)), None)
    vtt_file = next((f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith('.vtt')), None)
    return render_template('index.html', audio_file=audio_file, vtt_file=vtt_file)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        with open("app.log", "r") as f:
            return jsonify({"logs": f.read()})
    except FileNotFoundError:
        return jsonify({"logs": ""})

@app.route('/api/align', methods=['POST'])
def run_alignment():
    logger.info("API Request received: /api/align")
    try:
        exporter = FCPXMLExporter(os.path.join(EDL_IN_DIR, 'slides.xml'))
        slide_names = exporter.get_slide_names()
        logger.info(f"Extracted {len(slide_names)} slide names from slides.xml template.")
        
        pdf_file = next((f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')), None)
        vtt_file = next((f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith('.vtt')), None)
        
        if not pdf_file or not vtt_file:
            logger.error("Missing PDF or VTT file.")
            return jsonify({"error": "Missing PDF or VTT file in the designated folders."}), 400
            
        engine = AlignmentEngine()
        timings = engine.align(
            pdf_path=os.path.join(PDF_DIR, pdf_file),
            vtt_path=os.path.join(TRANSCRIPT_DIR, vtt_file),
            ordered_slide_names=slide_names
        )
        
        logger.info("Alignment complete. Sending timings to frontend.")
        return jsonify({"success": True, "timings": timings})
        
    except Exception as e:
        logger.error(f"Error during alignment: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_xml():
    logger.info("API Request received: /api/export")
    try:
        data = request.json
        if not data or 'timings' not in data:
            logger.error("No timings provided in export request.")
            return jsonify({"error": "No timings provided"}), 400
            
        final_timings = data['timings']
        logger.info(f"Exporting XML for {len(final_timings)} slides...")
        
        exporter = FCPXMLExporter(os.path.join(EDL_IN_DIR, 'slides.xml'))
        output_path = os.path.join(EDL_OUT_DIR, 'aligned_sequence.xml')
        
        exporter.export_aligned_xml(final_timings, output_path)
        logger.info(f"Successfully exported FCP XML to {output_path}")
        
        return jsonify({"success": True, "message": f"Exported to edl-out/aligned_sequence.xml"})
        
    except Exception as e:
        logger.error(f"Error during export: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
