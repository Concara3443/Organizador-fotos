import os
import shutil
import exifread
import hashlib
import time
from colorama import Fore, Style, init

init(autoreset=True)

# Constantes de configuración
INVASIVE_MODE = False  # True para mover y eliminar, False para copiar
RENAME_PHOTOS = False  # True para modificar el nombre de la foto, False para mantener el nombre original
source_folder = os.path.dirname(os.path.abspath(__file__))  # Carpeta por defecto

MESSAGES = {
    "photo_moved": Fore.GREEN + "Foto movida: {src} a {dest}",
    "photo_copied": Fore.GREEN + "Foto copiada: {src} a {dest}",
    "duplicate_photo_deleted": Fore.RED + "Foto duplicada eliminada: {src}. Original: {original}",
    "duplicate_photo_detected": Fore.RED + "Foto duplicada detectada: {src}. Original: {original}",
    "non_photo_moved": Fore.MAGENTA + "Archivo no fotográfico movido: {src} a {dest}",
    "non_photo_copied": Fore.MAGENTA + "Archivo no fotográfico copiado: {src} a {dest}"
}

def calculate_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_valid_date(date_str):
    return any(char.isdigit() for char in date_str)

def print_message(key, **kwargs):
    print(MESSAGES[key].format(**kwargs))

