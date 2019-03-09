from django.db import models

# Create your models here.


class Student(models.Model):
    #s_id = models.AutoField(primary_key=True)
    studentID = models.IntegerField(unique=False)
    name = models.CharField(max_length=128, unique=False)
    password = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    c_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.studentID)

    class Meta:
        ordering = ["studentID"]
        verbose_name = "Student"
        verbose_name_plural = "Student"


class Article(models.Model):
    articleID = models.AutoField(primary_key=True)
    authorName = models.CharField(max_length=128)
    articleTitle = models.CharField(max_length=128, unique=False)
    articleContent = models.TextField()
    articlecopyContent = models.TextField()
    article_copy_rate = models.FloatField()
    student = models.ForeignKey("Student", on_delete=models.CASCADE, null=True)


