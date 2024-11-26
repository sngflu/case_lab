# # * for windows. MS Word is required 
# import os
# from docx2pdf import convert

# def convert_docx_to_pdf(docx_dir, pdf_dir):
#     os.makedirs(pdf_dir, exist_ok=True)
    
#     for filename in os.listdir(docx_dir):
#         if filename.endswith(".docx"):
#             docx_path = os.path.join(docx_dir, filename)
#             pdf_path = os.path.join(pdf_dir, filename.replace(".docx", ".pdf"))
#             try:
#                 convert(docx_path, pdf_path)
#                 # print(f"Конвертирован: {filename} -> {pdf_path}")
#             except Exception as e:
#                 print(f"Ошибка при конвертации {filename}: {e}")

# if __name__ == "__main__":
#     docx_dir = "./data/docx"
#     pdf_dir = "./data/pdf"
#     convert_docx_to_pdf(docx_dir, pdf_dir)

# * for linux. libreoffice is required
import os
import subprocess

def convert_docx_to_pdf(docx_dir, pdf_dir):
    os.makedirs(pdf_dir, exist_ok=True)
    
    for filename in os.listdir(docx_dir):
        if filename.endswith(".docx"):
            docx_path = os.path.join(docx_dir, filename)
            try:
                subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', docx_path, '--outdir', pdf_dir], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при конвертации {filename}: {e}")

if __name__ == "__main__":
    docx_dir = "./data/docx"
    pdf_dir = "./data/pdf"
    convert_docx_to_pdf(docx_dir, pdf_dir)
