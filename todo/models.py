from django.db import models

class TodoModel(models.Model):
    text = models.TextField()
    complete = models.BooleanField()

    def __str__(self):
        return "Todo('{}')".format(self.text)
