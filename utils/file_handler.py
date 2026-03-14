import os


class FileHandler:
    def save_file(self, uploaded_file, path):
        folder = os.path.dirname(path)

        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return os.path.abspath(path)