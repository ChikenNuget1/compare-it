from compare import create_app
import secrets

app = create_app()
app.secret_key = secrets.token_hex(16)

if __name__ == "__main__":
    app.run()