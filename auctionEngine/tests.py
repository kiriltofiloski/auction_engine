from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Auction, Bid
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch

User = get_user_model()

class AuctionAPITests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects._create_user(
            email='seller@test.com',
            password='testpass123'
        )
        self.user2 = User.objects._create_user(
            email='bidder@test.com',
            password='testpass123'
        )
        
        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        
        # Create test auction
        self.auction = Auction.objects.create(
            name="Van Gogh Painting",
            description="Original artwork",
            creator=self.user1,
            starting_price=1000,
            current_price=1000,
            end_time=timezone.now() + timedelta(days=1)
        )
        
        # Create test bid
        self.bid = Bid.objects.create(
            auction=self.auction,
            user=self.user2,
            amount=1200
        )
        
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')

    # Auction List Tests
    def test_list_active_auctions(self):
        url = reverse('auction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Van Gogh Painting")

    def test_filter_auctions_by_price(self):
        url = reverse('auction-list') + '?min_price=900&max_price=1300'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 1)

    def test_order_auctions_by_price(self):
        Auction.objects.create(
            name="Cheap Art",
            creator=self.user1,
            starting_price=500,
            current_price=500,
            end_time=timezone.now() + timedelta(days=1))
        
        url = reverse('auction-list') + '?ordering=current_price'
        response = self.client.get(url)
        data = response.json()
        prices = [item['current_price'] for item in data['results']]
        self.assertEqual(prices, ['500.00', '1200.00'])

    # Auction Detail Tests
    def test_retrieve_auction_details(self):
        url = reverse('auction-detail', args=[self.auction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Van Gogh Painting")

    def test_nonexistent_auction(self):
        url = reverse('auction-detail', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Bid Creation Tests
    def test_create_valid_bid(self):
        url = reverse('bid-create', args=[self.auction.id])
        data = {'amount': 1500}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bid.objects.count(), 2)

    def test_bid_below_current_price(self):
        url = reverse('bid-create', args=[self.auction.id])
        data = {'amount': 800}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('higher than current price', str(response.data))

    def test_bid_on_inactive_auction(self):
        self.auction.is_active = False
        self.auction.save()
        url = reverse('bid-create', args=[self.auction.id])
        data = {'amount': 1500}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Authentication Tests
    def test_unauthenticated_access(self):
        self.client.credentials()
        url = reverse('bid-create', args=[self.auction.id])
        response = self.client.post(url, {'amount': 1500}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_self_bid_prevention(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('bid-create', args=[self.auction.id])
        response = self.client.post(url, {'amount': 1500}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Bid List Tests
    def test_list_bids_for_auction(self):
        url = reverse('bid-list', args=[self.auction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['amount'], '1200.00')

    def test_bid_list_pagination(self):
        for i in range(1, 16):
            Bid.objects.create(
                auction=self.auction,
                user=self.user2,
                amount=1200 + i
            )
        
        url = reverse('bid-list', args=[self.auction.id]) + '?page_size=10'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])

class AuctionCreationTests(APITestCase):
    def setUp(self):
        self.user = User.objects._create_user(
            email='seller@test.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = reverse('auction-create')
        self.valid_data = {
            'name': 'Rare Collectible',
            'description': 'Mint condition collectible item',
            'starting_price': 500,
            'end_time': (timezone.now() + timedelta(days=7)).isoformat()
        }

    def test_create_auction_success(self):
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Auction.objects.count(), 1)
        auction = Auction.objects.first()
        self.assertEqual(auction.name, 'Rare Collectible')
        self.assertEqual(auction.creator, self.user)
        self.assertTrue(auction.is_active)

    def test_missing_required_fields(self):
        invalid_data = self.valid_data.copy()
        del invalid_data['name']
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_invalid_price(self):
        invalid_data = self.valid_data.copy()
        invalid_data['starting_price'] = -10
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('starting_price', response.data)

    def test_unauthenticated_access(self):
        self.client.credentials()
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Auction.objects.count(), 0)

    def test_auto_current_price_setting(self):
        response = self.client.post(self.url, self.valid_data, format='json')
        auction = Auction.objects.get(id=response.data['auction']['id'])
        self.assertEqual(auction.current_price, auction.starting_price)