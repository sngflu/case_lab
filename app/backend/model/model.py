import torch
from PIL import Image, ImageDraw
from doclayout_yolo import YOLOv10

CLASS_NAMES = [
    'title', 'paragraph', 'table', 'picture',
    'table_signature', 'picture_signature', 'numbered_list',
    'marked_list', 'header', 'footer', 'footnote', 'formula'
]

COLORS = {
    'title': (255, 0, 0), 'paragraph': (0, 255, 0), 'table': (0, 0, 255),
    'picture': (255, 255, 0), 'table_signature': (255, 0, 255),
    'picture_signature': (0, 255, 255), 'numbered_list': (128, 0, 0),
    'marked_list': (0, 128, 0), 'header': (0, 0, 128), 'footer': (128, 128, 0),
    'footnote': (128, 0, 128), 'formula': (0, 128, 128)
}

class YOLOModel:
    def __init__(self, weights_path: str):
        """
        Инициализация и загрузка модели YOLO.

        Args:
            weights_path (str): Путь к весам модели.
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLOv10(weights_path).to(self.device)

    def predict(self, image_path: str, conf_threshold: float = 0.75) -> list:
        """
        Делает предсказание для одного изображения.

        Args:
            image_path (str): Путь к изображению.
            conf_threshold (float): Порог уверенности для предсказаний.

        Returns:
            list: Результаты предсказаний.
        """
        results = self.model.predict(
            source=image_path,
            conf=conf_threshold,
            save=False,
            device=self.device
        )
        return results

    def annotate_image(self, image_path: str, results: list, output_path: str):
        """
        Аннотирует изображение на основе предсказаний и сохраняет результат.

        Args:
            image_path (str): Путь к исходному изображению.
            results (list): Результаты предсказаний.
            output_path (str): Путь для сохранения аннотированного изображения.
        """
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        for result in results:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                cls_id = int(box.cls[0])
                class_name = CLASS_NAMES[cls_id]
                color = COLORS[class_name]

                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

                draw.text((x1, y1 - 10), class_name, fill=color)

        image.save(output_path)

def load_model(weights_path: str) -> YOLOModel:
    """
    Фабрика для создания экземпляра YOLOModel.

    Args:
        weights_path (str): Путь к весам модели.

    Returns:
        YOLOModel: Экземпляр модели YOLO.
    """
    return YOLOModel(weights_path)
