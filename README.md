![logo-image](doc/vive-les-points_titre.png)

# Vive les points! 

***
L'application Vive les points est destinée aux parents pour les aider à gérer les bons et mauvais points de leurs enfants.

## Fonctionnalité de l'application

 L'application dispose d'une page accueil (cliquer sur Vive les points), d'une page barême des points et récompenses (cliquer sur Barêmes), une page historique des points pour chaque enfant (cliquer sur les points de l'enfant concerné) et d'une page pour modifier les points. 


## Prérequis

L'application aura besoin de **Python** (version 3.12), **Git** et **Pipenv** pour fonctionner. Si besoin, vous pouvez les installer en suivant les instructions sur [cette page](doc/installation_python-git-pipenv.md).


## Installation

Cette application exécutable localement peut être installée à l'aide de *pipenv* en suivant les étapes décrites ci-dessous.
> [!NOTE]  
> Si vous souhaitez utiliser *pip* à la place de *pipenv*, vous diposez du fichier *requirements.txt* pour installer toutes les dépendances du projet. Il vous faudra ensuite activer vous-même l'environnement virtuel (dans ce cas enlever "pipenv" ou "pipenv run" de toutes les commandes),
et mettre *pip install* à la place de *pipenv install*


1. Ouvrez le **terminal** et tapez ::
```
git clone https://github.com/Nunespace/Vive-les-points.git
```

2. Placez-vous dans le répertoire Vive-les-points :
```
cd Vive-les-points
```

3. Installez les dépendances du projet :
```
pipenv install
```

<sub> Vous pouvez activer votre environnement virtuel si vous voulez taper les commande sans mettre à chaque fois *pipenv* au début de chaque commande. Voir [cette page](doc/installation_python-git-pipenv.md).


4. Renommer le fichier .env.dev en .env à la racine du projet, y mettre la clé secrète django :
La clé peut être générer avec cette commande : 
```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```


5. Créer les tables nécessaires en base selon les fichiers de migration : 

pipenv run python manage.py migrate
    
6. Démarrez le serveur avec :
```
pipenv run python manage.py runserver
```
7. Ouvrez votre navigateur et entrez l’URL comme indiqué sur le terminal pour démarrer l'application web :

http://127.0.0.1:8000/points/

8. Pour quitter le serveur, appuyez sur *CTRL+C*


Pour les lancements ultérieurs du serveur, il suffit d'exécuter les étapes 6 et 7 à partir du répertoire racine du projet.

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

3. Taper l'url suivante dans votre navigateur : <http://127.0.0.1:8000/admin/>


4. Entrer votre identifiant et votre mot de passe pour accéder au site d'administration de Django : ce site permet de gérer toutes les opérations [CRUD](https://openclassrooms.com/fr/courses/7172076-debutez-avec-le-framework-django/7516605-effectuez-des-operations-crud-dans-ladministration-de-django) sur les données de l'applications (création, modification, effacement, mise à jour des enfants, des points positifs et des points négatifs).


## Déploiement

Le projet est hébergé chez o2switch

## Tests et linting


### Lancement des tests
Les tests de ce projet ont été écrits avec le framework pytest.

Ils sont executables avec la commande [^2]: 
```
pipenv run pytest
```

### Couverture de test

Ce projet contient la librairie Python Coverage.py qui fournit un rapport qui nous donne le pourcentage de couverture de ligne par fichier source de couverture. Ce rapport peut être obtenu avec cette commande[^2] : 
```
pipenv run pytest --cov=.
```
Un rapport HTML, plus détaillé, peut aussi être généré en tapant[^2] : 
```
pipenv run pytest --cov=. --cov-report html
```
Un nouveau dossier *htmlcov* est ainsi créé à l'endroit où vous avez lancé la commande. Avec votre navigateur, ouvrez le fichier *index.html*  qui contient un résumé du rapport de couverture. À partir de cette page, vous pourrez naviguer à travers les différents fichiers afin d’avoir le détail sur la couverture.


### Linting

Le linting sur l'ensemble du code peut être exécuté avec Flake8.

Exécutez, à partir de la  racine du projet, la commande suivante[^2] : 
```
pipenv run flake8
```

[^1]: L’application nécessite un fichier *.env*, qui contient notamment la clé secrète Django non présente dans ce dépôt github.
[^2]: Si vous utilisez *pip*, activer votre environnement virtuel et enlever *pipenv run* :