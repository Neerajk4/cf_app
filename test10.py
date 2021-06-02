
import os
import glob
dir_path = 'shape/extracted_files'
##files = glob.glob('shape/extracted_files')
files = glob.glob(os.path.join(dir_path, "*"))
for f in files:
    os.remove(f)
    print(f)

os.rmdir(dir_path)

print("sucessful")