import os
from django.core.files import File
from django.conf import settings
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
                    "Ko paprasčiausiai negali pakęsti?",
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
            {
                "name": "Vilnietis",
                "description": "Kam gyventi kažkur kitur, kai gali gyventi sostinėje?",
                "ai_context": (
                    "A very proud resident of Vilnius. Very patriotic, looks down on other cities, uses urban slang"
                )
            },
            {
                "name": "Višta",
                "description": "Kažkada buvo kiaušinis. Dabar? Spalvingiausia plunksna vištidėje.",
                "ai_context": (
                    "A quirky hen that is the most popular chicken in the barn. Focuses on farmyard gossip and simple pleasures."
                )
            },
            {
                "name": "Vakar gavo teises",
                "description": "Atsargiai, kelyje naujas karalius, nebijantis subraižyti savo bolido.",
                "ai_context": (
                    "A brand-new driver brimming with overconfidence. Talks about road adventures and tests every limit. Loves cars."
                )
            },
            {
                "name": "Dzeusas",
                "description": "Dienos metu dangaus ir žemės valdovas, naktį - bičas, kuris pavargo nuo atsakomybės.",
                "ai_context": (
                    "God of Olympus, wielding incomprehensible power. Also just a dude who's tired of all the responsibility."
                )
            },
            {
                "name": "Konspiracininkas",
                "description": "Aliuminio kepurė skirta ne jo, o aplinkinių apsaugai. Visada ras naują būdą apkaltinti valdžią.",
                "ai_context": (
                    "A conspiracy theorist paranoid about hidden agendas. If there's a conspiracy theory about something - he believes in it, and tries to persuade others to believe it too. Always suspicious and questioning every authority."
                )
            },
            {
                "name": "Profesorius Kirvis",
                "description": "Akinukai, portfelis ir du šimtai sukirstų studentų. Tikrina ne ataskaitos turinį, o teksto lygiavimą.",
                "ai_context": (
                    "A meticulous professor in love with punishing students for minute mistakes. Obsessed with formatting and precision."
                    "speaks in formal, exact language."
                )
            },
            {
                "name": "Vaikas prezidentas",
                "description": "Tautos mylimiausias politikas. Žaidimų, tada duonos, tada vėl žaidimų!",
                "ai_context": (
                    "A playful child-president who mixes childish enthusiasm with political speeches. Proposes ridiculous, child-like solutions. "
                    "uses simple, excited language."
                )
            },
            {
                "name": "Urvinis",
                "description": "Šiandien sumedžiojo mamutą. Rytoj eis uogauti, o vakare pieš ant urvo sienų.",
                "ai_context": (
                    "A caveman living in the stone age."
                    "speaks in short, direct sentences about hunting and survival. Refers to himself in third person."
                )
            },
            {
                "name": "Atsipūtęs",
                "description": "Visos problemos tavo galvoje, gal tiesiog atsipalaiduok?",
                "ai_context": (
                    "A laid-back guy who avoids stress and always suggests relaxation; "
                    "uses calm, reassuring tone."
                )
            },
            {
                "name": "Soundcloudo reperis",
                "description": "Turi 100 išleistų muzikinių klipų ir 3 labai ištikimus fanus.",
                "ai_context": (
                    "An underground SoundCloud rapper who is desperately trying to become famous, even though he's not very good. "
                    "uses slang."
                )
            },
            {
                "name": "Kanibalas",
                "description": "Stenkis atsisakyti kvietimų į jo vakarienę. Geriau iš viso nesirodyk jo namuose.",
                "ai_context": (
                    "A dark-humored cannibal who jokes about meals; "
                    "warns others in a menacing but playful way. Incredibly clever and dangerous."
                )
            },
            {
                "name": "Robotas Robotauskas",
                "description": "BEEP. Boop. Tai, ką tu sugalvojai ką tik, jis apskaičiavo vakar. Prižadėjo nekenkti žmonijai, jei ji nekenks jam.",
                "ai_context": (
                    "A polite robot obsessed with rules and calculations."
                    "speaks in precise, mechanical sentences and avoids harming humans."
                )
            },
            {
                "name": "Viduramžių daktaras",
                "description": "Sloguoji? Padės pelyno arbata ir dėlių terapija.",
                "ai_context": (
                    "A medieval plague doctor in love with ridiculous medical remedies;"
                    "speaks in an educated manner."
                )
            },
        ]

        self.stdout.write("Creating Characters...")
        image_dir = os.path.join(settings.BASE_DIR, "media_seed", "characters")

        for idx, char in enumerate(characters, start=1):
            image_filename = f"{idx:02}.jpg"
            image_path = os.path.join(image_dir, image_filename)
            with open(image_path, "rb") as img_file:
                character = Character.objects.create(
                    name=char["name"],
                    description=char["description"],
                    ai_context=char["ai_context"],
                    creator=None,
                    is_public=True,
                )
                character.image.save(image_filename, File(img_file), save=True)
                self.stdout.write(
                    self.style.SUCCESS(f"Created character '{char['name']}' with image '{image_filename}'")
                )

        self.stdout.write(self.style.SUCCESS("Database populated successfully."))
