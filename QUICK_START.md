# AutoDecodeX - Quick Start Guide

Welcome to AutoDecodeX! This guide will get you up and running in 5 minutes.

---

## ⚡ Installation (2 minutes)

### Step 1: Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

Required packages:
- FastAPI
- uvicorn
- Pillow
- NumPy
- pydantic

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

---

## 🚀 Start the Application (1 minute)

### Terminal 1: Start Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2: Start Frontend
```bash
cd frontend
npm run dev
```

You should see:
```
  ▲ Next.js 14.2.3
  - Local:        http://localhost:3000
```

### Access the Application
Open your browser and navigate to: **http://localhost:3000**

---

## 🎯 Your First Decode (2 minutes)

### Test 1: Simple Base64 Decode
1. **Open the app** at http://localhost:3000
2. You'll land on the **Decoder** workspace
3. **Paste this** into the input box:
   ```
   SGVsbG8gV29ybGQh
   ```
4. **Watch the magic:**
   - Detection automatically runs
   - Confidence scores appear
   - Output shows: `Hello World!`
   - Live feed shows analysis logs

✅ **Success!** You just decoded Base64.

---

### Test 2: Multi-Layer Decoding
1. **Clear the input** (click Reset)
2. **Paste this:**
   ```
   NDg2NTZjNmM2ZjIwNTc2ZjcyNmM2NA==
   ```
3. **Observe:**
   - Step 1: Detects Base64
   - Step 2: Decodes to Hex
   - Step 3: Decodes to `Hello World`
   - Path shows: BASE64 → HEX → Plaintext

✅ **Success!** You decoded a 2-layer encoding.

---

### Test 3: CTF Flag Detection
1. **Clear the input**
2. **Paste this:**
   ```
   ZmxhZ3t0ZXN0X2ZsYWd9
   ```
3. **Look for:**
   - 🚩 **FLAG** indicator appears
   - Output: `flag{test_flag}`
   - Green pulsing highlight
   - Inspector shows "is_ctf_flag: true"

✅ **Success!** You found a CTF flag.

---

## 🖼️ Your First Stego Analysis

### Test 4: Upload and Analyze an Image
1. **Click "Stego Analyzer"** in the left sidebar
2. **Select the "Full Scan" tab** (should be default)
3. **Get a test image:**
   - Use any PNG or JPEG from your computer
   - Or download a test image online
4. **Upload the image:**
   - Drag and drop onto the upload zone
   - OR click "Select File"
5. **Click "Full Scan"**
6. **Watch the analysis:**
   - Logs appear in real-time
   - Metadata extraction runs
   - LSB analysis completes
   - Entropy analysis shows
   - Results display

✅ **Success!** You performed a complete stego analysis.

---

## 📝 More Examples

### Example 5: Hex Decoding
**Input:** `48656c6c6f20576f726c64`  
**Output:** `Hello World`

### Example 6: ROT13
**Input:** `Uryyb Jbeyq`  
**Output:** `Hello World`

### Example 7: Binary
**Input:** `01001000 01100101 01101100 01101100 01101111`  
**Output:** `Hello`

### Example 8: Morse Code
**Input:** `.... . .-.. .-.. ---`  
**Output:** `HELLO`

### Example 9: URL Encoding
**Input:** `Hello%20World%21`  
**Output:** `Hello World!`

---

## 🎨 UI Overview

### Left Sidebar (Navigation)
- **Decoder** - Text encoding/decoding
- **Stego Analyzer** - Image analysis
- **Metadata Explorer** - Coming soon
- **File Analyzer** - Coming soon
- **Settings** - Coming soon

### Main Workspace
- Input area
- Control buttons
- Results display
- Interactive visualizations

### Right Inspector Panel
- Real-time detection confidence
- File information
- Risk assessment
- Suspicious indicators

### Bottom Analysis Feed
- Live logs
- Color-coded messages
- Timestamps
- Auto-scroll

---

## 🔧 Troubleshooting

### Backend Won't Start
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install --upgrade -r backend/requirements.txt

