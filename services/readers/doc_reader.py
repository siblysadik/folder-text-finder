import logging
import subprocess
import os
import shutil
import platform
import tempfile

logger = logging.getLogger("doc_reader")

def get_doc_content(file_obj, file_name, temp_uploads_dir):
    full_text = ""
    input_file_path = os.path.join(temp_uploads_dir, file_name)
    output_dir = tempfile.mkdtemp()
    
    try:
        # Save the uploaded file to a temporary location
        with open(input_file_path, "wb") as f:
            f.write(file_obj.read())

        # Determine the LibreOffice executable path based on the operating system
        if platform.system() == 'Windows':
            libreoffice_path = 'soffice.exe'
        elif platform.system() == 'Darwin':  # macOS
            libreoffice_path = '/Applications/LibreOffice.app/Contents/MacOS/soffice'
        else:  # Linux
            libreoffice_path = 'libreoffice'

        # Convert the .doc file to a plain text file using LibreOffice
        command = [
            libreoffice_path,
            '--headless',
            '--convert-to', 'txt:Text',
            '--outdir', output_dir,
            input_file_path
        ]
        
        logger.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
        
        # Read the content from the converted text file
        output_file_name = os.path.splitext(file_name)[0] + '.txt'
        output_file_path = os.path.join(output_dir, output_file_name)
        
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
        else:
            logger.error(f"Converted text file not found at {output_file_path}")
            
    except FileNotFoundError:
        logger.error("LibreOffice executable not found. Please ensure it is installed and in your system PATH.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during file conversion: {e.stderr}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        # Clean up temporary files and directories
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            
    return full_text