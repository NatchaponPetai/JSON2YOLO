import json
import shutil
from pathlib import Path

import requests
import yaml
from PIL import Image


def make_dirs(dir='new_dir/'):
    # Create folders
    dir = Path(dir)
    if dir.exists():
        shutil.rmtree(dir)  # delete dir
    for p in dir, dir / 'labels', dir / 'images':
        p.mkdir(parents=True, exist_ok=True)  # make dir
    return dir


def convert(file):
    # Convert Labelbox JSON labels to YOLO labels
    names = []  # class names
    save_dir = make_dirs(Path(file).stem)
    with open(file) as f:
        data = json.load(f)  # load JSON

    for img in data:
        img_path = img['Labeled Data']
        im = Image.open(requests.get(img_path, stream=True).raw if img_path.startswith('http') else img_path)  # open
        width, height = im.size  # image size
        label_path = save_dir / 'labels' / Path(img_path[:img_path.index('?')]).with_suffix('.txt').name
        image_path = save_dir / 'images' / Path(img_path[:img_path.index('?')]).name
        im.save(image_path, quality=95, subsampling=0)

        for label in img['Label']['objects']:
            # box
            top, left, h, w = label['bbox'].values()  # top, left, height, width
            xywh = [(left + w / 2) / width, (top + h / 2) / height, w / width, h / height]  # xywh normalized

            # class
            cls = label['value']  # class name
            if cls not in names:
                names.append(cls)

            line = names.index(cls), *xywh  # YOLO format (class_index, xywh)
            with open(label_path, 'a') as f:
                f.write(('%g ' * len(line)).rstrip() % line + '\n')

    # Save dataset.yaml
    d = {'train': 'path/to/train_imgs', 'val': 'path/to/val_imgs', 'nc': len(names), 'names': names}  # dictionary
    with open(save_dir / Path(file).with_suffix('.yaml').name, 'w') as f:
        yaml.dump(d, f, sort_keys=False)

    # Zip
    # os.system(f'zip -r ../{save_dir}.zip {save_dir}')  # zip results


if __name__ == '__main__':
    convert('./export-2021-02-03T02_11_34.601Z.json')
