Le prompt utilisé pour générer la maquette est le suivant :

```
Je veux créer un template HTML sur une application de création de recette. Cette application permets aux personnes de créer leurs propres recettes personnelles et de soit les mettre dans des cookbooks (ou les créer directement dans celles-ci), soit de les publier en public auquel ils apparaîtront dans une page web tout publique pour les membres afin de partager leurs recettes. Les cookbooks sont un livre de recette personnel ou partagé avec d'autres personnes par un créateur en donnant différentes permissions (éditeur, commentateur, créateur, etc). Selon le profil, certaines actions sont omises et d'autres limitées. Des planning de repas peuvent être créer sur une journée ou une semaine afin de proposer différentes recettes d'entrées/plat et désert. 

En termes de pages web, j'aurais besoin :

- accueil : voir récemment les recettes personnelles consultées/créées (clickable, les cookbooks personnels/partagés, planning repas personnels), contient plusieurs boutons comme importer qui renvoit à un Popup/sous-onglet sur l'import d'un JSON personnalisé pour des cookbooks ou des recettes. Contient un bouton nouveau + pour créer une recette/cookbook/planning personnelle. bouton export pour exporter toutes les recettes personnelles et cookbooks dont j'en suis le créateur/l'auteur

- profil_modifier : montrer le profil de l'utilisateur connecté avec la possibilité de changer de mot de passe, d'icône de profil, d'adresse mail et de supprimer son compte.

- cookbooks partagés avec moi : les cookbooks qui sont partagés avec moi (dont je ne suis pas le créateur, avec indication de la permission que j'ai (lecteur, commentateur, etc)

- recherche recette/cookbooks/planning : page de recherche avec plusieurs possibilités de recherche par nom, tag, personnel, etc, le résultat sera renvoyé ci-dessous des filtres de recherches afin de proposer une réactivité assez simple.

Ce que je t'ai présenté sont les pages principales, maintenant les pages spécifiques :
- pour une recette : écran avec possibilité de modifier le texte qui se trouve au millieu de la page avec possibilité de mettre en gras, format, etc. Séparation par étape avec explication formatée par l'utilisateur. bouton de retour pour retourner à la page précédente. bouton de suppression avec confirmation en écrivant "suppression". possibilité de le consulter en lecture seule si c'est une recette dont n'est pas l'auteur avec pas de possibilité de modifier et observation du texte. le texte écrit et formatté sera en markdown à l'envoie vers l'API pour faciliter le traitement.

- pour un cookbook : création, possibilité d'accéder à la conversation globale ou spécifique à un repas, une planification selon la permission. bouton de création de recette, symbole corbeille sur les recettes pour supprimer et ajouter un pop-up pour valider la suppression d'une recette si la permission le permet. bouton d'export pour exporter le cookbook en question avec ses propres recettes.

- pour un planning : ajout des recettes disponibles dans l'emplacement où il se trouve, s'il est dans un cookbook, alors ce sont les recettes de ce cookbook et pas à l'extérieur, si c'est personnel, alors ce sont les recettes personnelles avec possibilité d'importer depuis l'extérieur un repas public impossible à modifier si j'en suis pas l'auteur et dont j'indique le profil de l'auteur qui l'a créé. 

La charte graphique devra respecter les couleurs suivantes :
- l'entreprise a une couleur verte RGB 84FA16 vers 2AC204 pour le plus foncé avec couleur classique rouge, jaune pour les erreurs et warning.

Donne-moi une charte graphique avec ces couleurs principalement.

L'entreprise fictive s'appelle SUPMEAL et je veux aussi que tu me crées un logo avec le nom écrit et remplacer la lettre P par une Poêle et le L par un couteau avec la couleur verte vers vert foncé.

Pour les onglets des pages principales, privilégier les onglets qui soit vers la gauche. Ajouter une page de connexion et d'inscription assez classique avec quelques boutons d'authentification d'OAuth (Microsoft et google) pour prévoir la connexion Oauth. ça sera les pages "login" et "register" avec différents inputs ?

```

Pour la génération des fichiers HTML :

```
En s'inspirant de la maquette @docs/prototype/Maquette_webapp.png  pour l'application, fait-moi les différentes pages HTML avec cette charte graphique, ces boutons, etc.  tu peux enregister ces fichiers dans le dossier prototype/code pour toutes les pages html séparées.
```