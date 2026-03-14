from pypdf import PdfReader

class DocProcessor:

    def read_pdf(self, file_path):

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            text += page.extract_text()

        return text