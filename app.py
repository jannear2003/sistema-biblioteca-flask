from flask import Flask, render_template, request, redirect, session, url_for
from database import db
from models import Usuario, Prestamo, Libro

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblioteca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "clave_secreta_super_segura"

db.init_app(app)

with app.app_context():
    db.create_all()


# ======================
# LOGIN
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Credenciales fijas (puedes cambiarlas)
        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/")
        else:
            error = "Credenciales incorrectas"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


def protegido():
    if "admin" not in session:
        return False
    return True


# ======================
# DASHBOARD
# ======================
@app.route("/")
def index():
    if not protegido():
        return redirect("/login")

    total_libros = Libro.query.count()
    libros_disponibles = Libro.query.filter_by(disponible=True).count()
    libros_prestados = Libro.query.filter_by(disponible=False).count()
    total_usuarios = Usuario.query.count()
    total_prestamos = Prestamo.query.count()

    return render_template("index.html",
                           total_libros=total_libros,
                           libros_disponibles=libros_disponibles,
                           libros_prestados=libros_prestados,
                           total_usuarios=total_usuarios,
                           total_prestamos=total_prestamos)


# ======================
# USUARIOS
# ======================
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if not protegido():
        return redirect("/login")

    error = None

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]

        usuario_existente = Usuario.query.filter_by(correo=correo).first()

        if usuario_existente:
            error = "El correo ya está registrado."
        else:
            nuevo_usuario = Usuario(nombre=nombre, correo=correo)
            db.session.add(nuevo_usuario)
            db.session.commit()
            return redirect("/usuarios")

    usuarios = Usuario.query.all()
    return render_template("usuarios.html", usuarios=usuarios, error=error)


# ======================
# LIBROS
# ======================
@app.route("/libros", methods=["GET", "POST"])
def libros():
    if not protegido():
        return redirect("/login")

    if request.method == "POST":
        titulo = request.form["titulo"]
        autor = request.form["autor"]

        nuevo_libro = Libro(titulo=titulo, autor=autor)
        db.session.add(nuevo_libro)
        db.session.commit()

        return redirect("/libros")

    libros = Libro.query.all()
    return render_template("libros.html", libros=libros)


# ======================
# PRESTAMOS
# ======================
@app.route("/prestamos", methods=["GET", "POST"])
def prestamos():
    if not protegido():
        return redirect("/login")

    if request.method == "POST":
        libro_id = request.form["libro_id"]
        usuario_id = request.form["usuario_id"]

        nuevo_prestamo = Prestamo(libro_id=libro_id, usuario_id=usuario_id)
        db.session.add(nuevo_prestamo)

        libro = Libro.query.get(libro_id)
        libro.disponible = False

        db.session.commit()
        return redirect("/prestamos")

    prestamos = Prestamo.query.all()
    usuarios = Usuario.query.all()
    libros = Libro.query.filter_by(disponible=True).all()

    return render_template("prestamos.html",
                           prestamos=prestamos,
                           usuarios=usuarios,
                           libros=libros)


# ======================
# DEVOLVER
# ======================
@app.route("/devolver/<int:id>")
def devolver(id):
    if not protegido():
        return redirect("/login")

    prestamo = Prestamo.query.get(id)

    if prestamo:
        libro = Libro.query.get(prestamo.libro_id)
        libro.disponible = True

        db.session.delete(prestamo)
        db.session.commit()

    return redirect("/prestamos")


if __name__ == "__main__":
    app.run(debug=True)