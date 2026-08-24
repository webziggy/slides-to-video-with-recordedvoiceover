import xml.etree.ElementTree as ET
import os

class FCPXMLExporter:
    def __init__(self, template_path):
        """
        Initializes the exporter by parsing the provided FCP XML template.
        """
        self.template_path = template_path
        self.tree = ET.parse(template_path)
        self.root = self.tree.getroot()
        
    def get_slide_names(self):
        """
        Extracts the ordered list of slide filenames from the XML template.
        Returns a list of strings (e.g., ['slide_Page_01.png', ...])
        """
        slide_names = []
        # Find the video track containing the slides
        # In the provided XML, it's the first <video><track> block
        video_tracks = self.root.findall('.//media/video/track')
        if not video_tracks:
            return []
            
        track = video_tracks[0]
        for clipitem in track.findall('clipitem'):
            name_element = clipitem.find('name')
            if name_element is not None and name_element.text and name_element.text.startswith('slide_Page_'):
                slide_names.append(name_element.text)
                
        return slide_names

    def export_aligned_xml(self, slide_timings, output_path):
        """
        Modifies the XML template with new start/end frames for each slide and exports it.
        
        slide_timings: A list of dictionaries, e.g.,
        [
            {'name': 'slide_Page_01.png', 'start_frame': 0, 'end_frame': 250},
            ...
        ]
        """
        # Create a lookup dictionary for fast access
        timing_lookup = {item['name']: item for item in slide_timings}
        
        video_tracks = self.root.findall('.//media/video/track')
        if not video_tracks:
            raise ValueError("No video tracks found in the template XML.")
            
        track = video_tracks[0]
        
        for clipitem in track.findall('clipitem'):
            name_element = clipitem.find('name')
            if name_element is not None and name_element.text in timing_lookup:
                timing = timing_lookup[name_element.text]
                
                # Update <start> and <end>
                start_elem = clipitem.find('start')
                end_elem = clipitem.find('end')
                
                if start_elem is not None:
                    start_elem.text = str(timing['start_frame'])
                if end_elem is not None:
                    end_elem.text = str(timing['end_frame'])
                    
                # Update <out> based on the new duration to keep Premiere happy.
                # duration = end_frame - start_frame
                # out = in + duration
                in_elem = clipitem.find('in')
                out_elem = clipitem.find('out')
                duration_elem = clipitem.find('duration')
                
                if in_elem is not None and out_elem is not None:
                    in_val = int(in_elem.text)
                    duration = timing['end_frame'] - timing['start_frame']
                    out_elem.text = str(in_val + duration)
                    
                    if duration_elem is not None:
                        # Some versions of Premiere strictly check the <duration> tag
                        duration_elem.text = str(duration)
                        
        # Write the modified XML to the output path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write with standard XML declaration
        self.tree.write(output_path, encoding='UTF-8', xml_declaration=True)
        
        # Premiere FCP XMLs require a specific DOCTYPE that ElementTree strips out
        # We need to manually inject the <!DOCTYPE xmeml> line
        with open(output_path, 'r') as f:
            content = f.read()
            
        if '<!DOCTYPE xmeml>' not in content:
            content = content.replace("<?xml version='1.0' encoding='UTF-8'?>", 
                                      '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>')
            
            with open(output_path, 'w') as f:
                f.write(content)

if __name__ == "__main__":
    # Quick test to verify it works
    exporter = FCPXMLExporter('edl-in/slides.xml')
    slides = exporter.get_slide_names()
    print(f"Found {len(slides)} slides:")
    for slide in slides[:3]: # Print first 3
        print(f" - {slide}")
