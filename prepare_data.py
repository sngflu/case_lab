import os
import json
import shutil
from pathlib import Path
import cv2
import numpy as np

def convert_to_yolo_format(bbox, img_width, img_height):
    """Конвертация координат из абсолютных в относительные для YOLO"""
    x_center = (bbox[0] + bbox[2]) / 2 / img_width
    y_center = (bbox[1] + bbox[3]) / 2 / img_height
    width = (bbox[2] - bbox[0]) / img_width
    height = (bbox[3] - bbox[1]) / img_height
    return [x_center, y_center, width, height]

def prepare_dataset(raw_data_dir, output_dir):
    """Подготовка датасета"""
    raw_data_dir = Path(raw_data_dir)
    output_dir = Path(output_dir)
    
    print(f"Проверка директорий:")
    print(f"raw_data_dir: {raw_data_dir}")
    print(f"output_dir: {output_dir}")

    # проверяем существование директорий
    if not (raw_data_dir / "images").exists():
        raise ValueError(f"Директория с изображениями не найдена: {raw_data_dir / 'images'}")
    if not (raw_data_dir / "jsons").exists():
        raise ValueError(f"Директория с JSON файлами не найдена: {raw_data_dir / 'jsons'}")

    # создаем необходимые директории
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    # словарь для маппинга классов
    class_map = {
        "title": 0, "paragraph": 1, "table": 2, "picture": 3,
        "table_signature": 4, "picture_signature": 5, "numbered_list": 6,
        "marked_list": 7, "header": 8, "footer": 9, "footnote": 10,
        "formula": 11
    }

    # собираем пары файлов
    valid_pairs = []
    image_files = list(Path(raw_data_dir / "images").glob("*.png"))
    print(f"\nНайдено {len(image_files)} PNG файлов")

    for img_path in image_files:
        json_path = raw_data_dir / "jsons" / f"{img_path.stem}.json"
        print(f"\nОбработка файла: {img_path.name}")
        print(f"Поиск JSON: {json_path}")
        
        if not json_path.exists():
            print(f"Пропускаем {img_path.name}: нет соответствующего JSON файла")
            continue

        try:
            # проверяем, что изображение читается
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"Пропускаем {img_path.name}: невозможно прочитать изображение")
                continue

            # копируем изображение
            new_img_path = images_dir / img_path.name
            shutil.copy(str(img_path), str(new_img_path))
            print(f"Изображение скопировано в {new_img_path}")

            # читаем JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # создаем YOLO-формат аннотаций
            label_content = []
            img_width = data['image_width']
            img_height = data['image_height']

            for class_name, boxes in data.items():
                if class_name in class_map and isinstance(boxes, list) and boxes:
                    class_id = class_map[class_name]
                    for bbox in boxes:
                        yolo_bbox = convert_to_yolo_format(bbox, img_width, img_height)
                        label_content.append(f"{class_id} {' '.join(map(str, yolo_bbox))}")

            # сохраняем файл с аннотациями
            label_file = labels_dir / f"{img_path.stem}.txt"
            with open(label_file, 'w') as f:
                f.write('\n'.join(label_content))
            print(f"Создан файл аннотаций: {label_file}")

            valid_pairs.append(img_path.stem)
            print(f"Пара успешно обработана")
            
        except Exception as e:
            print(f"Ошибка при обработке {img_path.name}: {str(e)}")
            continue

    print(f"\nИтоги обработки:")
    print(f"Всего найдено изображений: {len(image_files)}")
    print(f"Успешно обработано пар: {len(valid_pairs)}")

    if not valid_pairs:
        raise ValueError("Не найдено валидных пар изображение-разметка!")

    # создаем train/val split (80/20)
    np.random.shuffle(valid_pairs)
    split_idx = int(len(valid_pairs) * 0.8)
    train_pairs = valid_pairs[:split_idx]
    val_pairs = valid_pairs[split_idx:]

    # сохраняем списки train/val с полными путями
    with open(output_dir / "train.txt", 'w') as f:
        f.write('\n'.join(str(images_dir / f"{name}.png") for name in train_pairs))
    
    with open(output_dir / "val.txt", 'w') as f:
        f.write('\n'.join(str(images_dir / f"{name}.png") for name in val_pairs))

    print(f"\nСоздание файлов со списками:")
    print(f"train.txt: {len(train_pairs)} образцов")
    print(f"val.txt: {len(val_pairs)} образцов")
    
    return len(valid_pairs)

def main():
    # определяем пути
    project_root = Path.cwd()
    raw_data_dir = project_root / "raw_data"
    output_dir = project_root / "datasets/prepared_data"

    # подготовка данных
    print("Подготовка данных...")
    num_samples = prepare_dataset(raw_data_dir, output_dir)

    # создаем конфигурационный файл
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)
    
    config_content = f"""
path: {str(output_dir)}
train: {str(output_dir / 'train.txt')}
val: {str(output_dir / 'val.txt')}

nc: 12
names: ['title', 'paragraph', 'table', 'picture', 'table_signature', 'picture_signature', 
        'numbered_list', 'marked_list', 'header', 'footer', 'footnote', 'formula']
"""
    
    config_path = config_dir / "doclayout.yaml"
    with open(config_path, 'w') as f:
        f.write(config_content)

if __name__ == "__main__":
    main()
