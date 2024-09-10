class EmailUtils:
    @staticmethod
    def generate_test_email(name: str) -> tuple[str, str, str]:
        text = f'Hello, {name}!\nThis is a test email that was sent from your script!'
        html = f'''
        <html>
            <head></head>
            <body>
                <h1>Hello, {name}!</h1>
                <p>This is a test email that was sent from your script!</p>
            </body>
        </html>
        '''

        return 'Test Email', text, html