from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from game.models import QuestionCollection, Question, Character
import random

class Command(BaseCommand):
    help = "Populate the database with 10 fun Lithuanian question categories (10 questions each) and 20 characters."

    def handle(self, *args, **options):
        # Get the superadmin (creator) user
        try:
            superadmin = User.objects.get(username="mostghoste")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Superadmin 'mostghoste' not found."))
            return

        self.stdout.write("Deleting existing QuestionCollections, Questions, and Characters...")
        QuestionCollection.objects.all().delete()
        Question.objects.all().delete()
        Character.objects.all().delete()

        # Define 10 fun categories with 10 unique questions each.
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
            "Gyvenimo sprendimai be logikos": [
                "Kodėl tu atsisakai puikaus darbo, kad galėtum daryti ką nors visiškai netikėto?",
                "Kokį kasdienį beprasmišką ritualą tu atlieki, nors niekas jo nesupranta?",
                "Jei laimėtum milijoną, ką tu darytum pirmiausia?",
                "Kaip tu reaguotum, gavęs blogą naujieną, bet apsimetęs, kad viskas gerai?",
                "Kokia taisyklė, kurią tu įvedei be jokios priežasties, tapo tavo gyvenimo dalimi?",
                "Jei turėtum pasirinkti vieną gyvūną, kurį nešiotum ant peties visą gyvenimą, koks jis būtų?",
                "Kaip tu spręstum problemas, kai visi kiti kreipiasi į tradicinius sprendimus?",
                "Ką tu perkant, nors tau to tikrai nereikia?",
                "Koks būtų pats absurdžiausias slaptas talentas, kurį tu turėtum?",
                "Kaip tu reaguotum, jei netyčia taptum pasaulio lyderiu?"
            ],
            "Netikėti herojaus momentai": [
                "Kokiu juokingu būdu tu galėtum išgelbėti pasaulį?",
                "Koks yra tavo netyčinis nuopelnas, kuris privertų kitus tave girti?",
                "Kaip tu taptum herojumi, net jei neturėtum jokių įgūdžių?",
                "Koks absurdiškas ginklas tau būtų tinkamiausias epinei kovai?",
                "Kaip tu sugalvotum savo superherojų vardą?",
                "Ką tu darytum, jei netyčia išgelbėtum princesę?",
                "Koks būtų tavo pačios neefektyviausias, bet veiksmingas kovos būdas?",
                "Kokia priežastis leistų kitiems tave laikyti herojumi?",
                "Kaip tu mėgautumėtės savo nauju didvyriškumu?",
                "Jei turėtum pasirinkti herojinį šūkį, koks jis būtų?"
            ],
            "Blogiausi planai ir išdaigos": [
                "Koks yra blogiausias planas, kurį tu kada nors sugalvojai, bet vis tiek bandei įgyvendinti?",
                "Kaip tu apgautum sistemą, jei turėtum pabandyti?",
                "Kokia idėja atrodė puiki, kol supratai, kad ji visiškai netinka?",
                "Koks būtų pats absurdiškiausias būdas pabėgti iš kalėjimo, jei būtum įstrigęs?",
                "Kaip tu kovotum su priešu, jei neturėtum ginklų?",
                "Kokia priežastis privertų tave patekti į bėdą, kurią kiti laikytų juokinga?",
                "Kaip tu bandytum įrodyti, kad esi teisus, kai visi žino, kad klysti?",
                "Kur tu slapčiausiai paslėptum svarbų objektą?",
                "Koks būtų pats juokingiausias atsiprašymas, kurį tu sugalvotum?",
                "Kaip tu spręstum netikėtą katastrofą savo pačių būdu?"
            ],
            "Kas tave erzina labiausiai?": [
                "Koks įprotis tave labiausiai erzina?",
                "Kaip tu reaguotum, kai kas nors garsiai kramto šalia?",
                "Kokia priežastis priverstų tave pasimelsti dėl nieko?",
                "Kas yra tas dalykas, kurio tu niekada negalėtum toleruoti?",
                "Kaip tu elgtumeisi su žmonėmis, kurie elgiasi beprasmiškai?",
                "Koks garsas tave baisiausiai vargina?",
                "Ką tu darytum, jei kas nors užimtų tavo mėgstamiausią vietą?",
                "Kaip tu reaguotum į nuolatinį pertraukimą?",
                "Koks mažiausias dalykas, kuris tave gali priversti pratrūkti?",
                "Kaip tu spręstum neteisingus faktus, pasakytus su pasitikėjimu?"
            ],
            "Jei turėtum slaptą talentą...": [
                "Koks talentas tu turi, kurio niekam nenori rodyti?",
                "Jei būtum profesionalas, kurioje srityje spindėtum?",
                "Kaip tu panaudotum savo slaptą talentą neįprastai situacijoje?",
                "Koks būtų pats absurdiškiausias talentas, kuris vis tiek galėtų išgelbėti situaciją?",
                "Kaip tu išmokai savo paslėptą įgūdį?",
                "Kaip tu reaguotum, jei kas nors netyčia atskleistų tavo talentą?",
                "Ką tu norėtum turėti kaip visiškai netikėtą talentą?",
                "Kaip tu panaudotum savo įgūdžius, kad išsisuktum iš bėdos?",
                "Ką tu darytum, jei būtum priverstas viešai pasirodyti su savo talentu?",
                "Koks būtų pats juokingiausias momentas, kai tavo talentas išlįstų?"
            ],
            "Neįtikėtini nuotykiai": [
                "Koks būtų pats įdomiausias nuotykis, kurį tu galėtum patirti?",
                "Kaip tu leistum sau keliauti po pasaulį be jokių planų?",
                "Kokią keistą vietą tu norėtum aplankyti, kuri būtų nuotaikinga?",
                "Koks būtų tavo idealus nuotykis su netikėtu posūkiu?",
                "Kaip tu reaguotum, jei netikėtai susidurtum su nežemiška būtybe?",
                "Ką tu padarytum, jei rastum paslėptą lobį?",
                "Kaip tu pasiruoštum nuotykiui, apie kurį niekas negalvoja?",
                "Koks būtų pats absurdiškiausias nuotykis, kurio siektum?",
                "Kaip tu išnaudotum nuotykį, kad pakeistum savo gyvenimą?",
                "Koks būtų tavo nuotykis, jei būtum priverstas pamiršti viską?"
            ],
            "Kas tave įkvepia?": [
                "Kas ar kas tave įkvepia kiekvieną dieną?",
                "Kaip tu randi įkvėpimą netikėtose vietose?",
                "Koks filmas ar knyga tau suteikia naujų idėjų?",
                "Kaip tu panaudotum savo įkvėpimą, kad pakeistum pasaulį?",
                "Koks būtų tavo įkvepiantis pamokymas, kurį norėtum perduoti kitiems?",
                "Kaip tu apibūdintum savo svajonių gyvenimo viziją?",
                "Ką tu darai, kad išlaikytum motyvaciją net sunkiausiu metu?",
                "Kaip tu leistum sau svajoti didelius dalykus?",
                "Koks yra tavo požiūris į nesėkmes ir kaip jos tave įkvepia?",
                "Kaip tu, būdamas įkvėptas, motyvuotum kitus savo pavyzdžiu?"
            ],
            "Tavo keistų įpročių sąrašas": [
                "Koks yra keisčiausias įprotis, kurį tu turi?",
                "Kaip tu pradėjai šį keistą įprotį?",
                "Ką kiti dažniausiai sakytų apie tave dėl šio įpročio?",
                "Kaip tu jautiesi, kai negali atlikti šio įpročio?",
                "Ar tu kada nors bandei nutraukti šį įprotį? Kodėl nepavyko?",
                "Koks yra tavo kasdienio gyvenimo ritmas su šiuo įpročiu?",
                "Kaip tu derini šį įprotį su savo kasdieniais planais?",
                "Kokia būtų pasaulio reakcija, jei tu nutrauktum šį įprotį?",
                "Ar tu laikai šį įprotį savo stiprybe ar silpnybe?",
                "Kaip tu manai, ar šis įprotis tau padeda ar trukdo?"
            ],
            "Neįprasti pokalbiai": [
                "Koks būtų tavo pirmas klausimas nepažįstamam žmogui, jei turėtum pradėti pokalbį?",
                "Kaip tu pradėtum pokalbį su kažkuo, kas atrodo visiškai kitaip?",
                "Kokia tema tave labiausiai domina, kai nori sužinoti apie kitus?",
                "Koks būtų tavo keičiausias pokalbio pradžios sakinys?",
                "Kaip tu reaguotum, jei pokalbis netikėtai pasisuktų į absurdą?",
                "Koks klausimas tave privertų susimąstyti apie gyvenimą?",
                "Ką tu sakytum, jei norėtum pralaužti pokalbio ledus?",
                "Koks būtų tavo netikėčiausias pokalbio užbaigimo sakinys?",
                "Kaip tu užmegztum pokalbį, jei turėtum naudoti tik humorą?",
                "Koks būtų pats keisčiausias klausimas, kurį kada nors uždavė tavo protas?"
            ]
        }

        self.stdout.write("Creating QuestionCollections with Questions...")
        for cat_name, questions in categories.items():
            qc = QuestionCollection.objects.create(
                name=cat_name,
                description=f"Klausimų kolekcija apie {cat_name.lower()}.",
                created_by=superadmin
            )
            # Create each question only for its own collection.
            for q_text in questions:
                question = Question.objects.create(text=q_text, creator=superadmin)
                qc.questions.add(question)
            qc.save()
            self.stdout.write(self.style.SUCCESS(f"Created collection '{qc.name}' with {len(questions)} questions."))

        # Define 20 larger-than-life characters.
        characters = [
            {"name": "Didysis Karys", "description": "Nepašalinamas karys, turintis drąsos ir jėgos."},
            {"name": "Magas Didysis", "description": "Valdo senovines magijos paslaptis."},
            {"name": "Nuotykių Meistras", "description": "Niekada nesustoji ieškoti naujų nuotykių."},
            {"name": "Laisvės Šauklys", "description": "Kovotojas už teisingumą ir laisvę."},
            {"name": "Vaiduoklis Tylus", "description": "Paslaptingas ir mįslingas, niekada neatskleidžia savo tikrojo veido."},
            {"name": "Didysis Vyriausias", "description": "Lyderis, įkvepiantis savo didingumu ir išmintimi."},
            {"name": "Pasaulio Keliautojas", "description": "Pernelyg nuotykių kupinas, visada siekia naujų horizontų."},
            {"name": "Dainų Karalius", "description": "Jo dainos įkvepia širdis ir pakylėja dvasią."},
            {"name": "Erodiškasis Nuotykis", "description": "Energingas ir visada pasiruošęs iššūkiams."},
            {"name": "Legendo Kūrėjas", "description": "Skulptuoja pasakojimus, kurie įkvepia kartų kartoms."},
            {"name": "Mėnesio Paslaptis", "description": "Stebina savo neatskleista paslaptimi."},
            {"name": "Užburtasis Drąsuolis", "description": "Nepakartojamas savo drąsa ir magiška aura."},
            {"name": "Nepašalinamas Herojus", "description": "Stovi prieš blogį, nepaisydamas kliūčių."},
            {"name": "Nuotykių Mėgėjas", "description": "Visada ieško iššūkių ir naujų patirčių."},
            {"name": "Svajonių Karys", "description": "Kovoja už svajones, kurios keičia pasaulį."},
            {"name": "Didysis Išmintingasis", "description": "Žino atsakymus į senovės paslaptis."},
            {"name": "Šviesos Nešėjas", "description": "Atneša viltį ir šviesą net tamsiausiose akimirkose."},
            {"name": "Kariaujantis Poetas", "description": "Suvienija meną ir kovos aistrą."},
            {"name": "Galingasis Garsas", "description": "Jo balsas sklinda per visą pasaulį."},
            {"name": "Legionierius Didysis", "description": "Lyderis, kurio drąsa įkvepia visus."}
        ]

        self.stdout.write("Creating Characters...")
        for char in characters:
            Character.objects.create(
                name=char["name"],
                description=char["description"],
                creator=superadmin
            )
            self.stdout.write(self.style.SUCCESS(f"Created character '{char['name']}'."))

        self.stdout.write(self.style.SUCCESS("Database populated successfully."))
