
import sys

def safe_import_cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        print("OpenCV not available - image processing disabled")
        return None

def safe_import_tf():
    try:
        import tensorflow as tf
        return tf
    except ImportError:
        print("TensorFlow not available - ML model disabled")
        return None

def safe_import_easyocr():
    try:
        import easyocr
        return easyocr
    except ImportError:
        print("EasyOCR not available - OCR disabled")
        return None

# 기존 import 문들을 안전하게 래핑
cv2 = safe_import_cv2()
tf = safe_import_tf()
easyocr = safe_import_easyocr()
