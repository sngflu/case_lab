import cv2
import torch
import numpy as np
from pathlib import Path
from doclayout_yolo import YOLOv10
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class_names = [
    'title', 'paragraph', 'table', 'picture', 
    'table_signature', 'picture_signature', 'numbered_list', 
    'marked_list', 'header', 'footer', 'footnote', 'formula'
]

# определяем цвета для каждого класса (RGB формат)
colors = {
    'title': (255, 0, 0),      # Красный
    'paragraph': (0, 255, 0),   # Зеленый
    'table': (0, 0, 255),      # Синий
    'picture': (255, 255, 0),   # Желтый
    'table_signature': (255, 0, 255),    # Пурпурный
    'picture_signature': (0, 255, 255),  # Голубой
    'numbered_list': (128, 0, 0),       # Темно-красный
    'marked_list': (0, 128, 0),         # Темно-зеленый
    'header': (0, 0, 128),              # Темно-синий
    'footer': (128, 128, 0),            # Оливковый
    'footnote': (128, 0, 128),          # Фиолетовый
    'formula': (0, 128, 128)            # Бирюзовый
}

def load_model(weights_path):
    """Загрузка модели"""
    model = YOLOv10(weights_path)
    model.to('cuda' if torch.cuda.is_available() else 'cpu')
    return model

def predict_and_visualize(model, image_path, output_path, conf_threshold=0.25):
    """Получение предсказаний и визуализация результатов"""
    # загрузка изображения
    image = cv2.imread(str(image_path))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # получение предсказаний
    results = model.predict(
        source=image_path,
        conf=conf_threshold,
        save=False,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # создаем копию изображения для рисования
    output_image = image.copy()
    
    # получаем размеры изображения
    height, width = image.shape[:2]
    
    # создаем фигуру matplotlib
    plt.figure(figsize=(20, 20))
    plt.imshow(image)
    
    # рисуем предсказания
    for result in results:
        boxes = result.boxes.cpu().numpy()
        for box in boxes:
            # получаем координаты
            x1, y1, x2, y2 = box.xyxy[0]
            conf = box.conf[0]
            cls_id = int(box.cls[0])
            
            # получаем метку класса и цвет
            class_name = class_names[cls_id]
            color = colors[class_name]
            
            # создаем прямоугольник
            rect = patches.Rectangle(
                (x1, y1), x2-x1, y2-y1,
                linewidth=2,
                edgecolor=tuple(c/255 for c in color),
                facecolor='none',
                alpha=0.7
            )
            plt.gca().add_patch(rect)
            
            # добавляем текст с меткой класса и уверенностью
            plt.text(
                x1, y1-5,
                f'{class_name} {conf:.2f}',
                color='white',
                bbox=dict(facecolor=tuple(c/255 for c in color), alpha=0.7),
                fontsize=8
            )
    
    # убираем оси
    plt.axis('off')
    
    # сохраняем результат
    plt.savefig(
        output_path,
        bbox_inches='tight',
        pad_inches=0,
        dpi=300
    )
    plt.close()
    
    print(f"Результат сохранен в {output_path}")
    return results

def main():
    # пути к файлам и директориям
    project_root = Path.cwd()
    weights_path = project_root / "runs/train/exp/weights/last.pt"
    test_images_dir = project_root / "test_images"
    output_dir = project_root / "predictions"
    
    # создаем директорию для выходных файлов
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # загружаем модель
    print("Загрузка модели...")
    model = load_model(weights_path)
    
    # получаем список тестовых изображений
    test_images = list(test_images_dir.glob("*.png"))
    if not test_images:
        test_images = list(test_images_dir.glob("*.jpg"))
    
    if not test_images:
        print("Тестовые изображения не найдены!")
        return
    
    print(f"Найдено {len(test_images)} тестовых изображений")
    
    # обрабатываем каждое изображение
    for image_path in test_images:
        print(f"\nОбработка {image_path.name}...")
        output_path = output_dir / f"pred_{image_path.stem}.png"
        
        try:
            results = predict_and_visualize(model, image_path, output_path)
            
            # выводим информацию о найденных объектах
            for result in results:
                boxes = result.boxes.cpu().numpy()
                print(f"\nНайдено {len(boxes)} объектов:")
                for box in boxes:
                    class_name = class_names[int(box.cls[0])]
                    conf = box.conf[0]
                    print(f"- {class_name}: {conf:.2f}")
                    
        except Exception as e:
            print(f"Ошибка при обработке {image_path.name}: {str(e)}")
            continue

if __name__ == "__main__":
    try:
        # очищаем память CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        main()
        print("\nОбработка завершена успешно!")
    except Exception as e:
        import traceback
        print(f"Произошла ошибка: {e}")
        print("Полный стек ошибки:")
        print(traceback.format_exc())