def organize_photos(source_folder):
    start_time = time.time()
    photo_count = 0
    duplicate_count = 0
    base_dest = os.path.join(source_folder, "Ordenado")
    os.makedirs(base_dest, exist_ok=True)
    no_photos_folder = os.path.join(base_dest, "NoFotos")
    os.makedirs(no_photos_folder, exist_ok=True)
    processed_hashes = {}

    for root, dirs, files in os.walk(source_folder):
        if "Ordenado" in root or "$RECYCLE.BIN" in root:
            continue

        for filename in files:
            file_path = os.path.join(root, filename)
            if filename.lower().endswith(('.py', '.bat', '.txt')):
                continue
            elif filename.lower().endswith(('.jpg', '.png')):
                with open(file_path, 'rb') as f:
                    tags = exifread.process_file(f, stop_tag='DateTimeOriginal', details=False)
                date_tag = tags.get('EXIF DateTimeOriginal') or tags.get('EXIF DateTimeDigitized')
                if date_tag:
                    date_str = str(date_tag).strip()
                    if is_valid_date(date_str):
                        partes = date_str.split(':')
                        if len(partes) >= 3 and ' ' in partes[2]:
                            year = partes[0]
                            month = partes[1]
                            day_time = partes[2].split(' ')
                            day = day_time[0]
                            time_part = day_time[1].split(':')
                            hour = time_part[0]
                            minute = time_part[1] if len(time_part) > 1 else "00"
                            second = time_part[2] if len(time_part) > 2 else "00"
                            formatted_date = f"{year}-{month}-{day}_{hour}-{minute}-{second}" if len(time_part) > 1 else f"{year}-{month}-{day}_{hour}-00-00"
                            formatted_date = f"{year}-{month}-{day}" if len(time_part) == 1 else formatted_date
                            dest_folder = os.path.join(base_dest, year)
                            os.makedirs(dest_folder, exist_ok=True)
                            new_name = f"{formatted_date}.jpg" if RENAME_PHOTOS else filename
                            new_path = os.path.join(dest_folder, new_name)
                            file_hash = calculate_hash(file_path)
                            if file_hash in processed_hashes:
                                duplicate_count += 1
                                if INVASIVE_MODE:
                                    print_message("duplicate_photo_deleted", src=file_path, original=processed_hashes[file_hash])
                                    os.remove(file_path)
                                else:
                                    print_message("duplicate_photo_detected", src=file_path, original=processed_hashes[file_hash])
                            else:
                                processed_hashes[file_hash] = new_path
                                if not os.path.exists(new_path):
                                    if INVASIVE_MODE:
                                        shutil.move(file_path, new_path)
                                        print_message("photo_moved", src=file_path, dest=new_path)
                                    else:
                                        shutil.copy(file_path, new_path)
                                        print_message("photo_copied", src=file_path, dest=new_path)
                                    photo_count += 1
                                else:
                                    counter = 1
                                    while os.path.exists(new_path):
                                        new_name = f"{formatted_date}_{counter}.jpg" if RENAME_PHOTOS else f"{filename}_{counter}"
                                        new_path = os.path.join(dest_folder, new_name)
                                        counter += 1
                                    if INVASIVE_MODE:
                                        shutil.move(file_path, new_path)
                                        print_message("photo_moved", src=file_path, dest=new_path)
                                    else:
                                        shutil.copy(file_path, new_path)
                                        print_message("photo_copied", src=file_path, dest=new_path)
                                    photo_count += 1
                        else:
                            no_date_folder = os.path.join(base_dest, "SinFecha", os.path.relpath(root, source_folder))
                            os.makedirs(no_date_folder, exist_ok=True)
                            new_path = os.path.join(no_date_folder, filename)
                            file_hash = calculate_hash(file_path)
                            if file_hash in processed_hashes:
                                duplicate_count += 1
                                if INVASIVE_MODE:
                                    print_message("duplicate_photo_deleted", src=file_path, original=processed_hashes[file_hash])
                                    os.remove(file_path)
                                else:
                                    print_message("duplicate_photo_detected", src=file_path, original=processed_hashes[file_hash])
                            else:
                                processed_hashes[file_hash] = new_path
                                if INVASIVE_MODE:
                                    shutil.move(file_path, new_path)
                                    print_message("photo_moved", src=file_path, dest=new_path)
                                else:
                                    shutil.copy(file_path, new_path)
                                    print_message("photo_copied", src=file_path, dest=new_path)
                                photo_count += 1
                    else:
                        no_date_folder = os.path.join(base_dest, "SinFecha", os.path.relpath(root, source_folder))
                        os.makedirs(no_date_folder, exist_ok=True)
                        new_path = os.path.join(no_date_folder, filename)
                        file_hash = calculate_hash(file_path)
                        if file_hash in processed_hashes:
                            duplicate_count += 1
                            if INVASIVE_MODE:
                                print_message("duplicate_photo_deleted", src=file_path, original=processed_hashes[file_hash])
                                os.remove(file_path)
                            else:
                                print_message("duplicate_photo_detected", src=file_path, original=processed_hashes[file_hash])
                        else:
                            processed_hashes[file_hash] = new_path
                            if INVASIVE_MODE:
                                shutil.move(file_path, new_path)
                                print_message("photo_moved", src=file_path, dest=new_path)
                            else:
                                shutil.copy(file_path, new_path)
                                print_message("photo_copied", src=file_path, dest=new_path)
                            photo_count += 1
                else:
                    no_date_folder = os.path.join(base_dest, "SinFecha", os.path.relpath(root, source_folder))
                    os.makedirs(no_date_folder, exist_ok=True)
                    new_path = os.path.join(no_date_folder, filename)
                    file_hash = calculate_hash(file_path)
                    if file_hash in processed_hashes:
                        duplicate_count += 1
                        if INVASIVE_MODE:
                            print_message("duplicate_photo_deleted", src=file_path, original=processed_hashes[file_hash])
                            os.remove(file_path)
                        else:
                            print_message("duplicate_photo_detected", src=file_path, original=processed_hashes[file_hash])
                    else:
                        processed_hashes[file_hash] = new_path
                        if INVASIVE_MODE:
                            shutil.move(file_path, new_path)
                            print_message("photo_moved", src=file_path, dest=new_path)
                        else:
                            shutil.copy(file_path, new_path)
                            print_message("photo_copied", src=file_path, dest=new_path)
                        photo_count += 1
            else:
                no_photos_subfolder = os.path.join(no_photos_folder, os.path.relpath(root, source_folder))
                os.makedirs(no_photos_subfolder, exist_ok=True)
                new_path = os.path.join(no_photos_subfolder, filename)
                if INVASIVE_MODE:
                    shutil.move(file_path, new_path)
                    print_message("non_photo_moved", src=file_path, dest=new_path)
                else:
                    shutil.copy(file_path, new_path)
                    print_message("non_photo_copied", src=file_path, dest=new_path)

    if INVASIVE_MODE:
        for root, dirs, files in os.walk(source_folder, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    try:
                        os.rmdir(dir_path)
                    except PermissionError:
                        print(Fore.RED + f"Permission denied: {dir_path}" + Style.RESET_ALL)
                    except Exception as e:
                        print(Fore.RED + f"Error removing directory {dir_path}: {e}" + Style.RESET_ALL)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(Style.BRIGHT + f"\nFotos organizadas: {photo_count}")
    print(Style.BRIGHT + f"Fotos duplicadas: {duplicate_count}")
    print(Style.BRIGHT + f"Tiempo: {elapsed_time:.2f} segundos")
    print(Style.BRIGHT + "Organizado con ♥️ por Guillermo Cortés")

def main_menu():
    global INVASIVE_MODE, RENAME_PHOTOS, source_folder
    """
    Menú para configurar:
    1. Organiza la carpeta actual
    2. Alternar modo invasivo (mover/eliminar en lugar de copiar)
    3. Alternar renombrado de fotos (usar fecha/hora originales)
    4. Cambiar la carpeta de origen
    0. Salir
    """
    os.system('cls')
    print(Fore.CYAN + Style.BRIGHT + "╔═══════════════════════════════════════╗")
    print("            MENÚ DE CONFIGURACIÓN       ")
    print("╚═══════════════════════════════════════╝" + Style.RESET_ALL)
    estado_invasivo = (Fore.YELLOW + "[MOVER FOTOS Y ELIMINAR DUPLICADOS]" if INVASIVE_MODE else Fore.GREEN + "[COPIAR LAS FOTOS Y ORDENARLAS]")
    estado_renombrado = (Fore.YELLOW + "[NOMBRAR LAS FOTOS CON LA FECHA]" if RENAME_PHOTOS else Fore.GREEN + "[NO CAMBIAR EL NOMBRE]")
    print(Fore.GREEN + " 1 " + Style.BRIGHT + "- Iniciar el proceso de organización" + Style.RESET_ALL)
    print(Fore.GREEN + " 2 " + Style.RESET_ALL + "- Alternar modo invasivo (mover/eliminar en lugar de copiar)" + 
          Fore.WHITE + f"   Estado actual: {estado_invasivo}" + Style.RESET_ALL)
    print(Fore.GREEN + " 3 " + Style.RESET_ALL + "- Alternar renombrado de fotos (usar fecha/hora originales)" + 
          Fore.WHITE + f"  Estado actual: {estado_renombrado}" + Style.RESET_ALL)
    print(Fore.GREEN + " 4 " + Style.RESET_ALL + "- Cambiar la carpeta de origen" + 
          Fore.WHITE + "   Carpeta actual: " + Fore.YELLOW + f"[{source_folder}]" + Style.RESET_ALL)
    print(Fore.RED + " 0 " + Style.BRIGHT + "- Salir\n" + Style.RESET_ALL)
    
    eleccion = input("Seleccione una opción: " + Fore.YELLOW)
    if eleccion == '1':
        os.system('cls')
        organize_photos(source_folder)
    elif eleccion == '2':
        os.system('cls')
        INVASIVE_MODE = not INVASIVE_MODE
        print(Fore.CYAN + f"Modo invasivo {'activado' if INVASIVE_MODE else 'desactivado'}\n" + Style.RESET_ALL)
        main_menu()
    elif eleccion == '3':
        os.system('cls')
        RENAME_PHOTOS = not RENAME_PHOTOS
        print(Fore.CYAN + f"Renombrado de fotos {'activado' if RENAME_PHOTOS else 'desactivado'}\n" + Style.RESET_ALL)
        main_menu()
    elif eleccion == '4':
        os.system('cls')
        nuevo_path = input(Fore.CYAN + "Ingrese la nueva carpeta de origen: " + Style.RESET_ALL)
        if nuevo_path.strip():
            source_folder = nuevo_path.strip()
        else:
            source_folder = os.path.dirname(os.path.abspath(__file__))
        print(Fore.GREEN + f"Carpeta de origen actualizada: {source_folder}\n" + Style.RESET_ALL)
        main_menu()
    elif eleccion == '0':
        os.system('cls')
        print(Fore.MAGENTA + "Saliendo del programa..." + Style.RESET_ALL)
        exit()
    else:
        os.system('cls')
        print(Fore.RED + "Opción inválida. Inténtelo de nuevo.\n" + Style.RESET_ALL)
        main_menu()

if __name__ == "__main__":
    main_menu()