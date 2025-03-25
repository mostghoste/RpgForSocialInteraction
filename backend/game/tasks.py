# game/tasks.py

from celery import shared_task
from .utils import check_and_advance_rounds

@shared_task
def run_round_check():
    print("⏰ Celery: Checking rounds...")
    check_and_advance_rounds()