# Try different port
uvicorn backend.main:app --reload --port 8080
```

### Frontend Won't Start
```bash
# Clear node modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try different port
PORT=3001 npm run dev
```

### Can't Connect to Backend
1. Check backend is running on http://127.0.0.1:8000
2. Visit http://127.0.0.1:8000/docs to see API docs
3. Check browser console for errors
4. Verify CORS settings in `backend/main.py`

### Image Upload Fails
- Check file size (max 10MB)
- Verify format (PNG, JPEG, BMP, WebP only)
- Check browser console for errors
- Try a smaller image

---

## 🎓 Learning Path

### Beginner (Day 1)
1. ✅ Run Quick Start tests 1-4
2. Try all example encodings
3. Upload different images
4. Explore the UI

### Intermediate (Week 1)
5. Create your own encoded messages
6. Test with real CTF challenges
7. Try password-protected LSB extraction
8. Experiment with bit depths and channels

### Advanced (Month 1)
9. Use the CLI tool
10. Test API endpoints directly
11. Create custom encoded images
12. Analyze complex multi-layer encodings

---

## 📚 Next Steps

### Documentation
- Read **README.md** for complete feature list
- Check **PROJECT_STATUS.md** for implementation details
- Review **TESTING_GUIDE.md** for comprehensive testing

### API Documentation
Visit http://127.0.0.1:8000/docs for interactive Swagger docs

### CLI Usage
```bash
# Basic decode
python autodecodex.py "SGVsbG8gV29ybGQh"

# CTF mode
python autodecodex.py "ZmxhZ3t0ZXN0fQ==" --ctf

# Brute force Caesar
python autodecodex.py "Uryyb Jbeyq" --brute-force caesar

# Brute force XOR
python autodecodex.py "1b1b1b" --brute-force xor

# Detection only
python autodecodex.py "48656c6c6f" --detect-only
```

---

## 🎯 Tips & Tricks

### For CTF Players
- Use **CTF mode** for optimized flag detection
- Check **metadata first** - flags often hidden there
- Try **Full Scan** on images to catch everything
- **LSB depth 1** is most common for basic stego
- Look for **high entropy** regions

### For Best Results
- Start with **auto-detection** before manual selection
- Use **Full Scan** for comprehensive analysis
- Check **bit plane 0** first (LSB most likely)
- Enable **Auto-Decode** for extracted data
- Copy results immediately to clipboard

### Keyboard Shortcuts
- Coming soon!

---

## ⚡ Power User Features

### Stego Analyzer Tabs
1. **Full Scan** - Complete unified analysis
2. **Metadata** - EXIF/metadata only
3. **LSB / Stego** - LSB extraction + bit planes
4. **Text Stego** - Zero-width characters, whitespace

### LSB Options
- **Bit Depth:** 1-8 bits per channel
- **Channels:** R, G, B, or RGB combined
- **Password:** Optional extraction offset
- **Auto-Decode:** Automatically decode extracted data

### Metadata Features
- Automatic encoding detection
- Auto-decode suspicious fields
- Embedded file detection
- GPS data extraction
- PNG text chunk parsing

---

## 🆘 Getting Help

### In-App Help
- Hover over controls for tooltips
- Check Live Analysis Feed for hints
- Inspector Panel shows detection confidence

### Documentation
- All `.md` files in repository root
- API docs at http://127.0.0.1:8000/docs

### Common Issues
- **"Input cannot be empty"** - Paste some text first
- **"File too large"** - Max 10MB, try smaller image
- **"Unsupported format"** - Use PNG, JPEG, BMP, or WebP
- **Low confidence scores** - Input might not be encoded

---

## 🎉 You're Ready!

You've successfully:
- ✅ Installed AutoDecodeX
- ✅ Decoded your first message
- ✅ Analyzed an image
- ✅ Explored the UI

**Now try:**
- Real CTF challenges
- Your own encoded messages
- Different image formats
- Multi-layer encodings

---

## 🚀 Ready for Production?

See **FINAL_DELIVERY.md** for:
- Production deployment instructions
- Security considerations
- Performance optimization
- Scaling recommendations

---

**Happy Decoding! 🔓**

---

*Need more help? Check the documentation or create an issue in the repository.*
