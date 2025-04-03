from celery import shared_task
from django.core.mail import send_mail
from .models import Auction
from datetime import datetime

@shared_task
def check_ended_auctions():
    now = datetime.now()
    ended_auctions = Auction.objects.filter(
        end_time__lte=now,
        is_active=True
    )
    
    for auction in ended_auctions:
        send_auction_result_emails.delay(auction.id)
        auction.is_active = False
        auction.save()

@shared_task
def send_auction_result_emails(auction_id):
    auction = Auction.objects.get(id=auction_id)
    winner = auction.highest_bidder
    
    if(winner):
        # Email to winner
        send_mail(
            'You won the auction!',
            f'You won {auction.name} for ${auction.current_price}',
            'noreply@yourapp.com',
            [winner.email],
            fail_silently=False,
        )
    
    # Email to creator
    send_mail(
        'Your auction ended',
        f'Your auction {auction.name} sold for ${auction.current_price}',
        'noreply@yourapp.com',
        [auction.creator.email],
        fail_silently=False,
    )