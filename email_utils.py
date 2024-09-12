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

    @staticmethod
    def generate_email(subject: str, title: str, content: str, disclaimer: str) -> tuple[str, str, str]:
        text = f'{title}\n{content}\n\n{disclaimer}'
        html = f'''
        <html>
            <head></head>
            <body>
                <table style="margin: 0 auto; border-spacing: 0; font-family: Arial; font-size: 15px; width: 600px; color: #F0F0F0">
                    <tbody style="background: #121212;">
                        <tr>
                            <td style="padding-top: 20px; padding-bottom: 10px; padding-left: 35px;">
                                <img height="40" src="https://i.postimg.cc/cHTQ7jyW/frogworks-logo.png" alt="Frogworks Logo">
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2" style="padding-left: 35px; padding-right: 35px; padding-bottom: 20px;">
                                <p style="margin: 0; line-height: 25px; border-radius: 3px;">
                                    <span style="padding: 10px 30px 0px 30px; display: block; border-bottom: 2px solid #121212;">
                                        <h1>{title}</h1>
                                    </span>
                                    <span style="padding: 20px 30px; display: block;">
                                        <span style="display: inline-block; line-height: 22px;">
                                            {content}
                                        </span>
                                        <br>
                                        <span style="display: inline-block; margin-top: 20px; line-height: 22px;">
                                            Best regards,
                                            <br>
                                            Frogworks Interactive
                                        </span>
                                    </span>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2" style="padding: 0 35px 20px; font-size: 12px; color: #595959; line-height: 17px; text-align: center;">
                                {disclaimer}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        '''

        return subject, text, html
