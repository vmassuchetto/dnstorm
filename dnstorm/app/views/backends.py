from registration.backends.default import DefaultBackend
from registration.forms import RegistrationFormUniqueEmail

class RegistrationFormBackend(DefaultBackend):
    """
    Overrides the default registration backend to provide unique e-mail
    addresses on account creation.
    """

    def get_form_class(self, request):
        return RegistrationFormUniqueEmail
