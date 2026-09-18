import urllib.request
import json
import io
from PIL import Image, ImageDraw

# 1. Create a test Image with WBC & PLT
img = Image.new('RGB', (800, 300), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((30, 30), 'KET QUA XET NGHIEM HUYET HOC', fill=(0, 0, 0))
d.text((30, 70), 'WBC: 14.2 10^9/L', fill=(0, 0, 0))
d.text((30, 110), 'PLT: 75 10^9/L', fill=(0, 0, 0))
img_buf = io.BytesIO()
img.save(img_buf, format='PNG')
img_bytes = img_buf.getvalue()

# 2. PDF text bytes
pdf_raw_content = b'%PDF-1.4 KET QUA SINH HOA: GLUCOSE: 9.8 mmol/L, AST: 65 U/L, ALT: 58 U/L'

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = io.BytesIO()

# Add image file
body.write(f'--{boundary}\r\n'.encode('utf-8'))
body.write(b'Content-Disposition: form-data; name="files"; filename="xet_nghiem_mau.png"\r\n')
body.write(b'Content-Type: image/png\r\n\r\n')
body.write(img_bytes)
body.write(b'\r\n')

# Add PDF file
body.write(f'--{boundary}\r\n'.encode('utf-8'))
body.write(b'Content-Disposition: form-data; name="files"; filename="sinh_hoa.pdf"\r\n')
body.write(b'Content-Type: application/pdf\r\n\r\n')
body.write(pdf_raw_content)
body.write(b'\r\n')

body.write(f'--{boundary}--\r\n'.encode('utf-8'))
data = body.getvalue()

req = urllib.request.Request(
    'http://localhost:8000/api/v1/medical/ocr',
    data=data,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

try:
    res = urllib.request.urlopen(req)
    out = json.loads(res.read().decode('utf-8'))
    print('=== MULTI-FILE OCR SUCCESS ===')
    print('Total indicators found:', out.get('total_indicators_found'))
    print('Parsed indicators:', json.dumps(out.get('parsed_indicators'), ensure_ascii=False, indent=2))
    print('Critical flags:', out.get('critical_flags'))
except Exception as e:
    print('OCR Test Error:', e)
