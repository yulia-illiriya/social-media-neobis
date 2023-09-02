from django.db import models
from user_profile.models import User
from cloudinary.models import CloudinaryField
from cloudinary_storage.storage import VideoMediaCloudinaryStorage
from cloudinary_storage.validators import validate_video
    

class Thread(models.Model):
    content = models.CharField("Текст", max_length=280)
    author = models.ForeignKey(User, verbose_name="Автор", on_delete=models.CASCADE)
    video = models.FileField("Видео", null=True, blank=True, storage=VideoMediaCloudinaryStorage(),
                              validators=[validate_video])  
    likes = models.PositiveBigIntegerField("Лайки", blank=True, null=True, default=0)
    created = models.DateTimeField("Время поста", auto_now_add=True)
    repost = models.ForeignKey("Thread", verbose_name="Repost", on_delete=models.CASCADE, null=True, blank=True)    
    
    def __str__(self):
        return self.content
    
    class Meta:
        verbose_name = "thread"
        verbose_name_plural = "threads"
    
    
class Photo(models.Model):
    photo = models.ImageField(upload_to='images/')
    thread = models.ForeignKey(Thread, verbose_name="Thread", on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "photo"
        verbose_name_plural = "photos"
        
        
class Quote(models.Model):
    addional_text = models.CharField("Текст", max_length=280)
    thread = models.ForeignKey(Thread, verbose_name="Thread", related_name="quote", on_delete=models.CASCADE)
    reposted_at = models.DateTimeField("Репост сделан в", auto_now_add=True)
    who_quoted = models.ForeignKey(User, verbose_name="кто процитировал", on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Quote"
        verbose_name_plural = "Quotes"
        
        
class Like(models.Model):
    thread = models.ForeignKey(Thread, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("thread", "user"), )
    
