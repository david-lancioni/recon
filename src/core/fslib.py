import os

class FsLib:

    def join(self, path1, path2):
        path = os.path.join(path1, path2) if path2.strip() != "" else path1
        return path    
    
    def is_dir(self, path):
        if not os.path.isdir(path):
            return False
        else:
            return True
