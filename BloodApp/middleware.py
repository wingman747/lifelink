from django.shortcuts import redirect
from django.urls import reverse
from .models import InstitutionUser

class InstitutionAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                institution_user = InstitutionUser.objects.get(username=request.user)
                if not institution_user.institution.is_verified:
                    # Institution no longer verified
                    return redirect('institution_not_verified')
                if not institution_user.is_active:
                    # User account disabled
                    return redirect('account_disabled')
            except InstitutionUser.DoesNotExist:
                # Regular user, not from institution
                pass
        
        return self.get_response(request)