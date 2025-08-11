import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class EmailService:
    def __init__(self):
        # Configuration email (à adapter selon votre fournisseur)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.admin_email = "haknprestige@gmail.com"
        self.admin_password = os.getenv('EMAIL_PASSWORD', '')  # À configurer dans les variables d'environnement
        
    def send_email(self, to_email, subject, body, is_html=False):
        """Envoie un email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.admin_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connexion au serveur SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.admin_email, self.admin_password)
            
            # Envoi de l'email
            text = msg.as_string()
            server.sendmail(self.admin_email, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email: {e}")
            return False
    
    def send_welcome_email(self, user):
        """Email de bienvenue après inscription"""
        subject = "Bienvenue sur RépareTout !"
        
        if user.role == 'client':
            body = f"""
Bonjour {user.username},

Bienvenue sur RépareTout, la plateforme qui remet vos objets en vie !

Votre compte client a été créé avec succès. Vous pouvez maintenant :
- Publier des demandes de réparation
- Recevoir des devis de réparateurs qualifiés
- Suivre l'avancement de vos réparations

Connectez-vous dès maintenant pour publier votre première demande.

L'équipe RépareTout
"""
        else:  # repairer
            body = f"""
Bonjour {user.username},

Bienvenue sur RépareTout, la plateforme qui remet les objets en vie !

Votre compte réparateur a été créé avec succès. Vous pouvez maintenant :
- Consulter les demandes de réparation
- Envoyer des devis aux clients
- Gérer vos interventions

Votre compte sera vérifié sous 24h pour garantir la qualité de nos services.

L'équipe RépareTout
"""
        
        # Envoi à l'utilisateur
        self.send_email(user.email, subject, body)
        
        # Notification à l'admin
        admin_subject = f"Nouvelle inscription - {user.role}"
        admin_body = f"""
Nouvelle inscription sur RépareTout :

Utilisateur: {user.username}
Email: {user.email}
Rôle: {user.role}
Ville: {user.city}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

{"Compte réparateur à vérifier." if user.role == 'repairer' else ""}
"""
        self.send_email(self.admin_email, admin_subject, admin_body)
    
    def send_new_request_notification(self, request, repairers):
        """Notification aux réparateurs pour une nouvelle demande"""
        subject = f"Nouvelle demande de réparation - {request.category}"
        
        for repairer in repairers:
            body = f"""
Bonjour {repairer.username},

Une nouvelle demande de réparation correspond à vos compétences :

Titre: {request.title}
Catégorie: {request.category}
Ville: {request.city}
Budget: {request.budget_min}-{request.budget_max}€ (si renseigné)

Description:
{request.description}

Connectez-vous pour consulter la demande complète et envoyer votre devis.

L'équipe RépareTout
"""
            self.send_email(repairer.email, subject, body)
    
    def send_quote_notification(self, quote):
        """Notification au client quand il reçoit un devis"""
        subject = "Nouveau devis reçu sur RépareTout"
        
        body = f"""
Bonjour {quote.repair_request.client.username},

Vous avez reçu un nouveau devis pour votre demande "{quote.repair_request.title}" :

Réparateur: {quote.repairer.username}
Prix: {quote.price / 100}€
Durée estimée: {quote.estimated_duration}
Lieu: {'À domicile' if quote.location_type == 'domicile' else 'En atelier'}

Conditions:
{quote.conditions}

Connectez-vous pour consulter le devis complet et l'accepter si il vous convient.

L'équipe RépareTout
"""
        self.send_email(quote.repair_request.client.email, subject, body)
        
        # Notification à l'admin
        admin_body = f"""
Nouveau devis envoyé :

Demande: {quote.repair_request.title}
Client: {quote.repair_request.client.username}
Réparateur: {quote.repairer.username}
Prix: {quote.price / 100}€
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        self.send_email(self.admin_email, "Nouveau devis envoyé", admin_body)
    
    def send_quote_accepted_notification(self, quote):
        """Notification quand un devis est accepté"""
        # Au réparateur
        subject = "Votre devis a été accepté !"
        body = f"""
Bonjour {quote.repairer.username},

Excellente nouvelle ! Votre devis pour "{quote.repair_request.title}" a été accepté.

Client: {quote.repair_request.client.username}
Ville: {quote.repair_request.city}
Prix convenu: {quote.price / 100}€

Vous pouvez maintenant contacter le client pour organiser l'intervention.

L'équipe RépareTout
"""
        self.send_email(quote.repairer.email, subject, body)
        
        # Au client
        client_subject = "Devis accepté - Prochaines étapes"
        client_body = f"""
Bonjour {quote.repair_request.client.username},

Votre devis a été accepté. Le réparateur {quote.repairer.username} va vous contacter pour organiser l'intervention.

Détails de l'intervention :
Prix: {quote.price / 100}€
Durée estimée: {quote.estimated_duration}
Lieu: {'À domicile' if quote.location_type == 'domicile' else 'En atelier'}

L'équipe RépareTout
"""
        self.send_email(quote.repair_request.client.email, client_subject, client_body)
        
        # Notification à l'admin
        admin_body = f"""
Devis accepté :

Demande: {quote.repair_request.title}
Client: {quote.repair_request.client.username} ({quote.repair_request.client.email})
Réparateur: {quote.repairer.username} ({quote.repairer.email})
Prix: {quote.price / 100}€
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        self.send_email(self.admin_email, "Devis accepté - Intervention à suivre", admin_body)
    
    def send_admin_alert(self, subject, message):
        """Envoie une alerte à l'administrateur"""
        full_subject = f"[RépareTout Alert] {subject}"
        body = f"""
Alerte RépareTout :

{message}

Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        self.send_email(self.admin_email, full_subject, body)

# Instance globale du service email
email_service = EmailService()

