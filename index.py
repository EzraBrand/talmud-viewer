from app import app

# This is the WSGI entry point that Vercel requires
# Do not change or rename this variable
app.debug = False

# No need for app.run() here as Vercel handles that part
