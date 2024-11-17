import os
from pathlib import Path
from doclayout_yolo import YOLOv10
from prepare_data import prepare_dataset
from huggingface_hub import hf_hub_download

def main():
    # определяем пути
    project_root = Path.cwd()
    raw_data_dir = project_root / "raw_data"
    output_dir = project_root / "datasets/prepared_data"

    # Создаем конфигурационный файл
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

    print("Загрузка предобученной модели...")
    model_path = hf_hub_download(
        repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
        filename="doclayout_yolo_docstructbench_imgsz1024.pt"
    )
    
    model = YOLOv10(model_path)
    
    print("Запуск обучения...")
    results = model.train(
        data=str(config_path),
        epochs=100,
        imgsz=800,          
        batch=4,            
        device="0",         
        workers=4,          
        project=str(project_root / "runs/train"),
        name="exp",
        exist_ok=True,
        amp=False,          
        cache=False,
        pretrained=True,
        resume=False,
        verbose=True,
        optimizer="SGD",    
        lr0=0.001,         
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        plots=True,
        save=True,
        save_period=10,
        half=True,         
        rect=True,         
        multi_scale=False  
    )

    print(f"Обучение завершено. Модель сохранена в {project_root}/runs/train/exp/weights/best.pt")
    return results

if __name__ == "__main__":
    try:
        # очистка CUDA кэша
        import torch
        torch.cuda.empty_cache()
        
        # установка переменных окружения для оптимизации памяти CUDA
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:32'
        
        results = main()
        print("Обучение успешно завершено")
    except Exception as e:
        import traceback
        print(f"Произошла ошибка: {e}")
        print("Полный стек ошибки:")
        print(traceback.format_exc())