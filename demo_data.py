from __future__ import annotations

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task


def build_demo_owner() -> Owner:
    """Return a demo owner with pets and tasks for UI demos and evaluation."""
    owner = Owner("Jordan")

    luna = Pet("Luna", "Dog", 4)
    milo = Pet("Milo", "Cat", 2)
    kiwi = Pet("Kiwi", "Rabbit", 1)

    owner.add_pet(luna)
    owner.add_pet(milo)
    owner.add_pet(kiwi)

    today = date.today()
    tomorrow = today + timedelta(days=1)

    luna.add_task(Task("Morning walk", "08:00", today, "daily", "high", False, "walk"))
    luna.add_task(Task("Evening medication reminder", "18:00", today, "daily", "high", False, "medication"))
    luna.add_task(Task("Fetch play session", "17:00", tomorrow, "once", "medium", False, "play"))

    milo.add_task(Task("Brush fur", "07:30", today, "weekly", "medium", False, "grooming"))
    milo.add_task(Task("Feed dinner", "18:00", today, "daily", "high", False, "feeding"))
    milo.add_task(Task("Quiet play", "20:00", tomorrow, "once", "low", False, "play"))

    kiwi.add_task(Task("Hay refill", "09:00", today, "daily", "high", False, "feeding"))
    kiwi.add_task(Task("Cage cleanup", "15:00", today, "weekly", "medium", False, "general"))

    return owner