import cv2
import numpy as np
import os
try:
    from OCR_Reader.src.pdf_utils import convert_pdf_to_images
    from OCR_Reader.src.docx_utils import process_docx
except ImportError:
    # Fallback for relative imports or direct execution
    try:
        from .pdf_utils import convert_pdf_to_images
        from .docx_utils import process_docx
    except ImportError:
        from pdf_utils import convert_pdf_to_images
        from docx_utils import process_docx

class OCREngine:
    def __init__(self, languages=['en'], gpu=True):
        """
        Initialize the OCR engine.
        :param languages: List of supported languages (default: English and Arabic)
        :param gpu: Use GPU for acceleration
        """
        # Lazy import easyocr to avoid crash on import if DLLs are missing
        import easyocr

        # Define model storage path to be within the project directory in O drive
        model_dir = os.path.join(os.getcwd(), 'models_cache')
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        print(f"Loading OCR model for languages: {languages} (GPU={gpu})...")
        print(f"Models will be stored in: {model_dir}")
        
        self.reader = easyocr.Reader(languages, gpu=gpu, model_storage_directory=model_dir, download_enabled=True)

    def read_image(self, image_path, detail=1):
        """
        Read text from an image or PDF file.
        :param image_path: Path to the image or PDF
        :param detail: Detail level (1 for boxes and text, 0 for text only)
        :return: Reading results
        """
        if image_path.lower().endswith('.pdf'):
            print(f"Detected PDF: {image_path}. Converting to images...")
            images = convert_pdf_to_images(image_path)
            all_results = []
            for i, img in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                results = self.reader.readtext(img, detail=detail)
                all_results.extend(results)
            return all_results
            
        elif image_path.lower().endswith('.docx'):
            print(f"Detected DOCX: {image_path}. extracting text and images...")
            return process_docx(image_path, self, detail=detail)

        # Robust Image Loading for Windows paths
        try:
            # Try reading as byte stream first to handle non-standard paths
            if os.path.exists(image_path):
                 import numpy as np
                 stream = np.fromfile(image_path, dtype=np.uint8)
                 img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
                 if img is not None:
                     return self.reader.readtext(img, detail=detail)
        except Exception as e:
            print(f"Warning: Robust image read failed ({e}), falling back to direct path...")

        return self.reader.readtext(image_path, detail=detail)

    def read_image_from_array(self, image_array, detail=1):
        """
        Read text from an image array (NumPy array).
        Useful when cropping images or processing before reading.
        """
        return self.reader.readtext(image_array, detail=detail)
