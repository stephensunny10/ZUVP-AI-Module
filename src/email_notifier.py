import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class EmailNotifier:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.clerk_email = os.getenv('CLERK_EMAIL', 'clerk@municipality.cz')
        
    def send_draft_notification(self, draft_data):
        """Send notification to clerk about new draft"""
        try:
            subject = f"Nový koncept ZUVP - {draft_data['extracted_data'].get('applicant_name', 'N/A')}"
            
            body = f"""
Nový koncept žádosti o ZUVP byl vytvořen:

Žadatel: {draft_data['extracted_data'].get('applicant_name', 'N/A')}
Místo: {draft_data['extracted_data'].get('location', 'N/A')}
Účel: {draft_data['extracted_data'].get('purpose_of_use', 'N/A')}
Poplatek: {draft_data['extracted_data'].get('fee_czk', 0)} Kč
VS: {draft_data['extracted_data'].get('variable_symbol', 'N/A')}

Prosím zkontrolujte a schvalte v systému.

ID žádosti: {draft_data['id']}
"""
            
            self._send_email(self.clerk_email, subject, body)
            logger.info(f"Draft notification sent for {draft_data['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send draft notification: {str(e)}")
    
    def send_approval_email(self, applicant_email, draft_data, attachments=None):
        """Send approval email to applicant with documents"""
        try:
            extracted_data = draft_data['extracted_data']
            
            subject = "Souhlas se zvláštním užíváním veřejného prostranství"
            
            body = f"""
Vážený pane/paní {extracted_data.get('applicant_name', '')},

v příloze zasíláme souhlas se zvláštním užíváním veřejného prostranství dle Vaší žádosti.

Platební údaje:
Účet: 123456789/0100
Variabilní symbol: {extracted_data.get('variable_symbol', 'N/A')}
Částka: {extracted_data.get('fee_czk', 0)} Kč
Splatnost: 30 dnů od vystavení

S pozdravem,
Městský úřad
"""
            
            self._send_email(applicant_email, subject, body, attachments)
            logger.info(f"Approval email sent to {applicant_email}")
            
        except Exception as e:
            logger.error(f"Failed to send approval email: {str(e)}")
    
    def _send_email(self, to_email, subject, body, attachments=None):
        """Send email with optional attachments"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured - email not sent")
            return
        
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Add attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    filename = os.path.basename(file_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}',
                    )
                    msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        text = msg.as_string()
        server.sendmail(self.smtp_user, to_email, text)
        server.quit()