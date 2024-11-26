import torch
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
import wandb
from ultralytics.utils.metrics import ConfusionMatrix
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from ultralytics import YOLO

class_names = [
    'title', 'paragraph', 'table', 'picture', 
    'table_signature', 'picture_signature', 'numbered_list', 
    'marked_list', 'header', 'footer', 'footnote', 'formula'
]

def load_model(weights_path):
    """Загрузка модели"""
    model = YOLO(weights_path)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    return model, device

def load_ground_truth(json_path):
    """Загрузка ground truth разметки из JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    boxes = []
    labels = []
    
    for class_idx, class_name in enumerate(class_names):
        for box in data[class_name]:
            boxes.append(box)
            labels.append(class_idx)
    
    return np.array(boxes), np.array(labels)

def calculate_iou(box1, box2):
    """Вычисление IoU между двумя боксами"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / (union + 1e-6)

def evaluate_predictions(pred_boxes, pred_classes, pred_scores, gt_boxes, gt_classes, iou_threshold=0.5):
    """Оценка предсказаний для одного изображения"""
    matches = []
    num_pred = len(pred_boxes)
    num_gt = len(gt_boxes)
    
    # матрица IoU между всеми парами боксов
    iou_matrix = np.zeros((num_pred, num_gt))
    for i in range(num_pred):
        for j in range(num_gt):
            iou_matrix[i, j] = calculate_iou(pred_boxes[i], gt_boxes[j])
    
    # для каждого predicted box находим лучший matching ground truth box
    matched_gt_boxes = set()
    for pred_idx in range(num_pred):
        max_iou = iou_threshold
        match_gt_idx = -1
        
        for gt_idx in range(num_gt):
            if gt_idx in matched_gt_boxes:
                continue
                
            iou = iou_matrix[pred_idx, gt_idx]
            if (iou > max_iou) and (pred_classes[pred_idx] == gt_classes[gt_idx]):
                max_iou = iou
                match_gt_idx = gt_idx
        
        if match_gt_idx > -1:
            matched_gt_boxes.add(match_gt_idx)
            matches.append({
                'pred_idx': pred_idx,
                'gt_idx': match_gt_idx,
                'iou': max_iou,
                'confidence': pred_scores[pred_idx],
                'class_id': pred_classes[pred_idx]
            })
    
    return matches, num_pred, num_gt

def plot_confusion_matrix(confusion_matrix, class_names):
    """Построение confusion matrix"""
    plt.figure(figsize=(12, 10))
    
    # нормализация матрицы
    confusion_norm = confusion_matrix / confusion_matrix.sum(axis=1, keepdims=True)
    
    # создаем два subplot-а: для абсолютных значений и процентов
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    # абсолютные значения
    sns.heatmap(confusion_matrix, 
                annot=True, 
                fmt='.0f',
                cmap='Blues',
                xticklabels=class_names, 
                yticklabels=class_names,
                ax=ax1)
    ax1.set_title('Absolute Values')
    ax1.set_ylabel('True Label')
    ax1.set_xlabel('Predicted Label')
    
    # проценты
    sns.heatmap(confusion_norm, 
                annot=True, 
                fmt='.1%',
                cmap='Blues',
                xticklabels=class_names, 
                yticklabels=class_names,
                ax=ax2)
    ax2.set_title('Normalized Values')
    ax2.set_ylabel('True Label')
    ax2.set_xlabel('Predicted Label')
    
    plt.tight_layout()
    return plt.gcf()

