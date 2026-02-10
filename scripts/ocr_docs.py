from PIL import Image
import pytesseract
import glob
import os

os.makedirs('tmp_ocr_outputs', exist_ok=True)

pngs = sorted(glob.glob('docs/*.png'))
for p in pngs:
    try:
        txt = pytesseract.image_to_string(Image.open(p), lang='eng')
    except Exception as e:
        txt = f'ERROR OCR: {e}'
    out = os.path.join('tmp_ocr_outputs', os.path.basename(p) + '.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(txt)
    print('WROTE', out)

# Concatenate outputs for easier parsing
with open('tmp_ocr_outputs/combined_ocr.txt', 'w', encoding='utf-8') as fout:
    for fn in sorted(glob.glob('tmp_ocr_outputs/*.txt')):
        with open(fn, 'r', encoding='utf-8', errors='ignore') as fin:
            fout.write('\n----- ' + fn + ' -----\n')
            fout.write(fin.read())
print('COMBINED -> tmp_ocr_outputs/combined_ocr.txt')
