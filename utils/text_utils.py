"""Text utility functions for common text processing tasks."""
import re


def clean_markdown(text):
    """
    Remove markdown formatting from text.
    
    Args:
        text (str): Text with markdown formatting
        
    Returns:
        str: Cleaned text without markdown
    """
    if not text:
        return text
    
    # Remove # and ## headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove ** bold markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove * italic markers
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Clean up excessive newlines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


def extract_code_from_markdown(text):
    """
    Extract code blocks from markdown formatted text.
    
    Args:
        text (str): Markdown text containing code blocks
        
    Returns:
        list: List of extracted code strings
    """
    # Match code blocks with optional language specifier
    code_matches = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
    return [code.strip() for code in code_matches]


def extract_score_from_text(text):
    """
    Extract numeric score from text.
    
    Args:
        text (str): Text containing a score (e.g., "Puan: 85")
        
    Returns:
        int: Extracted score or 0 if not found
    """
    if not text:
        return 0
    
    # Try to find score in format "puan: X" or "score: X"
    score_match = re.search(r'(?:puan|score)[:\s]*(\d+)', text.lower())
    if score_match:
        return int(score_match.group(1))
    
    # Fallback: detect based on keywords
    text_lower = text.lower()
    if any(word in text_lower for word in ['doğru', 'correct', 'başarılı', 'successful']):
        return 85
    elif any(word in text_lower for word in ['kısmen', 'partial', 'yarım']):
        return 60
    else:
        return 30


def format_resource(resource, index=None):
    """
    Format a learning resource for display.
    
    Args:
        resource (dict): Resource dictionary with title, url, description, etc.
        index (int, optional): Resource index for numbering
        
    Returns:
        str: Formatted resource text
    """
    formatted = ""
    
    if index is not None:
        formatted += f"{index}. "
    
    formatted += f"{resource.get('title', 'Untitled Resource')}\n"
    
    if 'url' in resource:
        formatted += f"🔗 URL: {resource['url']}\n"
    
    if 'description' in resource:
        formatted += f"📝 Açıklama: {resource['description']}\n"
    
    if 'benefit' in resource:
        formatted += f"✅ Neden Faydalı: {resource['benefit']}\n"
    
    if 'level' in resource:
        formatted += f"📊 Zorluk Seviyesi: {resource['level']}\n"
    
    formatted += "\n"
    return formatted
