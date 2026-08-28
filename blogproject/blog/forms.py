from django import forms
# Added Comment to the import below
from .models import Post, Comment, Author
from .models import Tag
from django.utils.text import slugify  # <-- Add this import


class PostForm(forms.ModelForm):
    # Free-text input field for comma-separated tags
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. anime, movies, tech (separated by commas)",
            }
        ),
        help_text="Separate tags with commas.",
    )

    class Meta:
        model = Post
        fields = [
            "title",
            "excerpt",
            "content",
            "featured_image",
            "category",
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
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate tags_input when editing an existing post
        if self.instance and self.instance.pk:
            self.fields["tags_input"].initial = ", ".join(
                tag.name for tag in self.instance.tags.all()
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)

        def save_tags():
            raw_tags = self.cleaned_data.get("tags_input", "")
            tag_names = [
                name.strip().lower()
                for name in raw_tags.split(",")
                if name.strip()
            ]
            tag_objects = []
            for name in tag_names:
                tag_obj, _ = Tag.objects.get_or_create(
                    name=name,
                    defaults={"slug": slugify(name)},
                )
                tag_objects.append(tag_obj)
            instance.tags.set(tag_objects)

        if commit:
            save_tags()
        else:
            old_save_m2m = getattr(self, "save_m2m", None)

            def custom_save_m2m():
                if old_save_m2m:
                    old_save_m2m()
                save_tags()

            self.save_m2m = custom_save_m2m

        return instance
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
class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = [
            'profile_picture',
            'bio',
            'location',
            'website',
            'github',
            'linkedin',
            'twitter',
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'profile-picture-input',
                'accept': 'image/*',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell readers about yourself...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. San Francisco, CA',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com',
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username',
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username',
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://x.com/username',
            }),
        }
