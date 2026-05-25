from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django_registration.backends.activation.views import RegistrationView

class CustomPasswordResetForm(PasswordResetForm):
    """
    Override standard Password Reset to also trigger activation emails
    if the provided email belongs to an inactive user account.
    """
    def save(self, *args, **kwargs):
        # Standard behavior for active users (sends password reset emails)
        super().save(*args, **kwargs)
        
        email = self.cleaned_data["email"]
        User = get_user_model()
        email_field_name = User.get_email_field_name()
        
        inactive_users = User._default_manager.filter(**{
            '%s__iexact' % email_field_name: email,
            'is_active': False,
        })
        
        if inactive_users.exists():
            request = kwargs.get('request')
            reg_view = RegistrationView()
            reg_view.request = request
            for user in inactive_users:
                try:
                    reg_view.send_activation_email(user)
                except Exception:
                    pass
