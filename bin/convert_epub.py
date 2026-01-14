#!/usr/bin/env python3
"""
Convert EPUB to plain text for NotebookLM upload.
"""
import sys
from ebooklib import epub
from pathlib import Path

def epub_to_txt(epub_path, output_path):
    """Convert EPUB to plain text file."""
    print(f"📖 Reading EPUB: {epub_path}")

    try:
        book = epub.read_epub(epub_path)
        chapters = []

        # Get metadata
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown Title"
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown Author"

        print(f"📚 Title: {title}")
        print(f"✍️  Author: {author}")
        print(f"📄 Processing chapters...")

        # Extract text from all items
        for item in book.get_items():
            if item.get_type() == 9:  # ITEM_DOCUMENT = 9
                try:
                    # Extract text from HTML
                    content = item.get_content().decode('utf-8')
                    # Simple HTML tag removal
                    import re
                    text = re.sub(r'<[^>]+>', '\n', content)
                    text = re.sub(r'\n+', '\n', text)
                    text = text.strip()
                    if len(text) > 100:  # Only keep substantial content
                        chapters.append(text)
                except Exception as e:
                    print(f"⚠️  Error processing item: {e}")
                    continue

        # Combine all chapters
        full_text = f"\n{'='*80}\n"
        full_text += f"BOOK TITLE: {title}\n"
        full_text += f"AUTHOR: {author}\n"
        full_text += f"{'='*80}\n\n"

        for i, chapter in enumerate(chapters, 1):
            full_text += f"\n{'─'*80}\n"
            full_text += f"CHAPTER {i}\n"
            full_text += f"{'─'*80}\n\n"
            full_text += chapter
            full_text += "\n\n"

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

        file_size = len(full_text)
        print(f"\n✅ Conversion successful!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Characters: {file_size:,}")
        print(f"📖 Chapters: {len(chapters)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_epub.py <epub_file> [output_txt]")
        sys.exit(1)

    epub_file = sys.argv[1]
    if len(sys.argv) >= 3:
        txt_file = sys.argv[2]
    else:
        txt_file = Path(epub_file).stem + ".txt"

    success = epub_to_txt(epub_file, txt_file)
    sys.exit(0 if success else 1)
