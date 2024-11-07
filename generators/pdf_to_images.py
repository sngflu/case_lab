import os
import pypdfium2 as pdfium

def pdf_to_images(pdf_dir, img_dir, dpi=300):
    os.makedirs(img_dir, exist_ok=True)
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            base_name = os.path.splitext(filename)[0]
            try:
                pdf = pdfium.PdfDocument(pdf_path)
                for i in range(len(pdf)):
                    page = pdf[i]
                    img = page.render(scale=dpi / 72).to_pil()
                    img_filename = f"{base_name}_{i + 1}.png"
                    img.save(os.path.join(img_dir, img_filename))
                    # print(f"Сохранено изображение: {img_filename}")
            except Exception as e:
                print(f"Ошибка при обработке {filename}: {e}")

if __name__ == "__main__":
    pdf_dir = "C:/Users/ВИТАЛИЙ/Desktop/data/pdf"
    img_dir = "C:/Users/ВИТАЛИЙ/Desktop/data/image"
    pdf_to_images(pdf_dir, img_dir)
