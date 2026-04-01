from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model  = Post
        fields = ['content', 'image', 'visibility']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': "What's on your mind? Share an update, question, or resource…",
                'rows': 3,
                'class': 'gh-post-textarea',
            }),
            'visibility': forms.Select(),
        }
        labels = {
            'content':    '',
            'visibility': 'Who can see this?',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model  = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': 'Write a comment…',
                'autocomplete': 'off',
            }),
        }
        labels = {'content': ''}