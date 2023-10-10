from cloudinary.uploader import upload
import cloudinary
from moviepy.editor import VideoFileClip
import io
import os
import tempfile
from PIL import Image

def compress_and_upload_video(video_file):
    temp_video_dir = tempfile.mkdtemp()
       
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



# def compress_and_upload_image(image):
#     try:
#         upload_result = upload(image)
#         public_url = upload_result.get("secure_url")
#         transformation = {"width": 600, "crop": "scale"}
#         processed_url = cloudinary.utils.cloudinary_url(public_url, transformation=transformation)
#         return processed_url[1]
    
#     except Exception as e:
#         return str(e)
    
    
def compress_and_upload_image(image):
    try:
        
        transformation = {"quality": "auto", "fetch_format": "auto", "secure": True}
        
        upload_result = upload(image, transformation=transformation)
        public_url = upload_result.get("secure_url")
        
        return public_url
    
    except Exception as e:
        return str(e)



