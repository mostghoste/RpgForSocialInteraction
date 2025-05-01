from django.core.management.base import BaseCommand
from game.models import QuestionCollection, Question, Character

class Command(BaseCommand):
    help = "Populate the database with Lithuanian question categories and characters"

    def handle(self, *args, **options):
        # Remove existing data
        self.stdout.write("Deleting existing QuestionCollections, Questions, and Characters...")
        QuestionCollection.objects.all().delete()
        Question.objects.all().delete()
        Character.objects.all().delete()

        # Define new question categories, descriptions, and questions
        collections_data = [
            {
                "name": "Kas aš toks?",
                "description": "Savęs pažinimas, vertybės, įsitikinimai ir gyvenimo kryptis.",
                "questions": [
                    "Koks tavo gyvenimo moto?",
                    "Jei galėtum pasirinkti, kokį darbą norėtum dirbti?",
                    "Ką labiausiai norėtum pasiekti gyvenime?",
                    "Ko labiausiai gailiesi?",
                    "Ką paprasčiausiai negali pakęsti?",
                    "Kokį vieną dalyką pakeistum apie save?",
                    "Koks filmas ar serialas geriausiai apibūdina tavo gyvenimą?",
                    "Kas tavo didžiausias įkvėpimas?",
                    "Ką norėtum, kad kiti žmonės žinotų apie tave?",
                    "Ko labiausiai ieškai antroje pusėje?",
                    "Ką apie tave žino tik tavo tėvai?"
                ]
            },
            {
                "name": "Atsiminimai ir jausmai",
                "description": "Praeities patirtys, emocijos, sentimentai ir vidinės kovos.",
                "questions": [
                    "Koks atsiminimas naktį tau neleidžia užmigti?",
                    "Koks tavo mėgstamiausias atsiminimas?",
                    "Kokiu savo poelgiu didžiuojiesi labiausiai?",
                    "Kada esi jautęs didžiausią pavydą?",
                    "Už ką savo gyvenime esi labiausiai dėkingas?",
                    "Kokį komplimentą dažniausiai girdi iš aplinkinių?",
                    "Kokia tavo mėgstamiausia šventė?",
                    "Ką mėgsti daryti, kai nori pailsėti?",
                    "Koks yra gražiausias dalykas, kokį esi matęs?"
                ]
            },
            {
                "name": "Svajonės ir fantazijos",
                "description": "Ateities troškimai ir išgalvoti scenarijai.",
                "questions": [
                    "Į kokį pasaulio kraštą labiausiai norėtum nuvykti?",
                    "Jei pinigai nebūtų limitas, ką norėtum nusipirkti?",
                    "Kokią super galią norėtum turėti?",
                    "Su kokio dalyko ekspertu norėtum susitikti?",
                    "Kokį įgūdį visada norėjai išmokti?",
                    "Jei galėtum keliauti laiku, į kokį laikotarpį nusikeltum?",
                    "Jei galėtum palikti tik vieną metų laiką, koks jis būtų?",
                    "Ką norėtum daryti dažniau, nei darai dabar?",
                    "Kokį gyvūną norėtum laikyti kaip augintinį?"
                ]
            },
            {
                "name": "Kasdienybė ir įpročiai",
                "description": "Maži, bet svarbūs gyvenimo aspektai.",
                "questions": [
                    "Koks tavo mėgstamiausias patiekalas?",
                    "Kokia tavo mėgstamiausia telefono programėlė?",
                    "Kokio kvapo nemėgsti labiausiai?",
                    "Kokią dovaną norėtum gauti su gimtadieniu?",
                    "Koks yra keisčiausias dalykas tavo namuose?",
                    "Kas yra svarbiausia tavo ryto rutinos dalis?",
                ]
            },
            {
                "name": "Įdomybės ir iššūkiai",
                "description": "Netikėti, juokingi ir kūrybiški klausimai.",
                "questions": [
                    "Ką darytum, kad išbūtum nemiegojęs tris paras?",
                    "Jei galėtum įšokti į baseiną, pripildytą bet kuo – kas tai būtų?",
                    "Jei penkioms sekundėms turėtum visos žmonijos dėmesį, ką sakytum?",
                    "Kokio modernaus išradimo niekaip nesupranti?",
                    "Kokiu kvailiausiu būdu esi susižalojęs?",
                    "Su kokia transporto priemone atriedėtum į lenktynes?",
                    "Ką darytum, jei žinotum, kad už 24h mirsi?",
                    "Ką atsineštum į vakarėlį, kad visus pralinksmintum?",
                ]
            }
        ]

        self.stdout.write("Creating QuestionCollections with Questions...")
        for col in collections_data:
            qc = QuestionCollection.objects.create(
                name=col["name"],
                description=col["description"],
                created_by=None  # public collection
            )
            for text in col["questions"]:
                q = Question.objects.create(
                    text=text,
                    creator=None
                )
                qc.questions.add(q)
            qc.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created collection '{qc.name}' ({len(col['questions'])} questions)"
                )
            )

        # Create characters
        characters = [
            {"name": "Didysis Karys",     "description": "Nepašalinamas karys, turintis drąsos ir jėgos."},
            {"name": "Magas Didysis",     "description": "Valdo senovines magijos paslaptis."},
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
                self.style.SUCCESS(f"Created character '{char['name']}'")
            )

        self.stdout.write(self.style.SUCCESS("Database populated successfully."))
