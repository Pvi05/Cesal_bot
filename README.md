# Cesal bot
Ce robot discord verifie en continu la présence de logement libre et prévient l'utilisateur par message privé Discord le cas échéant

## Usage

Ce robot nécessite les éléments suivants :

- Un compte Césal (attention, Césal retire les comptes non loueurs au bout de 3 mois)
- Une clé API discord (obtenable en s'enregistrant discord dev)
- Un compte 2captcha (optionnel mais fortement reccomandé)

Les clefs correspondantes sont à entrer en tête du fichier de code.

Ce script a été construit pour tourner en continu, et fonctionnera au mieux sur une machine fixe connecté en permanence à Internet.

Le site de Césal présente un Captcha qui ne peut pas être tout le temps contourné. 
La stratégie du robot ici utilise le service 2captcha pour résoudre le captcha les fois ou cela est nécéssaire. 2captcha est un service payant mais qui facture une fraction de centime d'euro pour 1 captcha. Notre robot conserve les cookies pour résoudre le captcha le moins de fois possible. Au total, le coût par mois d'utilisation du service ne devrait pas dépasser qqu centimes/mois (typiquement 1 ou 2 centimes).

Si vous ne souhaitez pas utiliser ce service, cela nécessitera une mise à jour manuelle des cookies à intervalle régulier (qui varie avec la fréquence de rafraichissement).
La procédure à suivre est la suivante :
- Le robot vous annoncera que les cookies ne sont plus à jour
- Connectez-vous à Césal sur chrome avec votre appareil
- Lancez le script cookie_extraction2.py sur le même appareil
- Copiez-collez le texte imprimé en sortie derriere la commande $cstring dans la conversation discord du Bot

Pour certaines fréquences de rafraichissement, cette procédure sera nécessaire jusqu'à plusieurs fois par semaine, il est donc **vivement reccomandé d'utiliser 2captcha**.

**Dans le code de base, le robot regarde les disponibilités toutes les 5 minutes, et rappele qu'il est en route toutes les 6 heures.** Ces deux valeurs peuvent être modifiés à la fin du code.

Vous trouverez également un fichier bash cesal_bot.sh si vous souhaiter lancer le bot au démarrage de votre appareil (avec un plist par exemple)

## Commandes discord

$cstring : Voir procédure ci-dessus

$logement : Vérification à la demande de la disponibilité (en parallèle de la vérification continue)

$restart : Normalement le robot redémarre tout seul en cas de problème. Si vous pensez néanmoins pour une raison ou une autre que le robot a arreté de vérifier les logements, cette commande relancera la procédure si elle s'est effectivement arrêtée.

  
