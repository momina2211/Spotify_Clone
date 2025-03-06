from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsArtistOrReadOnly(BasePermission):
    """
    ✅ Artists can create, update, and delete their own songs.
    ✅ Users can only read songs.
    ✅ Artists cannot modify other artists' songs.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:  # ✅ GET, HEAD, OPTIONS allowed for all
            return True
        return request.user.is_authenticated and request.user.role == 2  # ✅ Only artists can modify

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:  # ✅ Read permissions allowed for everyone
            return True
        return obj.user == request.user  # ✅ Only allow modifying own songs
