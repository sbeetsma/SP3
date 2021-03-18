# SP3
SP opdracht 3

Naam: Sjoerd Beetsma
Student nr: 1789293
Opdracht: 3. Business rules voor Recommendation Engine
Main bestand: TeamV1A1/SP Sjoerd.py
Bestand wat ook functies bevat van deze opdracht: TeamV1A1/PostgresDAO.py

Gebruik het progamma als volgt:

1. Installeer de datastructuur van docent Nick (niet volledig inbegrepen vanwege file size limit)
2. Open de map TeamV1A1 (Prongelijk zelfde map naam als waar PostresDAO instond)
3. Edit het bestand postgresDAO.py zodat bovenaan in dit script de juiste DB credentials hebben
Nu is het bestand van de opdracht 'SP 3 Sjoerd.py' klaar voor gebruik.

2 functies specifiek gemaakt voor opdracht 3 staan in PostgresDAO om de functies die queries constructen gescheiden te houden.
Onderaan dit bestand staan de function calls klaar om de recommendation tables te vullen en ook om een aantal recommendations te doen.

De recommendation engine bepaalt op dezelfde manier voor content filtering en collaborative filtering of een profiel/product op elkaar lijkt.
Door een gegegeven lijst van attributen met elkaar te vergelijken als 1 van die attributen overeenkomt in een ander profiel/product kan deze worden gebruikt bij de recommendation.

De recommendation engine recommend dan bij content filtering products met 1 of meer gelijke eigenschappen.
Bij collaborative filtering wordt eerst een tussen stap gedaan om te kijken welke producten zijn gekocht door profielen met 1 of meer gelijke eigenschapen

Content Rule 1 filtert op category en targetaudience
Content Rule 2 op eigenschappen brand en targetaudience

Collaborative Rule 1 op eigenschap segment

Screenshots staan in de mainbranch.

Meer regels zijn makkelijk toe te voegen door eerst een function call te maken om gegeven eigenschappen te filteren en in te vullen in een nieuwe tabel
Daarna toe te voegen aan de functie start recommendation zodat de regel ook gebruikt kan worden om recommendations op te halen.
