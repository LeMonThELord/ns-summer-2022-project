_DEBUG = False

def log(message):
    print(message) if _DEBUG else 0

def ensure_dir(path):
    import os
    exists = os.path.exists(path)
    if not exists:
        os.makedirs(path)
        print(path + ' created')
        return True
    else:
        print(path + ' exists')
        return False