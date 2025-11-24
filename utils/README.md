# Utilities Module

This module contains common utility functions used across the CodeMateTR application to eliminate code duplication and improve maintainability.

## Modules

### text_utils.py
Text processing utilities for common text manipulation tasks.

**Functions:**
- `clean_markdown(text)` - Removes markdown formatting from text
- `extract_code_from_markdown(text)` - Extracts code blocks from markdown
- `extract_score_from_text(text)` - Extracts numeric scores from evaluation text
- `format_resource(resource, index)` - Formats learning resources for display

**Usage:**
```python
from utils.text_utils import clean_markdown

text = "## Header\n**Bold text**"
clean_text = clean_markdown(text)  # "Header\nBold text"
```

### config_utils.py
Configuration utilities for Flask application setup.

**Functions:**
- `configure_session(app, is_production)` - Configures Flask session settings
- `get_cors_config(is_production)` - Returns CORS configuration dictionary
- `is_production_environment()` - Checks if running in production

**Usage:**
```python
from utils.config_utils import configure_session, is_production_environment

# In app.py
configure_session(app, is_production=is_production_environment())
```

### audio_utils.py
Audio generation and handling utilities for speech features.

**Functions:**
- `save_wave_file(filename, pcm_data, ...)` - Saves PCM data as wave file
- `generate_speech_with_client(client, text, voice_name, model)` - Generates speech from text
- `create_audio_response(text, client, voice_name)` - Creates audio response with fallback

**Usage:**
```python
from utils.audio_utils import create_audio_response

response = create_audio_response(
    text="Hello, world!",
    client=gemini_client,
    voice_name='Kore'
)
# Returns dict with audio_file, audio_data, and text
```

### code_formatter.py
Code indentation and formatting utilities (pre-existing).

**Classes:**
- `CodeIndenter` - Multi-language code indentation support

## Benefits of Refactoring

1. **Reduced Duplication**: Eliminated ~191 lines of duplicated code
2. **Improved Maintainability**: Changes to common patterns only need to be made in one place
3. **Better Testability**: Utility functions can be tested independently
4. **Cleaner Code**: Main application files are more focused on business logic
5. **Reusability**: Utilities can be easily imported and used across the project

## Migration Guide

### For Markdown Cleanup
**Before:**
```python
import re
text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
```

**After:**
```python
from utils.text_utils import clean_markdown
text = clean_markdown(text)
```

### For Session Configuration
**Before:**
```python
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    # ... 20+ more lines
else:
    app.config['SESSION_COOKIE_SECURE'] = False
    # ... 10+ more lines
```

**After:**
```python
from utils.config_utils import configure_session, is_production_environment
configure_session(app, is_production=is_production_environment())
```

### For Audio Generation
**Before:**
```python
response = client.models.generate_content(...)
audio_data = response.candidates[0].content.parts[0].inline_data.data
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
with wave.open(temp_file.name, "wb") as wf:
    # ... wave file setup
```

**After:**
```python
from utils.audio_utils import create_audio_response
result = create_audio_response(text, client, voice_name)
```

## Testing

All utility modules have been verified to compile successfully:
```bash
python -m py_compile utils/text_utils.py
python -m py_compile utils/config_utils.py
python -m py_compile utils/audio_utils.py
```

## Future Improvements

- Add unit tests for all utility functions
- Add type hints for better IDE support
- Consider adding logging utilities
- Extract common database query patterns
- Add validation utilities for common input types
