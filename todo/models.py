from django.db import models

class TodoModel(models.Model):
    class Meta:
        # Ugh. Graphene's Relay pagination support appears to assume all querysets are ordered.
        ordering = ['pk']

    text = models.TextField()
    complete = models.BooleanField()

    def __str__(self):
        return "Todo('{}')".format(self.text)
