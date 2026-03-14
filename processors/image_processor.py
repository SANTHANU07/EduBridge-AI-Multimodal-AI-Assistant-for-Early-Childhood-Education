import easyocr

class ImageProcessor:

    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        print("EasyOCR loaded")

    def extract_text(self, image_path):

        results = self.reader.readtext(image_path)

        text = ""

        for result in results:
            text += result[1] + " "

        return text