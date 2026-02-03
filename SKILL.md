---
name: zlibrary-to-notebooklm
description: Automatically download books from Z-Library and upload to Google NotebookLM. Supports PDF/EPUB formats, automatic conversion, one-click knowledge base creation.
---

# Z-Library to NotebookLM Skill

Let Claude help you automatically download books and upload to NotebookLM, enabling "zero-hallucination" AI conversational reading.

## 🎯 Core Features

- One-click book download (prioritizes PDF, auto-fallback to EPUB)
- Automatically create NotebookLM notebooks
- Upload files and return notebook ID
- Support AI conversations based on book content

## 📋 Activation Triggers

Use this Skill when the user mentions the following needs:

- User provides Z-Library book link (containing domains like `zlib.li`, `z-lib.org`, `zh.zlib.li`, etc.)
- User says "help me upload this book to NotebookLM"
- User says "automatically download and read this book"
- User says "use Z-Library link to create NotebookLM knowledge base"
- User requests to download books from a specific URL and analyze

## 🔧 Core Commands

When user provides a Z-Library link, execute the following workflow:

### Step 1: Extract Information

Extract from the user-provided URL:
- Book title
- Author (if available)
- Full URL
- Format options (PDF/EPUB/MOBI, etc.)

### Step 2: Automatic Download

Use saved session (`~/.zlibrary/storage_state.json`) to automatically login to Z-Library:

1. **Priority download PDF** (preserves formatting, better AI analysis)
2. **Auto fallback**: If no PDF available, download EPUB
3. **Format conversion**: If EPUB downloaded, use ebooklib to convert to plain text

### Step 3: Create NotebookLM Notebook

```bash
notebooklm create "Book Title"
```

### Step 4: Upload File

```bash
notebooklm source add "file path"
```

### Step 5: Return Results

Return to user:
- ✅ Download success confirmation
- 📚 Notebook ID
- 💡 Suggested follow-up question examples

### Step 6: Error Handling

If errors occur:
- Retry up to 3 times
- If login fails, prompt user to run `python3 ~/.claude/skills/zlibrary-to-notebooklm/scripts/login.py`
- If download fails, provide troubleshooting suggestions

## ⚠️ Important Limitations

**Legal Resources Only!**

- ✅ Resources the user has legal access to
- ✅ Public domain or open-source licensed documents
- ✅ Content personally owned or authorized

## 🛠️ Dependency Tools

### Required Tools

1. **Playwright** - Browser automation
   - For automatic login and download
   - Need to pre-run `playwright install chromium`

2. **ebooklib** - EPUB processing
   - For converting EPUB to plain text

3. **NotebookLM CLI** - Upload tool
   - `notebooklm create` - Create notebook
   - `notebooklm source add` - Upload file

### Configuration Files

- `~/.zlibrary/storage_state.json` - Saved login session
- `~/.zlibrary/browser_profile/` - Browser data

## 📝 Usage Examples

### User Request

```
Help me upload this book to NotebookLM:
https://zh.zlib.li/book/25314781/aa05a1/钱的第四维
```

### Execution Flow

1. **Confirm and extract information**
   ```
   Title: 钱的第四维
   URL: https://zh.zlib.li/book/25314781/aa05a1/钱的第四维
   ```

2. **Execute download script**
   ```bash
   cd ~/.claude/skills/zlibrary-to-notebooklm
   python3 scripts/upload.py "https://zh.zlib.li/book/25314781/aa05a1/钱的第四维"
   ```

3. **Return results**
   ```
   ✅ Download successful!
   📚 Notebook ID: 22916611-c68c-4065-a657-99339e126fb4

   Now you can ask me:
   - "What are the core viewpoints of this book?"
   - "Summarize Chapter 3 content"
   - "What unique insights does the author have?"
   ```

## 🔄 Alternative Flows

### If User Only Provides Book Title

```
User: "Help me download the book 'Cognitive Awakening'"
```

**Actions:**
1. Ask: "Do you have the Z-Library link?"
2. If has link, execute standard flow
3. If no link, prompt: "Please provide Z-Library book page link, I can help you automatically download and upload to NotebookLM"

### If User Provides Other Sources

```
User: "Can this PDF be uploaded to NotebookLM? [local file path]"
```

**Actions:**
1. Inform user: "This Skill is mainly for Z-Library links"
2. Suggest: "For local files, you can directly use notebooklm source add command to upload"

## 📊 Technical Details

### Download Priority

1. **PDF** - Preserves formatting, best AI analysis
2. **EPUB** - Convert to plain text (using ebooklib)
3. **Other formats** - Try conversion or prompt user

### Session Management

- **One-time login, permanent use**
- Session saved in `~/.zlibrary/storage_state.json`
- If session expires, prompt user to re-login

### Error Retry

- Download failure: Auto-retry 3 times
- Login failure: Prompt user for manual login
- Upload failure: Check file size and format

## 💡 Best Practices

### First Time Use

Before first use, ensure user has completed login:

```bash
cd ~/.claude/skills/zlibrary-to-notebooklm
python3 scripts/login.py
```

### Batch Processing

If user has multiple links:

```
User: "Help me download these 3 books: [link1] [link2] [link3]"
```

**Actions:**
1. Process one by one (one link at a time)
2. After each completion, process next
3. Avoid concurrency causing session conflicts

### Content Analysis

After upload completion, proactively suggest:

```
✅ Book uploaded! You can:

• Start reading immediately: "What are the core viewpoints of this book?"
• Deep dive: "Explain the case in Chapter 5"
• Generate notes: "Create detailed reading notes"
• Comparative analysis: "How does this differ from the viewpoints in the book?"
```

## 🚨 Troubleshooting

### Common Issues

**Q: Prompt "Login session not found"**
A: Need to first run `python3 scripts/login.py` to login once

**Q: Download failure, timeout**
A: May be network issue, suggest retry or check network connection

**Q: Cannot find download button**
A: Z-Library page structure may have changed, use backup plan for manual download

**Q: NotebookLM upload failure**
A: Check file size (NotebookLM has upload limits)

### Detailed Help

See `docs/TROUBLESHOOTING.md` for complete troubleshooting guide.

## 📚 Related Resources

- [NotebookLM Official Documentation](https://notebooklm.google.com/)
- [Z-Library Website](https://zh.zlib.li/)
- [Playwright Documentation](https://playwright.dev/)
- [Project GitHub](https://github.com/zstmfhy/zlibrary-to-notebooklm)

## 🎓 Learning Resources

If you want to learn more:

- **How to efficiently use NotebookLM**: Ask "What are NotebookLM usage tips?"
- **How to create personal knowledge base**: Ask "How to build a knowledge management system with NotebookLM?"
- **AI conversational reading**: Ask "How to have AI help me deeply read a book?"

---

**Skill Version:** 1.0.0
**Last Updated:** 2025-01-14
**Author:** zstmfhy
