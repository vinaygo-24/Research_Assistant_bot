import re

def extract_formulas_and_clean(text_objects):
    """
    Scans text objects for math formulas.
    Input: List of Dictionaries (from chunking.py)
    Output: List of Dictionaries (with updated 'type' if math is found)
    """
    processed_objects = []
    
    # Regex for common latex/math patterns
    math_pattern = r"(\$[^$]+\$|\\\[.*?\\\]|\\begin\{equation\}.*?\\end\{equation\}|[∑∫∂√∆])"
    
    for obj in text_objects:
        # --- FIX: Safe access to text ---
        content = obj.get("text", "") 
        
        # If content is somehow not a string (e.g. None), force it to empty string
        if not isinstance(content, str):
            content = ""
            
        matches = re.findall(math_pattern, content, re.DOTALL)
        
        # If significant math is found, tag it as 'formula'
        if len(matches) > 0 or "equation" in content.lower():
            obj["type"] = "formula"
            # Optional: Add a prefix to help the LLM context
            if "Mathematical Context" not in content:
                obj["text"] = f"Mathematical Context/Formula:\n{content}"
        
        processed_objects.append(obj)
        
    return processed_objects