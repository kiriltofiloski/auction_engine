from datetime import timedelta
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save

class UserManager(BaseUserManager):
    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if not email:
            raise ValueError('Email is required for superuser.')
        
        # If username is not provided, generate one (optional)
        if not username:
            username = email.split('@')[0]  # Use part of email as username
        
        return self._create_user(email, username, password, **extra_fields)
    
    def _create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30, blank=True)

    #remove constraints from username, since we won't use it
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

class Auction(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='auctions/', null=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=(timezone.now() + timedelta(days=1)))
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['end_time']),
        ]

    def __str__(self):
        return f"{self.name} (${self.current_price})"

    @property
    def time_remaining(self):
        """Returns remaining time in seconds"""
        return (self.end_time - timezone.now()).total_seconds()

    @property
    def highest_bidder(self):
        """Returns the user with the highest bid"""
        highest_bid = self.bids.order_by('-amount').first()
        return highest_bid.user if highest_bid else None

    def update_status(self):
        """Check and update auction active status"""
        if self.end_time <= timezone.now():
            self.is_active = False
            self.save()
            return False
        return True
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New auction being created
            from .tasks import check_ended_auctions
            check_ended_auctions.apply_async(eta=self.end_time)
        super().save(*args, **kwargs)

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['auction', 'amount'],
                name='unique_bid_amount_per_auction'
            )
        ]

    def __str__(self):
        return f"${self.amount} on {self.auction.name} by {self.user.email}"

    def save(self, *args, **kwargs):
        """Override save to update auction price"""
        self.full_clean()  # Runs clean() validation
        super().save(*args, **kwargs)
        self.auction.current_price = self.amount
        self.auction.save()

@receiver(post_save, sender=Auction)
def set_initial_price(sender, instance, created, **kwargs):
    """Set current_price = starting_price when auction is created"""
    if created:
        instance.current_price = instance.starting_price
        instance.save()