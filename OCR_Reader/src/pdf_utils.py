import fitz  # PyMuPDF
import numpy as np

def convert_pdf_to_images(pdf_path, zoom=2.0):
    """
    Convert a PDF file to a list of images (numpy arrays).
    
    :param pdf_path: Path to the PDF file.
    :param zoom: Zoom factor for higher resolution (default 2.0).
    :return: List of numpy arrays representing images.
    """
    images = []
    try:
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(zoom, zoom)  # Transformation matrix for higher resolution
        
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            # Convert to numpy array (H, W, 3)
            # fitz returns data as bytes, we need to reshape
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # If alpha channel exists (4 channels), drop it to get RGB
            if pix.n == 4:
                img_array = img_array[..., :3]
            
            images.append(img_array)
            
        doc.close()
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []
    
    return images
