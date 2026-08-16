from datetime import date
from rest_framework import serializers
from .models import SitterProfile, Service, SitterService, Pet, Booking


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "description"]


class SitterServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = SitterService
        fields = ["id", "service", "service_name", "price_per_day"]


class SitterProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    services = SitterServiceSerializer(many=True, read_only=True)

    class Meta:
        model = SitterProfile
        fields = ["id", "first_name", "last_name", "email", "bio", "city", "years_experience", "services"]


class PetSerializer(serializers.ModelSerializer):
    species_display = serializers.CharField(source="get_species_display", read_only=True)

    class Meta:
        model = Pet
        fields = ["id", "name", "species", "species_display", "breed", "age"]


class BookingSerializer(serializers.ModelSerializer):
    num_days = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pets_details = PetSerializer(source="pets", many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "sitter_service",
            "pets",
            "pets_details",
            "start_date",
            "end_date",
            "status",
            "notes",
            "num_days",
            "total_price",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]

    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate(self, data):
        # Validare interval calendaristic
        if data.get("end_date") and data.get("start_date"):
            if data["end_date"] <= data["start_date"]:
                raise serializers.ValidationError({"end_date": "End date must be strictly after start date."})

        # Validare ca animalele trimise să aparțină userului curent
        request = self.context.get("request")
        if request and "pets" in data:
            for pet in data["pets"]:
                if pet.owner != request.user:
                    raise serializers.ValidationError(
                        {"pets": f"Pet '{pet.name}' (ID: {pet.id}) does not belong to you."}
                    )
        return data

    def create(self, validated_data):
        pets = validated_data.pop("pets")
        booking = Booking.objects.create(
            owner=self.context["request"].user,
            **validated_data
        )
        booking.pets.set(pets)
        return booking