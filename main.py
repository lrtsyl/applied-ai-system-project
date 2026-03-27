from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(title, tasks):
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("No tasks found.")
        return

    for pet, task in tasks:
        status = "Done" if task.completed else "Pending"
        print(
            f"{task.time_str} | {pet.name:<8} | {task.description:<15} | "
            f"{task.frequency:<6} | {status}"
        )


def main():
    owner = Owner("Alex")

    luna = Pet("Luna", "Dog", 4)
    milo = Pet("Milo", "Cat", 2)

    owner.add_pet(luna)
    owner.add_pet(milo)

    today = date.today()

    # Add tasks out of order on purpose
    luna.add_task(Task("Morning walk", "08:00", today, "daily"))
    luna.add_task(Task("Medication", "18:00", today, "daily"))
    milo.add_task(Task("Vet appointment", "10:30", today, "once"))
    milo.add_task(Task("Feed dinner", "18:00", today, "daily"))  # same time as Luna's medication

    scheduler = Scheduler(owner)

    print_schedule("Today's Schedule", scheduler.todays_schedule())

    print("\nConflict Warnings")
    print("-----------------")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(warning)
    else:
        print("No conflicts detected.")

    scheduler.mark_task_complete("Luna", "Morning walk", "08:00", today)

    print_schedule("Incomplete Tasks for Luna", scheduler.filter_tasks(pet_name="Luna", completed=False))


if __name__ == "__main__":
    main()