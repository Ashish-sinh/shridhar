import json
from typing import Dict, List, Any
import docx

class DocxTopicExtractor:
    def __init__(self):
        self.extracted_content = {}
    
    def extract_topics_and_subtopics(self, file_path: str, topic_filter: List[str] = None) -> Dict[str, Any]:
        """
        Extract topics (Heading 2) and subtopics (Heading 3) from DOCX file
        
        Args:
            file_path: Path to the DOCX file
            topic_filter: Optional list of specific topic titles to extract
        
        Returns:
            Dictionary with topics and their subtopics with content
        """
        doc = docx.Document(file_path)
        structure = {}
        current_topic = None
        current_subtopic = None
        current_text = []
        
        # Convert filter to lowercase for case-insensitive matching
        topic_filter_lower = [title.lower() for title in topic_filter] if topic_filter else None
        
        for paragraph in doc.paragraphs:
            paragraph_text = paragraph.text.strip()
            
            # Skip empty paragraphs
            if not paragraph_text:
                continue
            
            # Main topic (Heading 2)
            if paragraph.style.name == 'Heading 2':
                # Save previous content before switching topics
                if current_topic:
                    self._save_content(structure, current_topic, current_subtopic, current_text)
                
                # Check if this topic should be extracted
                if topic_filter_lower and paragraph_text.lower() not in topic_filter_lower:
                    current_topic = None
                    current_subtopic = None
                    current_text = []
                    continue
                
                # Start new topic
                current_topic = paragraph_text
                current_subtopic = None
                current_text = []
                structure[current_topic] = {'text': '', 'subtopics': {}}
            
            # Subtopic (Heading 3)
            elif paragraph.style.name == 'Heading 3' and current_topic:
                # Save previous subtopic content
                if current_subtopic:
                    structure[current_topic]['subtopics'][current_subtopic] = {'text': '\n'.join(current_text).strip()}
                
                # Start new subtopic
                current_subtopic = paragraph_text
                current_text = []
            
            # Regular content - only collect if we're tracking a topic
            elif current_topic and paragraph.style.name not in ['TOC 1', 'TOC 2', 'TOC 3', 'Header', 'Footer']:
                current_text.append(paragraph_text)
        
        # Save the last content
        if current_topic:
            self._save_content(structure, current_topic, current_subtopic, current_text)
        
        return structure
    
    def _save_content(self, structure: Dict, current_topic: str, current_subtopic: str, current_text: List[str]):
        """Save current content to the appropriate place in structure"""
        content = '\n'.join(current_text).strip()
        
        if current_subtopic:
            # Save to subtopic with 'text' key
            structure[current_topic]['subtopics'][current_subtopic] = {'text': content}
        else:
            # Save to main topic text
            structure[current_topic]['text'] = content
    
    def analyze_document_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze the document to show heading structure
        Helpful for understanding your document before extraction
        """
        doc = docx.Document(file_path)
        analysis = {
            'heading_counts': {},
            'topics': [],
            'structure_preview': []
        }
        
        current_topic = None
        
        for paragraph in doc.paragraphs:
            if paragraph.style.name.startswith('Heading') and paragraph.text.strip():
                style = paragraph.style.name
                text = paragraph.text.strip()
                
                # Count heading types
                if style not in analysis['heading_counts']:
                    analysis['heading_counts'][style] = 0
                analysis['heading_counts'][style] += 1
                
                # Track structure
                if style == 'Heading 2':
                    current_topic = text
                    analysis['topics'].append(text)
                    analysis['structure_preview'].append(f" {text}")
                elif style == 'Heading 3' and current_topic:
                    analysis['structure_preview'].append(f"   {text}")
        
        return analysis
    
    def save_to_json(self, structure: Dict[str, Any], output_file: str):
        """Save extracted content to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f" Content saved to '{output_file}'")
    
    def print_extraction_summary(self, structure: Dict[str, Any]):
        """Print a summary of extracted content"""
        print("\n" + "="*60)
        print(" EXTRACTION SUMMARY")
        print("="*60)
        
        print(f" Total Topics: {len(structure)}")
        total_subtopics = sum(len(content['subtopics']) for content in structure.values())
        print(f" Total Subtopics: {total_subtopics}")
        
        print("\n Content Details:")
        for topic_name, content in structure.items():
            main_text_chars = len(content['text'])
            subtopic_count = len(content['subtopics'])
            
            print(f"\n '{topic_name}'")
            print(f"   Main content: {main_text_chars} characters")
            print(f"   Subtopics: {subtopic_count}")
            
            for subtopic_name, subtopic_text in content['subtopics'].items():
                print(f"      {subtopic_name}: {len(subtopic_text['text'])} characters")
    
    def print_content_preview(self, structure: Dict[str, Any], preview_length: int = 150):
        """Print content with preview text"""
        print("\n" + "="*60)
        print(" CONTENT PREVIEW")
        print("="*60)
        
        for topic_name, content in structure.items():
            print(f"\n TOPIC: {topic_name}")
            print("-" * 50)
            
            if content['text']:
                preview = content['text'][:preview_length]
                if len(content['text']) > preview_length:
                    preview += "..."
                print(f"Main Text: {preview}")
            
            if content['subtopics']:
                print(f"\nSubtopics:")
                for subtopic_name, subtopic_text in content['subtopics'].items():
                    preview = subtopic_text['text'][:preview_length]
                    if len(subtopic_text['text']) > preview_length:
                        preview += "..."
                    print(f"  {subtopic_name}")
                    print(f"     {preview}")


def extract_json_from_doc(path: str):
    extractor = DocxTopicExtractor()
    structure = extractor.extract_topics_and_subtopics(path)
    extractor.save_to_json(structure,"test.json")
    return structure 