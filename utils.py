import os


def get_file_list_from_folder(folder):
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
