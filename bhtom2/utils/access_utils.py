
def can_access(request):
    user = request.user
    if request.path.startswith('/proposals/'):
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    if request.path.startswith('/users/'):
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    if request.path.startswith('/observations/'):
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    if request.path.startswith('/alerts/'):
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    return True  # Allow access to other URLs