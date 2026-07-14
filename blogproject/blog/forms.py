from django import forms
<<<<<<< HEAD

from .models import Post
=======
# Added Comment to the import below
from .models import Post, Comment
>>>>>>> 5cc9867f4a4bdeb22ab5dbdb98edbe6a2278d16d


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "excerpt",
            "content",
            "featured_image",
            "category",
            "tags",
            "status",
            "is_featured",
        ]
        
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "excerpt": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
            "featured_image": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
<<<<<<< HEAD
=======

# --- NEW COMMENT FORM ADDED BELOW ---

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        # We only want the user to type the content itself
        fields = ['content'] 
        
        # Adding Bootstrap classes for styling and validation constraints
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Write a comment...',
                'minlength': '2',
                'maxlength': '1000'
            }),
        }
        
    def clean_content(self):
        """Strips whitespace from the beginning and end of the comment"""
        content = self.cleaned_data.get('content')
        if content:
            return content.strip()
        return content
>>>>>>> 5cc9867f4a4bdeb22ab5dbdb98edbe6a2278d16d
