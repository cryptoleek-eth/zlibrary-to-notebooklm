#!/usr/bin/env python3
"""
Z-Library Full Auto-Download and Upload to NotebookLM
"""

import asyncio
import sys
import time
import re
from pathlib import Path
from urllib.parse import unquote

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed")
    print("Please run: pip install playwright")
    sys.exit(1)


class ZLibraryAutoUploader:
    """Z-Library Automatic Download and Uploader"""

    def __init__(self):
        self.downloads_dir = Path.home() / "ZLibraryDownloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        self.temp_dir = Path("/tmp")
        self.config_dir = Path.home() / ".zlibrary"
        self.config_file = self.config_dir / "config.json"

    def load_credentials(self) -> dict | None:
        """Load Z-Library credentials"""
        if not self.config_file.exists():
            return None

        try:
            import json
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return None

    async def login_to_zlibrary(self, page):
        """Login to Z-Library"""
        credentials = self.load_credentials()

        if not credentials:
            print("⚠️  Z-Library config not found")
            print("💡 Please run first: python3 /tmp/zlib_config.py")
            return False

        print("🔐 Logging in to Z-Library...")
        print(f"📧 Using account: {credentials['email']}")

        try:
            # Check if login dialog already exists
            modal = await page.query_selector('#zlibrary-modal-auth')
            if modal:
                print("📝 Login dialog detected")
                # Input directly in dialog
                email_input = await page.wait_for_selector('#modal-auth input[type="email"], #modal-auth input[name="email"]', timeout=5000)
                await email_input.fill(credentials['email'])

                password_input = await page.wait_for_selector('#modal-auth input[type="password"], #modal-auth input[name="password"]', timeout=5000)
                await password_input.fill(credentials['password'])

                # Click login
                submit_button = await page.wait_for_selector('#modal-auth button[type="submit"]', timeout=5000)
                await submit_button.click()
            else:
                # Click login button
                login_button = await page.wait_for_selector('a:has-text("Log in"), a:has-text("登录")', timeout=5000)
                await login_button.click()
                await asyncio.sleep(2)

                # Enter email
                email_input = await page.wait_for_selector('input[type="email"], input[name="email"]', timeout=5000)
                await email_input.fill(credentials['email'])

                # Enter password
                password_input = await page.wait_for_selector('input[type="password"], input[name="password"]', timeout=5000)
                await password_input.fill(credentials['password'])

                # Click login
                submit_button = await page.wait_for_selector('button[type="submit"], button:has-text("Log in"), button:has-text("登录")', timeout=5000)
                await submit_button.click()

            # Wait for login to complete
            await asyncio.sleep(5)

            # Check if login successful
            current_url = page.url
            page_content = await page.content()

            if "logout" in page_content.lower() or "登录" not in page_content:
                print("✅ Login successful")
                return True
            else:
                print("❌ Login may have failed, please check account credentials")
                return False

        except Exception as e:
            print(f"❌ Login process error: {e}")
            return False

    async def download_from_zlibrary(self, url: str) -> Path | None:
        """Download book from Z-Library"""
        print("="*70)
        print("🌐 Starting browser automation download")
        print("="*70)

        # Check if saved session exists
        storage_state = self.config_dir / "storage_state.json"

        if not storage_state.exists():
            print("❌ Session state not found")
            print("💡 Please run first: python3 /tmp/zlibrary_login.py")
            return None

        print(f"✅ Using saved session")

        async with async_playwright() as p:
            # Launch browser (using persistent context)
            print("🚀 Launching browser...")

            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.config_dir / "browser_profile"),
                headless=False,
                accept_downloads=True,
                args=['--disable-blink-features=AutomationControlled']
            )

            page = browser.pages[0] if browser.pages else await browser.new_page()
            page.set_default_timeout(60000)

            # Setup download handler
            download_path = None
            download_complete = False
            download_started = False

            async def handle_download(download):
                nonlocal download_path, download_complete, download_started
                try:
                    download_started = True
                    suggested_filename = download.suggested_filename
                    print(f"✅ Download started: {suggested_filename}")
                    download_path = self.downloads_dir / suggested_filename
                    
                    # Use download path directly - let browser save it
                    await download.save_as(str(download_path))
                    download_complete = True
                    print(f"💾 Saved: {download_path}")
                except Exception as e:
                    print(f"⚠️  Download handler error: {e}")
                    # Don't fail - we'll check directory as fallback

            page.on('download', handle_download)

            try:
                # Visit target page
                print(f"📖 Visiting book page...")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                print("⏳ Waiting for page to load...")
                await asyncio.sleep(5)

                # Step 1: Find download method (prioritize PDF, then EPUB)
                print("🔍 Step 1: Finding download method...")

                # First check if there's a three-dot menu button (new interface)
                dots_button = await page.query_selector('button[aria-label="更多选项"], button[title="更多"], .more-options, [class*="dots"], [class*="more"]')

                download_link = None
                downloaded_format = None

                if dots_button:
                    print("📱 Detected new interface (three-dot menu)")
                    # Click to open menu
                    await dots_button.click()
                    await asyncio.sleep(2)

                    # Find PDF option (priority)
                    print("🔍 Searching for PDF option...")
                    pdf_options = await page.query_selector_all('a:has-text("PDF"), button:has-text("PDF")')
                    if pdf_options:
                        # Look for actual download links only (with href="/dl/")
                        for option in pdf_options:
                            href = await option.get_attribute('href')
                            if href and '/dl/' in href:
                                download_link = option
                                downloaded_format = 'pdf'
                                print(f"✅ Found PDF download link")
                                break
                        
                        if not download_link:
                            print("⚠️  PDF options found but no download link, trying EPUB...")
                    
                    if not download_link:
                        # Fallback: search for EPUB
                        print("🔍 Searching for EPUB option...")
                        epub_options = await page.query_selector_all('a:has-text("EPUB"), button:has-text("EPUB")')
                        if epub_options:
                            for option in epub_options:
                                href = await option.get_attribute('href')
                                if href and '/dl/' in href:
                                    download_link = option
                                    downloaded_format = 'epub'
                                    print(f"✅ Found EPUB download link")
                                    break

                else:
                    # Old interface: check conversion button
                    print("📱 Detected old interface")
                    convert_selector_pdf = 'a[data-convert_to="pdf"]'
                    convert_selector_epub = 'a[data-convert_to="epub"]'

                    # Try PDF first
                    convert_button = await page.query_selector(convert_selector_pdf)

                    if convert_button:
                        print("📝 PDF conversion button detected")
                        downloaded_format = 'pdf'
                        await convert_button.evaluate('el => el.click()')
                        print("✅ Clicked PDF conversion button")

                        # Wait for conversion to complete
                        print("⏳ Waiting for PDF conversion to complete...")
                        for i in range(60):
                            await asyncio.sleep(1)
                            try:
                                message = await page.query_selector('.message:has-text("转换为")')
                                if message:
                                    message_text = await message.inner_text()
                                    if 'pdf' in message_text.lower() and '完成' in message_text:
                                        print("✅ PDF conversion completed!")
                                        break
                            except:
                                pass
                            if i % 10 == 0 and i > 0:
                                print(f"   ⏳ Waiting... {i} seconds")

                        # Find download link
                        download_link = await page.query_selector('a[href*="/dl/"][href*="convertedTo=pdf"]')

                        if not download_link:
                            all_links = await page.query_selector_all('a[href*="/dl/"]')
                            if all_links:
                                download_link = all_links[0]
                                href = await download_link.get_attribute('href')
                                print(f"✅ Found download link: {href}")

                    else:
                        # Fallback: try EPUB
                        convert_button = await page.query_selector(convert_selector_epub)

                        if convert_button:
                            print("📝 EPUB conversion button detected")
                            downloaded_format = 'epub'
                            await convert_button.evaluate('el => el.click()')
                            print("✅ Clicked EPUB conversion button")

                            # Wait for conversion to complete
                            print("⏳ Waiting for EPUB conversion to complete...")
                            for i in range(60):
                                await asyncio.sleep(1)
                                try:
                                    message = await page.query_selector('.message:has-text("转换为")')
                                    if message:
                                        message_text = await message.inner_text()
                                        if 'epub' in message_text.lower() and '完成' in message_text:
                                            print("✅ EPUB conversion completed!")
                                            break
                                except:
                                    pass
                                if i % 10 == 0 and i > 0:
                                    print(f"   ⏳ Waiting... {i} seconds")

                            # Find download link
                            download_link = await page.query_selector('a[href*="/dl/"][href*="convertedTo=epub"]')

                            if not download_link:
                                all_links = await page.query_selector_all('a[href*="/dl/"]')
                                if all_links:
                                    download_link = all_links[0]
                                    href = await download_link.get_attribute('href')
                                    print(f"✅ Found download link: {href}")

                # If still not found, try direct download links (more comprehensive)
                if not download_link:
                    print("🔍 Searching for direct download link...")

                    selectors = [
                        'a[href*="/dl/"]',  # Direct download links
                        'a.dlButton',  # Common download button class
                        'button.addDownloadedBook',  # Download tracking button
                        'a:has-text("下载文档")',  # Chinese "download document"
                        'a:has-text("下载")',
                        'a:has-text("Download")',
                    ]

                    for selector in selectors:
                        try:
                            links = await page.query_selector_all(selector)
                            if links:
                                for link in links:
                                    href = await link.get_attribute('href') or ''
                                    onclick = await link.get_attribute('onclick') or ''
                                    
                                    # Check if it's a real download link
                                    if '/dl/' in href or 'download' in onclick.lower():
                                        download_link = link
                                        # Determine format from URL or page content
                                        if 'pdf' in href.lower() or 'pdf' in onclick.lower():
                                            downloaded_format = 'pdf'
                                        elif 'epub' in href.lower() or 'epub' in onclick.lower():
                                            downloaded_format = 'epub'
                                        else:
                                            # Try to detect from page
                                            page_text = await page.content()
                                            if 'PDF' in page_text and '完成' in page_text:
                                                downloaded_format = 'pdf'
                                            else:
                                                downloaded_format = 'epub'
                                        
                                        link_text = await link.inner_text() if hasattr(link, 'inner_text') else ''
                                        print(f"✅ Found download link: {href or onclick} (format: {downloaded_format})")
                                        break
                                if download_link:
                                    break
                        except Exception as e:
                            continue

                if not download_link:
                    print("❌ Download link not found")
                    await browser.close()
                    return None

                # Click download
                print("⬇️  Step 2: Clicking download link...")

                try:
                    await download_link.evaluate('el => el.click()')
                    print("✅ Click successful")
                except Exception as e:
                    print(f"❌ Click failed: {e}")
                    await browser.close()
                    return None

                # Wait for download to complete
                print("⏳ Step 3: Waiting for download to complete...")
                max_wait = 60  # Wait up to 1 minute for download handler
                for i in range(max_wait):
                    await asyncio.sleep(1)
                    
                    # Check if download completed via handler
                    if download_complete and download_path and download_path.exists():
                        break
                    
                    # Fallback: Check if file appeared in directory (even if handler failed)
                    if download_started and download_path and download_path.exists():
                        file_size = download_path.stat().st_size
                        if file_size > 0:  # File has content
                            print(f"✅ Download detected in directory!")
                            download_complete = True
                            break
                    
                    if i % 10 == 9:
                        print(f"   ⏳ Still waiting... {i+1} seconds")

                # Check result
                if download_path and download_path.exists():
                    file_size = download_path.stat().st_size / 1024
                    print(f"✅ Download successful!")
                    print(f"   Format: {downloaded_format.upper() if downloaded_format else 'Unknown'}")
                    print(f"   File: {download_path.name}")
                    print(f"   Path: {download_path}")
                    print(f"   Size: {file_size:.1f} KB")
                    await browser.close()
                    return download_path, downloaded_format

                # Fallback: check downloads directory
                print("🔍 Checking downloads directory...")

                # Find files based on format
                if downloaded_format == 'pdf':
                    pattern = "*.pdf"
                else:
                    pattern = "*.epub"

                downloaded_files = list(self.downloads_dir.glob(pattern))

                if downloaded_files:
                    latest_file = max(downloaded_files, key=lambda p: p.stat().st_mtime)
                    file_age = time.time() - latest_file.stat().st_mtime

                    if file_age < 120:
                        file_size = latest_file.stat().st_size / 1024
                        print(f"✅ Download successful!")
                        print(f"   Format: {downloaded_format.upper() if downloaded_format else 'Unknown'}")
                        print(f"   File: {latest_file.name}")
                        print(f"   Path: {latest_file}")
                        print(f"   Size: {file_size:.1f} KB")
                        await browser.close()
                        return latest_file, downloaded_format

                print("❌ Downloaded file not found")
                await browser.close()
                return None, None

            except Exception as e:
                print(f"❌ Download failed: {e}")
                import traceback
                traceback.print_exc()
                await browser.close()
                return None, None

    def count_words(self, text: str) -> int:
        """Count Chinese and English words"""
        import re
        # Match Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # Match English words
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        return chinese_chars + english_words

    def split_markdown_file(self, file_path: Path, max_words: int = 350000) -> list[Path]:
        """Split large Markdown file into multiple smaller files"""
        print(f"📊 File too large, starting split...")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        total_words = self.count_words(content)
        print(f"   Total words: {total_words:,}")
        print(f"   Max per chunk: {max_words:,} words")

        # Split by chapters (looking for ## or ### headings)
        import re
        chapters = re.split(r'\n(?=#{1,3}\s)', content)

        chunks = []
        current_chunk = ""
        current_words = 0
        chunk_num = 1

        for i, chapter in enumerate(chapters):
            chapter_words = self.count_words(chapter)

            # If single chapter exceeds limit, need further splitting
            if chapter_words > max_words:
                # First save current chunk
                if current_chunk:
                    chunks.append(current_chunk)
                    chunk_num += 1
                    current_chunk = ""
                    current_words = 0

                # Split large chapter (by paragraphs)
                paragraphs = chapter.split('\n\n')
                temp_chunk = ""
                temp_words = 0

                for para in paragraphs:
                    para_words = self.count_words(para)
                    if temp_words + para_words > max_words and temp_chunk:
                        chunks.append(temp_chunk)
                        chunk_num += 1
                        temp_chunk = para + "\n\n"
                        temp_words = para_words
                    else:
                        temp_chunk += para + "\n\n"
                        temp_words += para_words

                if temp_chunk:
                    current_chunk = temp_chunk
                    current_words = temp_words

            elif current_words + chapter_words > max_words:
                # Current chunk is full, save and start new one
                chunks.append(current_chunk)
                chunk_num += 1
                current_chunk = chapter + "\n\n"
                current_words = chapter_words
            else:
                # Add to current chunk
                current_chunk += chapter + "\n\n"
                current_words += chapter_words

        # Save last chunk
        if current_chunk:
            chunks.append(current_chunk)

        # Write files
        chunk_files = []
        stem = file_path.stem
        for i, chunk in enumerate(chunks, 1):
            chunk_file = file_path.parent / f"{stem}_part{i}.md"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
            chunk_files.append(chunk_file)
            chunk_words = self.count_words(chunk)
            print(f"   ✅ Part {i}/{len(chunks)}: {chunk_words:,} words")

        return chunk_files

    def convert_to_txt(self, file_path: Path, file_format: str = None) -> Path | list[Path]:
        """Convert file to TXT or use PDF directly"""
        print("")
        print("="*70)
        print("📝 Processing file")
        print("="*70)

        file_ext = file_path.suffix.lower()

        # If PDF, use directly (Solution A)
        if file_ext == '.pdf' or file_format == 'pdf':
            print("✅ PDF format detected, using directly")
            print(f"   File: {file_path.name}")
            return file_path

        md_file = self.temp_dir / f"{file_path.stem}.md"

        # If EPUB, convert to Markdown
        if file_ext == '.epub':
            print("📖 EPUB format detected, converting to Markdown...")
            # Get script directory
            script_dir = Path(__file__).parent
            convert_script = script_dir / "convert_epub.py"

            cmd = f"python3 '{convert_script}' '{file_path}' '{md_file}'"
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Conversion failed: {result.stderr}")
                return file_path

            print(f"✅ Conversion successful: {md_file}")

            # Check file size, split if too large
            word_count = self.count_words(open(md_file, 'r', encoding='utf-8').read())
            print(f"📊 Word count: {word_count:,}")

            if word_count > 350000:
                print(f"⚠️  File exceeds 350k words (NotebookLM CLI limit)")
                return self.split_markdown_file(md_file)
            else:
                return md_file

        else:
            print(f"ℹ️  File format: {file_ext}, using directly")
            return file_path

    def upload_to_notebooklm(self, file_path: Path | list[Path], title: str = None) -> dict:
        """Upload to NotebookLM"""
        print("")
        print("="*70)
        print("⬆️  Uploading to NotebookLM")
        print("="*70)

        # Handle file list (split files)
        if isinstance(file_path, list):
            print(f"📦 Detected {len(file_path)} file chunks")

            # Use first file to determine book title
            first_file = file_path[0]
            if not title:
                title = first_file.stem.replace('_part1', '').replace('_', ' ')
                # Clean filename
                title = re.sub(r'\[.*?\]', '', title)
                title = re.sub(r'\(.*?\)', '', title)
                title = re.sub(r'\s+', ' ', title).strip()
                if len(title) > 50:
                    title = title[:50] + "..."

            # Create notebook
            print(f"📚 Creating notebook: {title}")
            import subprocess
            import json

            cmd = f"notebooklm create '{title}' --json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            try:
                data = json.loads(result.stdout)
                notebook_id = data['notebook']['id']
                print(f"✅ Notebook created (ID: {notebook_id[:8]}...)")
            except:
                return {"success": False, "error": "Failed to parse notebook ID"}

            # Set context
            print(f"🎯 Setting notebook context...")
            cmd = f"notebooklm use {notebook_id}"
            subprocess.run(cmd, shell=True, capture_output=True)

            # Upload all chunks
            source_ids = []
            for i, chunk_file in enumerate(file_path, 1):
                print(f"📄 Uploading chunk {i}/{len(file_path)}: {chunk_file.name}")
                cmd = f"notebooklm source add '{chunk_file}' --json"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"⚠️  Chunk {i} upload failed: {result.stderr}")
                    continue

                try:
                    data = json.loads(result.stdout)
                    source_id = data['source']['id']
                    source_ids.append(source_id)
                    print(f"   ✅ Success (ID: {source_id[:8]}...)")
                except:
                    print(f"⚠️  Chunk {i} parsing failed")

            return {
                "success": len(source_ids) > 0,
                "notebook_id": notebook_id,
                "source_ids": source_ids,
                "title": title,
                "chunks": len(file_path)
            }

        # Single file upload
        # Determine book title
        if not title:
            title = file_path.stem.replace('_', ' ')
            # Clean filename
            title = re.sub(r'\[.*?\]', '', title)
            title = re.sub(r'\(.*?\)', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            # Truncate overly long title
            if len(title) > 50:
                title = title[:50] + "..."

        # Create notebook
        print(f"📚 Creating notebook: {title}")
        import subprocess
        import json

        cmd = f"notebooklm create '{title}' --json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        try:
            data = json.loads(result.stdout)
            notebook_id = data['notebook']['id']
            print(f"✅ Notebook created (ID: {notebook_id[:8]}...)")
        except:
            return {"success": False, "error": "Failed to parse notebook ID"}

        # Set context
        print(f"🎯 Setting notebook context...")
        cmd = f"notebooklm use {notebook_id}"
        subprocess.run(cmd, shell=True, capture_output=True)

        # Upload file
        print(f"📄 Uploading file...")
        cmd = f"notebooklm source add '{file_path}' --json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        try:
            data = json.loads(result.stdout)
            source_id = data['source']['id']
            print(f"✅ Upload successful (ID: {source_id[:8]}...)")

            return {
                "success": True,
                "notebook_id": notebook_id,
                "source_id": source_id,
                "title": title
            }
        except:
            return {"success": False, "error": "Failed to parse source ID"}


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Z-Library Full Auto-Download and Upload to NotebookLM")
        print("")
        print("Usage: python3 auto_download_and_upload.py <Z-Library URL>")
        sys.exit(1)

    url = sys.argv[1]
    uploader = ZLibraryAutoUploader()

    # Download
    downloaded_file, file_format = await uploader.download_from_zlibrary(url)

    if not downloaded_file or not downloaded_file.exists():
        print("")
        print("="*70)
        print("❌ Download failed, cannot continue")
        print("="*70)
        sys.exit(1)

    # Convert
    final_file = uploader.convert_to_txt(downloaded_file, file_format)

    # Upload
    result = uploader.upload_to_notebooklm(final_file)

    print("")
    print("="*70)
    if result['success']:
        print("🎉 Full workflow completed!")
        print("="*70)
        print(f"📚 Title: {result['title']}")
        print(f"🆔 Notebook ID: {result['notebook_id']}")

        # Handle chunked upload results
        if 'chunks' in result:
            print(f"📦 Chunks: {result['chunks']}")
            print(f"📄 Successfully uploaded {len(result['source_ids'])}/{result['chunks']} chunks")
            print("   Source IDs:")
            for sid in result['source_ids']:
                print(f"      - {sid}")
        else:
            print(f"📄 Source ID: {result['source_id']}")

        print("")
        print("💡 Next steps:")
        print(f"   notebooklm use {result['notebook_id']}")
        print(f"   notebooklm ask \"What are the core viewpoints of this book?\"")
    else:
        print("❌ Upload failed")
        print("="*70)
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
