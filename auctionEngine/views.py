from django.shortcuts import render

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics, filters
from django_filters.rest_framework import DjangoFilterBackend

from django.shortcuts import get_object_or_404
from .models import User, Auction, Bid
from rest_framework.authtoken.models import Token

from .serializers import UserSerializer, AuctionCreateSerializer, AuctionListSerializer, AuctionSerializer, BidSerializer, BidCreateSerializer

from .filters import AuctionFilter

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(email=request.data['email'])
        user.set_password(request.data['password'])
        user.save()
        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'user': serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, email=request.data['email'])
    if not user.check_password(request.data['password']):
        return Response("missing user", status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    return Response({'token': token.key, 'user': serializer.data})

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def postAuction(request):
    serializer = AuctionCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(creator=request.user)
        return Response({'auction': serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuctionListView(generics.ListAPIView):
    """
    GET: List all auctions with filtering, ordering, and pagination
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionListSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AuctionFilter
    ordering_fields = ['created_at', 'current_price']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
    
class AuctionDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve a single auction's details
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer

class BidListView(generics.ListAPIView):
    """
    GET: List all auctions with filtering, ordering, and pagination
    """
    serializer_class = BidSerializer
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return Bid.objects.filter(auction_id=auction_id)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def postBid(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    serializer = BidCreateSerializer(data=request.data)
    if serializer.is_valid():
        bid_amount = serializer.validated_data['amount']
        
        # Check if auction is active
        if not auction.is_active:
            return Response(
                {'error': 'This auction is no longer active'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if bid is higher than current price
        if bid_amount <= auction.current_price:
            return Response(
                {'error': f'Bid must be higher than current price (${auction.current_price})'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if user is not the auction creator
        if request.user == auction.creator:
            return Response(
                {'error': 'You cannot bid on your own auction'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Save the valid bid
        bid = serializer.save(user=request.user, auction=auction)
            
        # Update auction current price
        auction.current_price = bid_amount
        auction.save()
            
        return Response({'bid': serializer.data}, status=status.HTTP_201_CREATED)    
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)