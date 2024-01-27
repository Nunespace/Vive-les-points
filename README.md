# Application web Orange County Lettings 

***
Orange County Lettings est une start-up dans le secteur de la location de biens immobiliers. La start-up est en pleine phase d’expansion aux États-Unis. 
Elle souhaite améliorer son site tant sur le code que sur le déploiement.

## Amélioration de l'application

 Les améliorations suivantes ont été mise en oeuvre:
- Refonte de l'architecture modulaire dans le repository GitHub ;
- Réduction de diverses dettes techniques sur le projet ;
- Ajout d'un pipeline CI/CD ainsi que son déploiement ; 
- Surveillance de l’application et suivi des erreurs via Sentry ; 
- Création de la documentation technique de l'application avec Read The Docs et Sphinx.


## Prérequis

L'application aura besoin de **Python** (version 3.12), **Git** et **Pipenv** pour fonctionner. Si besoin, vous pouvez les installer en suivant les instructions sur [cette page](doc/installation_python-git-pipenv.md).


## Installation

Cette application exécutable localement peut être installée à l'aide de *pipenv* en suivant les étapes décrites ci-dessous.
> [!NOTE]  
> Si vous souhaitez utiliser *pip* à la place de *pipenv*, vous diposez du fichier *requirements.txt* pour installer toutes les dépendances du projet. Il vous faudra ensuite activer vous-même l'environnement virtuel (dans ce cas enlever "pipenv" ou "pipenv run" de toutes les commandes),
et mettre *pip install* à la place de *pipenv install*


1. Ouvrez le **terminal** et tapez ::
```
git clone https://github.com/Nunespace/Lettings.git
```

2. Placez-vous dans le répertoire Lettings :
```
cd Lettings
```

3. Installez les dépendances du projet :
```
pipenv install
```
    
4. Démarrez le serveur avec :
```
pipenv run python manage.py runserver
```
5. Ouvrez votre navigateur et entrez l’URL comme indiqué sur le terminal pour démarrer l'application web :

http://127.0.0.1:8000/points/

6. Pour quitter le serveur, appuyez sur *CTRL+C*


Pour les lancements ultérieurs du serveur, il suffit d'exécuter les étape 4 et 5 à partir du répertoire racine du projet.

## Administration du site

Les données de l'API peuvent être administrées par le super-utilisateur avec [le site d'administration de Django](http://127.0.0.1:8000/admin/).

1. Créer votre accès super-utilisateur en tapant :

```
pipenv run python manage.py createsuperuser
```
<sub>puis suivez les instructions après avoir choisi un identifiant(username) et un mot de passe : Voir la [documentation officielle de Django](https://docs.djangoproject.com/fr/4.2/topics/auth/default/) si besoin.

2. Démarrer le serveur avec : 
```
pipenv run python manage.py runserver
```

3. Après avoir démarrer le serveur local (voir *Installation/6 ci-dessus*), taper l'url suivante dans votre navigateur : <http://127.0.0.1:8000/admin/>


4. Entrer votre identifiant et votre mot de passe pour accéder au site d'administration de Django : ce site permet de gérer toutes les opérations [CRUD](https://openclassrooms.com/fr/courses/7172076-debutez-avec-le-framework-django/7516605-effectuez-des-operations-crud-dans-ladministration-de-django) sur les données de l'applications (enfants, points positifs, points négatifs).

