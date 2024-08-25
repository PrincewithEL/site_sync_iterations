from django.shortcuts import redirect

def save_profile(backend, user, response, *args, **kwargs):
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Check if all required fields are present
    if not profile.phone_number or not profile.gender or not profile.user_type:
        # Redirect to the complete profile page
        return redirect('complete_profile')