def main():
    # инициализация wandb
    wandb.init(project="doclayout-evaluation", name="evaluation-run")
    
    # пути к файлам и директориям
    project_root = Path.cwd()
    weights_path = project_root / "runs/train/experiment2_yolov8/weights/best.pt"
    test_dataset_dir = project_root / "test_dataset"
    images_dir = test_dataset_dir / "image"
    json_dir = test_dataset_dir / "json"
    
    # загружаем модель
    print("Загрузка модели...")
    model, device = load_model(weights_path)
    
    # инициализация метрик
    conf_matrix = ConfusionMatrix(nc=len(class_names))
    class_metrics = defaultdict(lambda: {'TP': 0, 'FP': 0, 'FN': 0, 'total_iou': 0})
    all_matches = []
    
    # получаем список изображений
    test_images = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    
    print(f"Найдено {len(test_images)} тестовых изображений")
    
    # обработка изображений
    for image_path in tqdm(test_images, desc="Оценка модели"):
        # получаем ground truth
        json_path = json_dir / f"{image_path.stem}.json"
        gt_boxes, gt_classes = load_ground_truth(json_path)
        
        # получаем предсказания
        results = model.predict(
            source=str(image_path),
            conf=0.25,
            save=False,
            device=device
        )
        
        if len(results) > 0:
            pred_boxes = results[0].boxes.xyxy.cpu().numpy()
            pred_classes = results[0].boxes.cls.cpu().numpy().astype(int)
            pred_scores = results[0].boxes.conf.cpu().numpy()
            
            # оценка предсказаний
            matches, num_pred, num_gt = evaluate_predictions(
                pred_boxes, pred_classes, pred_scores,
                gt_boxes, gt_classes
            )
            
            # обновление метрик
            for match in matches:
                class_id = match['class_id']
                class_metrics[class_id]['TP'] += 1
                class_metrics[class_id]['total_iou'] += match['iou']
            
            # подсчет FP и FN
            for class_id in range(len(class_names)):
                pred_count = np.sum(pred_classes == class_id)
                gt_count = np.sum(gt_classes == class_id)
                tp_count = sum(1 for m in matches if m['class_id'] == class_id)
                
                class_metrics[class_id]['FP'] += pred_count - tp_count
                class_metrics[class_id]['FN'] += gt_count - tp_count
            
            all_matches.extend(matches)
            
            # обновление confusion matrix
            device = next(model.parameters()).device
            conf_matrix.process_batch(
                torch.cat((results[0].boxes.xyxy, 
                        results[0].boxes.conf.unsqueeze(1), 
                        results[0].boxes.cls.unsqueeze(1)), 1),
                torch.from_numpy(gt_boxes).float().to(device),
                torch.from_numpy(gt_classes).long().to(device)
            )
    
    # вычисление метрик для каждого класса
    class_results = {}
    overall_metrics = {
        'precision': 0,  # при IoU > 0.5
        'recall': 0, # при IoU > 0.5
        'f1': 0, # при IoU > 0.5
        'mean_iou': 0
    }
    
    for class_id in range(len(class_names)):
        metrics = class_metrics[class_id]
        tp = metrics['TP']
        fp = metrics['FP']
        fn = metrics['FN']
        
        precision = tp / (tp + fp + 1e-6)
        recall = tp / (tp + fn + 1e-6)
        f1 = 2 * precision * recall / (precision + recall + 1e-6)
        mean_iou = metrics['total_iou'] / (tp + 1e-6) if tp > 0 else 0
        
        class_results[class_names[class_id]] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'mean_iou': mean_iou
        }
        
        overall_metrics['precision'] += precision
        overall_metrics['recall'] += recall
        overall_metrics['f1'] += f1
        overall_metrics['mean_iou'] += mean_iou
    
    # усреднение общих метрик
    for key in overall_metrics:
        overall_metrics[key] /= len(class_names)
    
    # построение confusion matrix
    conf_matrix_fig = plot_confusion_matrix(conf_matrix.matrix, class_names)
    
    # логирование в wandb
    wandb.log({
        'overall_precision': overall_metrics['precision'],
        'overall_recall': overall_metrics['recall'],
        'overall_f1': overall_metrics['f1'],
        'overall_mean_iou': overall_metrics['mean_iou'],
        'confusion_matrix': wandb.Image(conf_matrix_fig),
        **{f"{class_name}_precision": metrics['precision']
           for class_name, metrics in class_results.items()},
        **{f"{class_name}_recall": metrics['recall']
           for class_name, metrics in class_results.items()},
        **{f"{class_name}_f1": metrics['f1']
           for class_name, metrics in class_results.items()},
        **{f"{class_name}_mean_iou": metrics['mean_iou']
           for class_name, metrics in class_results.items()}
    })
    
    # вывод результатов
    print("\nОбщие метрики:")
    for metric, value in overall_metrics.items():
        print(f"{metric}: {value:.4f}")
    
    print("\nМетрики по классам:")
    for class_name, metrics in class_results.items():
        print(f"\n{class_name}:")
        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")
    
    wandb.finish()

if __name__ == "__main__":
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print('Начало оценки модели!')
        main()
        print("\nОценка модели успешно завершена!")
    except Exception as e:
        import traceback
        print(f"Произошла ошибка: {e}")
        print("Полный стек ошибки:")
        print(traceback.format_exc())