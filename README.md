# Mycroft Mind

## Postup

0. Udělat soubor s projekty, které chci sledovat a spustit inicializační skript, který by nahrál týmy a projekty i s jejich id podle gitlabu do databáze
1. Získat data z gitlabu pomocí skriptu, který poběží následující den přes cron nebo pipeline
2. Skript pak následně zpracuje data a přídá do databáze
    Deployment Frequency (DF)
        COUNT(deployments WHERE env=production AND status=success) GROUP BY week/project/team

    Lead Time for Changes (LT)
        AVG(deploy_time - commit_time)

    Change Failure Rate (CFR)
        COUNT(deployments WHERE env=production AND status=failed) / COUNT(deployments_total)

    Mean Time To Restore (MTTR)
        AVG(incident_resolved - incident_detected)
3. Data se zobrazí v Grafaně v předem připravených dashboardech
    - dashboardy se definují buď jako celofiremní, po projektech nebo po týmech
    - navíc by se dali sledovat i samostatné aplikace
    - zde hodně záleží na tom jak je firma velká nebo jaké jsou jednotlivé požadavky
    - každý teamleader by pak měl přístup, aby se mohl podívat, jak se jeho týmu momentálně daří (případně i zaměstnanci)

Jak přidat nový projekt ? Přidá se do souboru
Vylepšení stávajícího skriptu ? Předělal bych to aby to fungovalo asynchronně
Jak počítat commit_time ? Můžeme brát v potaz merge commit a nebo první commit který je v tom merge requestu
Kde brát incident_detected a incident_resolved ? Je možnost použít Issues s typem incident (created_at and closed_at) v gitlabu nebo asi by šlo i vzít přes alerty z Grafany nebo i případně Jira a filtrovat issues
Co zobrazovat v Grafaně ? Tabulka s výsledky nebo graf, který ukáže deploymenty v čase