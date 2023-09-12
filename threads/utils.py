from cloudinary.uploader import upload
from moviepy.editor import VideoFileClip
import os
import tempfile
from PIL import Image

def compress_and_upload_video(video_file):
    temp_video_dir = tempfile.mkdtemp()
       
    # Сжимаем видео
    input_path = video_file.temporary_file_path()
    compressed_video_path = os.path.join(temp_video_dir, "compressed_video.mp4")    
    video_clip = VideoFileClip(input_path)
    compressed_clip = video_clip.resize(width=640)  # Пример сжатия до ширины 640 пикселей, можно настроить как вам нужно
    
    compressed_clip.write_videofile(compressed_video_path, codec="libx264")
    
    # Загружаем сжатое видео в Cloudinary
    compressed_video_upload = upload(compressed_video_path, resource_type="video")

    # Получаем URL загруженного сжатого видео из Cloudinary
    video_url = compressed_video_upload["secure_url"]
    print(video_url)
    os.remove(compressed_video_path)

    return video_url


def compress_and_upload_image(image):
    try:
        img = Image.open(image)
        image_format = img.format

        if img.width > 600:
            img.thumbnail((600, 600), Image.ANTIALIAS)

        with tempfile.NamedTemporaryFile(encoding="utf8", errors='ignore', delete=False, suffix=".jpeg") as tmp_image:
            if image_format:
                img.save(tmp_image, format=image_format)
            else:
                # Если формат не определен, явно указываем JPEG
                img.save(tmp_image, format="JPEG")

        # Загружаем сжатое изображение в Cloudinary
        result = upload(tmp_image.name)

        # Возвращаем URL загруженного изображения из Cloudinary
        return result.get('secure_url')
    except Exception as e:
        # Обработка ошибок, которые могут возникнуть при обработке изображения
        print(f"An error occurred: {str(e)}")
        return None
    finally:
        if 'tmp_image' in locals():
            # Удаление временного файла
            tmp_image.close()
            os.remove(tmp_image.name)
