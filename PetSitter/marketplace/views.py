from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import SitterProfile, Pet, Booking
from .serializers import SitterProfileSerializer, PetSerializer, BookingSerializer


# -------------------------------------------------------------
# Sitters Endpoints (GET list with filters & GET detail)
# -------------------------------------------------------------
@api_view(["GET"])
def sitter_list(request):
    """
    List sitters with optional filtering:
    - ?city=amsterdam
    - ?service=boarding
    - ?max_price=50
    """
    queryset = SitterProfile.objects.select_related("user").prefetch_related(
        "services__service"
    ).all()

    city = request.query_params.get("city")
    service_name = request.query_params.get("service")
    max_price = request.query_params.get("max_price")

    if city:
        queryset = queryset.filter(city__icontains=city)

    if service_name:
        queryset = queryset.filter(services__service__name__icontains=service_name)

    if max_price:
        queryset = queryset.filter(services__price_per_day__lte=max_price)

    queryset = queryset.distinct()
    serializer = SitterProfileSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def sitter_detail(request, pk):
    """Get complete details for a single sitter."""
    sitter = get_object_or_404(
        SitterProfile.objects.select_related("user").prefetch_related("services__service"),
        pk=pk
    )
    serializer = SitterProfileSerializer(sitter)
    return Response(serializer.data, status=status.HTTP_200_OK)


# -------------------------------------------------------------
# Pets Endpoints (GET user's pets & POST new pet)
# -------------------------------------------------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def pet_list_create(request):
    """List current user's pets or create a new pet assigned to current user."""
    if request.method == "GET":
        pets = Pet.objects.filter(owner=request.user)
        serializer = PetSerializer(pets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = PetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------
# Bookings Endpoints (GET user's bookings & POST new booking)
# -------------------------------------------------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def booking_list_create(request):
    """List bookings for the logged-in user or create a new booking."""
    if request.method == "GET":
        bookings = (
            Booking.objects.filter(owner=request.user)
            .select_related("sitter_service__service", "sitter_service__sitter__user")
            .prefetch_related("pets")
        )
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = BookingSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            booking = serializer.save()
            return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------
# Stretch Phase 4: Patch Booking Status (Confirm / Cancel)
# -------------------------------------------------------------
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def booking_update_status(request, pk):
    """Allow sitters or booking owners to update booking status."""
    booking = get_object_or_404(
        Booking.objects.select_related("sitter_service__sitter__user", "owner"),
        pk=pk
    )

    # Verificare permisiune: doar sitterul asociat sau posesorul pot modifica statusul
    is_sitter = booking.sitter_service.sitter.user == request.user
    is_owner = booking.owner == request.user

    if not (is_sitter or is_owner):
        return Response(
            {"detail": "You do not have permission to update this booking."},
            status=status.HTTP_403_FORBIDDEN,
        )

    new_status = request.data.get("status")
    allowed_statuses = [choice[0] for choice in Booking.STATUS_CHOICES]

    if new_status not in allowed_statuses:
        return Response(
            {"status": f"Invalid status. Choose from: {', '.join(allowed_statuses)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.status = new_status
    booking.save(update_fields=["status"])
    return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)