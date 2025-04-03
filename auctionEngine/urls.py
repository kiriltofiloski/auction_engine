from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('auctions/create', views.postAuction, name='auction-create'),
    path('auctions/', views.AuctionListView.as_view(), name='auction-list'),
    path('auctions/<int:pk>/', views.AuctionDetailView.as_view(), name='auction-detail'),
    path('auctions/<int:pk>/bids/create/', views.postBid, name='bid-create'),
    path('auctions/<int:auction_id>/bids/', views.BidListView.as_view(), name='bid-list'),
]