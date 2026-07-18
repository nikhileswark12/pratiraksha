import re
from rest_framework import serializers
from .models import User
from hospitals.models import Hospital

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    hospitalId = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('name', 'email', 'password', 'role', 'hospitalId', 'phone')

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least 1 uppercase letter.")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least 1 number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least 1 special character.")
        return value

    def validate_role(self, value):
        if value not in dict(User.ROLE_CHOICES).keys():
            raise serializers.ValidationError("Role must be 'operator' or 'hospital_manager'.")
        return value

    def validate(self, data):
        role = data.get('role')
        hospital_id = data.get('hospitalId')

        if role == 'hospital_manager':
            if not hospital_id:
                raise serializers.ValidationError({"hospitalId": "Required for hospital_manager role."})
            if not Hospital.objects.filter(id=hospital_id).exists():
                raise serializers.ValidationError({"hospitalId": "Invalid hospital ID."})
        elif role == 'operator':
            if hospital_id is not None:
                raise serializers.ValidationError({"hospitalId": "Must be null for operator role."})
        
        return data

    def create(self, validated_data):
        hospital_id = validated_data.pop('hospitalId', None)
        if hospital_id:
            validated_data['hospital_id'] = hospital_id
            
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            role=validated_data['role'],
            phone=validated_data.get('phone'),
            hospital_id=hospital_id
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    hospitalId = serializers.UUIDField(source='hospital_id', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'role', 'hospitalId', 'phone')
