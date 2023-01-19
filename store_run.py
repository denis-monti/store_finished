from app import create_app
from app.models import *

app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True, port=5050)
# app.run(port=8080)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'category': Category, 'Products': Products, 'Review': Review, 'Favourites': Favourites, 'Cart': Cart, 'Balance': Balance, 'Path_picture': Path_picture, 'Price': Price, 'Review_liking_check': Review_liking_check, 'User': User}
