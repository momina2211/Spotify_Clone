from rest_framework import serializers
from datetime import date

from users.models import User, UserProfile, StudentVerification
from users.role_enum import RoleEnum
from users.student_verification_utils import (
    is_educational_email,
    validate_student_age
)


class UserSerializer(serializers.ModelSerializer):
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True)
    role=serializers.ChoiceField(choices=[(role.value,role.name.capitalize()) for role in RoleEnum],required=False)
    class Meta:
        model = User
        fields = ('id', 'email', 'password','role')

    def validate_email(self, value):
        """Validate that the email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        # Also check if username with this email exists
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        email = validated_data['email']
        # Check again before creating (double-check)
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        validated_data['username'] = email
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        try:
            user.save()
        except Exception as e:
            # Handle any database constraint errors
            if 'username' in str(e) or 'unique' in str(e).lower():
                raise serializers.ValidationError("A user with this email already exists.")
            raise
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = instance.email
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        if 'role' in validated_data:
            instance.role = validated_data['role']
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    subscription_plan_name = serializers.SerializerMethodField()
    subscription_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
    
    def get_subscription_plan_name(self, obj):
        """Get subscription plan name if exists"""
        if obj.subscription_plan:
            return obj.subscription_plan.name
        return None

    def update(self, instance, validated_data):
        # Handle nested user data
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        # Handle profile picture
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        
        instance.save()
        return instance


class StudentVerificationSerializer(serializers.ModelSerializer):
    """Serializer for student verification submissions."""
    
    class Meta:
        model = StudentVerification
        fields = [
            'id', 'status', 'verification_method', 'school_email',
            'document_type', 'document_file', 'school_name',
            'full_name_on_document', 'enrollment_date', 'graduation_date',
            'reviewed_at', 'rejection_reason', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'reviewed_at', 'created_at']
    
    def validate_school_email(self, value):
        """Validate school email if provided."""
        if value:
            is_edu, reason = is_educational_email(value)
            if not is_edu:
                raise serializers.ValidationError(reason)
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        verification_method = attrs.get('verification_method')
        
        if verification_method == StudentVerification.VerificationMethod.EMAIL:
            if not attrs.get('school_email'):
                raise serializers.ValidationError({
                    'school_email': 'School email is required for email verification method.'
                })
        elif verification_method == StudentVerification.VerificationMethod.DOCUMENT:
            if not attrs.get('document_file'):
                raise serializers.ValidationError({
                    'document_file': 'Document file is required for document verification method.'
                })
            if not attrs.get('document_type'):
                raise serializers.ValidationError({
                    'document_type': 'Document type is required for document verification method.'
                })
            if not attrs.get('full_name_on_document'):
                raise serializers.ValidationError({
                    'full_name_on_document': 'Full name on document is required for document verification.'
                })
        
        return attrs


class StudentVerificationSubmitSerializer(serializers.Serializer):
    """Serializer for submitting student verification.
    Both email and document are now required for verification.
    """
    
    # Email verification fields (REQUIRED)
    school_email = serializers.EmailField(required=True)
    
    # Document verification fields (REQUIRED)
    document_type = serializers.ChoiceField(
        choices=StudentVerification.DocumentType.choices,
        required=True
    )
    document_file = serializers.ImageField(required=True)
    full_name_on_document = serializers.CharField(
        max_length=200,
        required=True
    )
    
    # Additional information
    school_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    enrollment_date = serializers.DateField(required=False, allow_null=True)
    graduation_date = serializers.DateField(required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=True)
    is_distance_learning = serializers.BooleanField(default=False)
    
    def validate_school_email(self, value):
        """Validate school email."""
        if value:
            is_edu, reason = is_educational_email(value)
            if not is_edu:
                raise serializers.ValidationError(reason)
        return value
    
    def validate_date_of_birth(self, value):
        """Validate student age."""
        is_valid, error_msg = validate_student_age(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_enrollment_date(self, value):
        """Validate enrollment date is reasonable."""
        if value:
            from datetime import date
            today = date.today()
            # Enrollment should not be more than 10 years in the past or in the future
            if value.year < today.year - 10:
                raise serializers.ValidationError(
                    f"Enrollment date {value.year} is too far in the past. Please check the date."
                )
            if value.year > today.year + 1:
                raise serializers.ValidationError(
                    f"Enrollment date {value.year} is in the future. Please check the date."
                )
            # Check for obviously invalid years (like 0024 instead of 2024)
            if value.year < 1900 or value.year > 2100:
                raise serializers.ValidationError(
                    f"Invalid enrollment year: {value.year}. Please check the date format (should be YYYY-MM-DD)."
                )
        return value
    
    def validate_graduation_date(self, value):
        """Validate graduation date is reasonable."""
        if value:
            from datetime import date
            today = date.today()
            # Check for obviously invalid years (like 0024 instead of 2024)
            if value.year < 1900 or value.year > 2100:
                raise serializers.ValidationError(
                    f"Invalid graduation year: {value.year}. Please check the date format (should be YYYY-MM-DD, e.g., 2024-12-31)."
                )
            # Graduation should be in the future (or very recent past for graduated students)
            if value.year < today.year - 2:
                raise serializers.ValidationError(
                    f"Graduation date {value.year} is more than 2 years in the past. If you have already graduated, please contact support."
                )
            if value.year > today.year + 10:
                raise serializers.ValidationError(
                    f"Graduation date {value.year} is too far in the future. Please check the date."
                )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        date_of_birth = attrs.get('date_of_birth')
        enrollment_date = attrs.get('enrollment_date')
        graduation_date = attrs.get('graduation_date')
        
        # Validate age
        if date_of_birth:
            is_valid, error_msg = validate_student_age(date_of_birth)
            if not is_valid:
                raise serializers.ValidationError({'date_of_birth': error_msg})
        
        # Validate date relationships
        if enrollment_date and graduation_date:
            if graduation_date < enrollment_date:
                raise serializers.ValidationError({
                    'graduation_date': 'Graduation date must be after enrollment date.'
                })
        
        # Both email and document are now required
        if not attrs.get('school_email'):
            raise serializers.ValidationError({
                'school_email': 'School email is required for verification.'
            })
        
        if not attrs.get('document_file'):
            raise serializers.ValidationError({
                'document_file': 'Document file is required for verification.'
            })
        
        if not attrs.get('document_type'):
            raise serializers.ValidationError({
                'document_type': 'Document type is required for verification.'
            })
        
        if not attrs.get('full_name_on_document'):
            raise serializers.ValidationError({
                'full_name_on_document': 'Full name on document is required.'
            })
        
        return attrs


class StudentVerificationStatusSerializer(serializers.ModelSerializer):
    """Serializer for checking student verification status."""
    
    class Meta:
        model = StudentVerification
        fields = [
            'id', 'status', 'verification_method', 'created_at',
            'reviewed_at', 'rejection_reason', 'school_email',
            'document_type'
        ]
        read_only_fields = fields

