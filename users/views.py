from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.utils import timezone
from users.models import *
from users.serializers import *
from users.role_enum import RoleEnum
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from music.models import ArtistFollow, Song, Album
from users.student_verification_utils import (
    extract_ip_address,
    extract_user_agent
)


class UserViewSet(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except Exception as e:
            # Handle any remaining database errors gracefully
            if 'unique' in str(e).lower() or 'username' in str(e).lower():
                return Response(
                    {'error': 'A user with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise
        
        role = request.data.get('role', RoleEnum.USER.value)
        UserProfile.objects.create(user=user, profile_type=role)
        token,created = Token.objects.get_or_create(user=user)
        response_data={
            'token': token.key,
            'user':serializer.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        role = request.data.get('role')
        if role is not None:
            user.profile.profile_type = role
            user.profile.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LoginView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            token= Token.objects.get(user=user)
            response_data = {
                'token': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        # Handle nested user data format from frontend
        data = request.data.copy()
        if 'user[email]' in data:
            if 'user' not in data:
                data['user'] = {}
            data['user']['email'] = data.pop('user[email]')
        if 'user[password]' in data:
            if 'user' not in data:
                data['user'] = {}
            data['user']['password'] = data.pop('user[password]')
        
        serializer = self.get_serializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ArtistViewSet(viewsets.ViewSet):
    """ViewSet for artist-related operations"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def list_artists(self, request):
        """List all artists"""
        artists = User.objects.filter(role=RoleEnum.ARTIST.value).annotate(
            song_count=Count('songs'),
            follower_count=Count('followers')
        )
        
        # Search filter
        search = request.query_params.get('search', None)
        if search:
            artists = artists.filter(username__icontains=search)
        
        results = [{
            'id': str(artist.id),
            'username': artist.username,
            'email': artist.email,
            'song_count': artist.song_count,
            'follower_count': artist.follower_count,
            'is_following': ArtistFollow.objects.filter(
                user=request.user,
                artist=artist
            ).exists() if request.user.is_authenticated else False
        } for artist in artists[:50]]
        
        return Response(results)

    @action(detail=True, methods=['post', 'delete'])
    def follow(self, request, pk=None):
        """Follow or unfollow an artist"""
        try:
            artist = User.objects.get(id=pk, role=RoleEnum.ARTIST.value)
        except User.DoesNotExist:
            return Response({"error": "Artist not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        if artist == request.user:
            return Response({"error": "Cannot follow yourself"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if request.method == 'POST':
            follow, created = ArtistFollow.objects.get_or_create(
                user=request.user,
                artist=artist
            )
            if created:
                return Response({"message": f"Now following {artist.username}"}, 
                              status=status.HTTP_201_CREATED)
            return Response({"message": "Already following this artist"})
        
        elif request.method == 'DELETE':
            deleted = ArtistFollow.objects.filter(
                user=request.user,
                artist=artist
            ).delete()
            if deleted[0]:
                return Response({"message": f"Unfollowed {artist.username}"})
            return Response({"error": "Not following this artist"}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def following(self, request):
        """Get artists the user is following"""
        following = ArtistFollow.objects.filter(user=request.user).select_related('artist')
        artists = [f.artist for f in following]
        results = [{
            'id': str(artist.id),
            'username': artist.username,
            'email': artist.email,
            'song_count': artist.songs.count(),
            'followed_at': f.followed_at.isoformat()
        } for f, artist in zip(following, artists)]
        return Response(results)

    @action(detail=False, methods=['get'])
    def followers(self, request):
        """Get user's followers (if user is an artist)"""
        if request.user.role != RoleEnum.ARTIST.value:
            return Response({"error": "Only artists have followers"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        followers = ArtistFollow.objects.filter(artist=request.user).select_related('user')
        results = [{
            'id': str(f.user.id),
            'username': f.user.username,
            'email': f.user.email,
            'followed_at': f.followed_at.isoformat()
        } for f in followers]
        return Response(results)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get artist profile with stats"""
        try:
            artist = User.objects.get(id=pk, role=RoleEnum.ARTIST.value)
        except User.DoesNotExist:
            return Response({"error": "Artist not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        profile_data = {
            'id': str(artist.id),
            'username': artist.username,
            'email': artist.email,
            'song_count': artist.songs.count(),
            'album_count': Album.objects.filter(user=artist).count(),
            'follower_count': ArtistFollow.objects.filter(artist=artist).count(),
            'total_plays': artist.songs.aggregate(total=Count('play_count'))['total'] or 0,
            'total_likes': artist.songs.aggregate(total=Count('likes'))['total'] or 0,
            'is_following': ArtistFollow.objects.filter(
                user=request.user,
                artist=artist
            ).exists() if request.user.is_authenticated else False
        }
        
        return Response(profile_data)

    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Get all songs by an artist"""
        try:
            artist = User.objects.get(id=pk, role=RoleEnum.ARTIST.value)
        except User.DoesNotExist:
            return Response({"error": "Artist not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        from music.serializers import SongSerializer
        songs = artist.songs.filter(visibility=1)  # Public songs only
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)


class StudentVerificationViewSet(viewsets.ViewSet):
    """ViewSet for student verification operations."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """Submit student verification request."""
        serializer = StudentVerificationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        profile = user.profile
        
        # Check if user already has an approved verification
        existing_approved = StudentVerification.objects.filter(
            user=user,
            status=StudentVerification.VerificationStatus.APPROVED
        ).first()
        
        if existing_approved and profile.is_student_verified:
            return Response({
                'error': 'You already have an approved student verification.',
                'verification_id': str(existing_approved.id),
                'status': existing_approved.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if there's a pending verification
        pending = StudentVerification.objects.filter(
            user=user,
            status=StudentVerification.VerificationStatus.PENDING
        ).first()
        
        if pending:
            return Response({
                'error': 'You already have a pending verification request. Please wait for review.',
                'verification_id': str(pending.id),
                'status': pending.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare verification data
        verification_data = serializer.validated_data.copy()
        date_of_birth = verification_data.pop('date_of_birth')
        is_distance_learning = verification_data.pop('is_distance_learning', False)
        
        # AI Verification BEFORE creating the record
        from django.conf import settings
        from users.ai_verification import StudentVerificationAI
        
        ai_result = None
        if getattr(settings, 'ENABLE_AI_VERIFICATION', True):
            ai_service = StudentVerificationAI()
            
            # Prepare verification data for AI (both email and document are required)
            ai_verification_data = {
                'school_email': verification_data.get('school_email'),
                'school_name': verification_data.get('school_name'),
                'enrollment_date': verification_data.get('enrollment_date'),
                'graduation_date': verification_data.get('graduation_date'),
                'document_type': verification_data.get('document_type'),
                'document_file': verification_data.get('document_file'),
                'full_name_on_document': verification_data.get('full_name_on_document'),
            }
            
            # Run AI verification
            ai_result = ai_service.auto_verify_submission(ai_verification_data)
            
            # Auto-reject if AI is confident it's invalid - return detailed error messages
            if ai_result.get('auto_rejected'):
                error_messages = ai_result.get('error_messages', [])
                if error_messages:
                    error_text = "\n".join(f"• {msg}" for msg in error_messages)
                else:
                    error_text = ai_result.get('reason', 'Verification failed')
                
                return Response({
                    'error': error_text,
                    'error_messages': error_messages,
                    'ai_verified': True,
                    'confidence': ai_result.get('confidence', 0.0),
                    'verification_details': ai_result.get('verification_details', {})
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create verification request (only if not auto-rejected)
        # Both email and document are required, use 'document' as primary method since both are provided
        verification = StudentVerification.objects.create(
            user=user,
            verification_method=StudentVerification.VerificationMethod.DOCUMENT,  # Both are required, document is primary
            school_email=verification_data.get('school_email'),
            document_type=verification_data.get('document_type'),
            document_file=verification_data.get('document_file'),
            full_name_on_document=verification_data.get('full_name_on_document'),
            school_name=verification_data.get('school_name'),
            enrollment_date=verification_data.get('enrollment_date'),
            graduation_date=verification_data.get('graduation_date'),
            ip_address=extract_ip_address(request),
            user_agent=extract_user_agent(request),
            status=StudentVerification.VerificationStatus.PENDING
        )
        
        # Update user profile with date of birth and distance learning status
        profile.student_date_of_birth = date_of_birth
        profile.is_distance_learning = is_distance_learning
        profile.save()
        
        # Auto-approve if AI is confident
        if ai_result and ai_result.get('auto_approved') and not ai_result.get('requires_manual_review'):
            verification.approve(reviewer=user)  # Auto-approve
            response_serializer = StudentVerificationSerializer(verification)
            return Response({
                'message': 'Student verification approved automatically! Your student status has been verified.',
                'verification': response_serializer.data,
                'ai_verified': True,
                'confidence': ai_result.get('confidence', 0.0)
            }, status=status.HTTP_201_CREATED)
        
        # Store AI verification result in notes for admin review
        if ai_result:
            verification.notes = f"AI Verification: {ai_result.get('reason', '')} (Confidence: {ai_result.get('confidence', 0.0):.2f})"
            if ai_result.get('warnings'):
                verification.notes += f"\nWarnings: {', '.join(ai_result.get('warnings', []))}"
            verification.save()
        
        response_serializer = StudentVerificationSerializer(verification)
        message = 'Student verification request submitted successfully.'
        if ai_result and ai_result.get('requires_manual_review'):
            message += ' AI verification completed but requires manual review for final approval.'
            if ai_result.get('warnings'):
                message += f" Note: {', '.join(ai_result.get('warnings', []))}"
        else:
            message += ' It will be reviewed within a few days.'
        
        return Response({
            'message': message,
            'verification': response_serializer.data,
            'ai_verified': ai_result is not None,
            'ai_confidence': ai_result.get('confidence', 0.0) if ai_result else None,
            'warnings': ai_result.get('warnings', []) if ai_result else []
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current student verification status."""
        user = request.user
        profile = user.profile
        
        # Get latest verification
        latest_verification = StudentVerification.objects.filter(
            user=user
        ).order_by('-created_at').first()
        
        response_data = {
            'is_student': profile.is_student,
            'is_verified': profile.is_student_verified,
            'verification_date': profile.student_verification_date,
            'school_email': profile.student_school_email,
            'school_name': profile.student_school_name,
        }
        
        if latest_verification:
            verification_serializer = StudentVerificationStatusSerializer(latest_verification)
            response_data['latest_verification'] = verification_serializer.data
        
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get all verification requests for the user."""
        verifications = StudentVerification.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        serializer = StudentVerificationSerializer(verifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a student verification (admin only)."""
        try:
            verification = StudentVerification.objects.get(id=pk)
        except StudentVerification.DoesNotExist:
            return Response(
                {'error': 'Verification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        verification.approve(request.user)
        
        serializer = StudentVerificationSerializer(verification)
        return Response({
            'message': 'Student verification approved successfully.',
            'verification': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a student verification (admin only)."""
        try:
            verification = StudentVerification.objects.get(id=pk)
        except StudentVerification.DoesNotExist:
            return Response(
                {'error': 'Verification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        verification.reject(request.user, rejection_reason)
        
        serializer = StudentVerificationSerializer(verification)
        return Response({
            'message': 'Student verification rejected.',
            'verification': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """Get all pending verifications (admin only)."""
        verifications = StudentVerification.objects.filter(
            status=StudentVerification.VerificationStatus.PENDING
        ).order_by('created_at')
        
        serializer = StudentVerificationSerializer(verifications, many=True)
        return Response(serializer.data)