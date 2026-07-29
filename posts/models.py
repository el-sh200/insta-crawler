from django.db import models


# Create your models here.

class Page(models.Model):
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class PostKind(models.IntegerChoices):
    PHOTO = 1
    VIDEO = 2
    ALBUM = 3


class Interval(models.IntegerChoices):
    BEFORE = 1
    CURRENT = 2
    AFTER = 3


class Post(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    original_pk = models.CharField(max_length=50)
    post_kind = models.IntegerField(choices=PostKind, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    short_code = models.CharField(max_length=50)
    taken_at = models.DateTimeField()
    is_media_saved = models.BooleanField(default=False)
    is_comment_saved = models.BooleanField(default=False)
    interval = models.IntegerField(choices=Interval)
    is_related = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.short_code


def post_path(instance, filename):
    return '{0}/{1}/{2}'.format(instance.page.username, instance.post.short_code, filename)


class Slide(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    media = models.FileField(upload_to=post_path)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)
    likes_count = models.IntegerField(default=0)
    username = models.CharField(max_length=100)
    left_at = models.DateTimeField()
