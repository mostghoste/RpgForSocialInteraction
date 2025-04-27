from django.core.management.base import BaseCommand
from game.models import QuestionCollection, Question, Character

class Command(BaseCommand):
    help = (
        "Populate the database with lithuanian question categories and characters"
    )

    def handle(self, *args, **options):
        # Remove existing data
        self.stdout.write("Deleting existing QuestionCollections, Questions, and Characters...")
        QuestionCollection.objects.all().delete()
        Question.objects.all().delete()
        Character.objects.all().delete()

        # Define question categories and questions
        categories = {
            "Keisčiausios asmeninės nuostatos": [
                "Kokį keistą įsitikinimą turi tu, kurio niekas kitas nesupranta?",
                "Kokia yra pati kvailiausia taisyklė, kurios laikaisi tu?",
                "Jei galėtum pašalinti vieną įprastą dalyką iš pasaulio, kas tai būtų?",
                "Koks įgūdis, kurio tu niekada nenori rodyti, bet kuris tave padaro ypatingu?",
                "Kokią keistą teoriją apie pasaulį tu laikai tiesa?",
                "Ką tu darai be jokios priežasties, kad parodytum savo unikalumą?",
                "Koks būtų tavo didžiausias gyvenimo pasiekimas, kurį kiti laikytų absurdišku?",
                "Ką tu darytum, jei staiga išnyktų gravitacija?",
                "Jei turėtum pasirinkti naują odos ar plaukų spalvą, kokią tu rinktųsi?",
                "Kokią absurdišką lažybą tu visada esi pasiruošęs priimti?"
            ],
        }

        self.stdout.write("Creating QuestionCollections with Questions...")
        for cat_name, questions in categories.items():
            qc = QuestionCollection.objects.create(
                name=cat_name,
                description=f"Klausimų kolekcija apie {cat_name.lower()}.",
                created_by=None  # public collection
            )
            for q_text in questions:
                question = Question.objects.create(
                    text=q_text,
                    creator=None  # public question
                )
                qc.questions.add(question)
            qc.save()
            self.stdout.write(
                self.style.SUCCESS(f"Created collection '{qc.name}' with {len(questions)} questions.")
            )

        # Define characters
        characters = [
            {"name": "Didysis Karys", "description": "Nepašalinamas karys, turintis drąsos ir jėgos."},
            {"name": "Magas Didysis", "description": "Valdo senovines magijos paslaptis."},
            {"name": "Nuotykių Meistras", "description": "Niekada nesustoji ieškoti naujų nuotykių."},
        ]

        self.stdout.write("Creating Characters...")
        for char in characters:
            Character.objects.create(
                name=char["name"],
                description=char["description"],
                creator=None,
                is_public=True
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created character '{char['name']}'.")
            )

        self.stdout.write(self.style.SUCCESS("Database populated successfully."))
