from flask import Flask, render_template, request, redirect, session, url_for, flash
from database import db
from models import Usuario, Prestamo, Libro

app = Flask(__name__)

# SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///biblioteca.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Sesión
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
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Credenciales simples (puedes mejorar luego)
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
    return "admin" in session


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

    return render_template(
        "index.html",
        total_libros=total_libros,
        libros_disponibles=libros_disponibles,
        libros_prestados=libros_prestados,
        total_usuarios=total_usuarios,
        total_prestamos=total_prestamos,
    )


# ======================
# USUARIOS
# ======================
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if not protegido():
        return redirect("/login")

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()

        if not nombre or not correo:
            flash("Debes completar nombre y correo.", "warning")
            return redirect("/usuarios")

        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash("El correo ya está registrado.", "danger")
            return redirect("/usuarios")

        nuevo_usuario = Usuario(nombre=nombre, correo=correo)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Usuario agregado correctamente.", "success")
        return redirect("/usuarios")

    usuarios = Usuario.query.all()
    return render_template("usuarios.html", usuarios=usuarios)


@app.route("/usuarios/eliminar/<int:id>", methods=["POST"])
def eliminar_usuario(id):
    if not protegido():
        return redirect("/login")

    usuario = Usuario.query.get(id)
    if not usuario:
        flash("Usuario no encontrado.", "warning")
        return redirect("/usuarios")

    # En tu app, un préstamo activo existe mientras haya fila en Prestamo
    prestamo_activo = Prestamo.query.filter_by(usuario_id=id).first()
    if prestamo_activo:
        flash("No se puede eliminar el usuario porque tiene un préstamo activo.", "danger")
        return redirect("/usuarios")

    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado correctamente.", "success")
    return redirect("/usuarios")


# ======================
# LIBROS
# ======================
@app.route("/libros", methods=["GET", "POST"])
def libros():
    if not protegido():
        return redirect("/login")

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor = request.form.get("autor", "").strip()

        if not titulo or not autor:
            flash("Debes completar título y autor.", "warning")
            return redirect("/libros")

        nuevo_libro = Libro(titulo=titulo, autor=autor)
        db.session.add(nuevo_libro)
        db.session.commit()
        flash("Libro agregado correctamente.", "success")
        return redirect("/libros")

    libros = Libro.query.all()
    return render_template("libros.html", libros=libros)


@app.route("/libros/eliminar/<int:id>", methods=["POST"])
def eliminar_libro(id):
    if not protegido():
        return redirect("/login")

    libro = Libro.query.get(id)
    if not libro:
        flash("Libro no encontrado.", "warning")
        return redirect("/libros")

    prestamo_activo = Prestamo.query.filter_by(libro_id=id).first()

    # Bloquear si está prestado (por relación o por bandera disponible)
    if prestamo_activo or (hasattr(libro, "disponible") and libro.disponible is False):
        flash("No se puede eliminar el libro porque está prestado.", "danger")
        return redirect("/libros")

    db.session.delete(libro)
    db.session.commit()
    flash("Libro eliminado correctamente.", "success")
    return redirect("/libros")


# ======================
# PRESTAMOS
# ======================
@app.route("/prestamos", methods=["GET", "POST"])
def prestamos():
    if not protegido():
        return redirect("/login")

    if request.method == "POST":
        libro_id = request.form.get("libro_id")
        usuario_id = request.form.get("usuario_id")

        if not libro_id or not usuario_id:
            flash("Debes seleccionar un libro y un usuario.", "warning")
            return redirect("/prestamos")

        libro = Libro.query.get(int(libro_id))
        usuario = Usuario.query.get(int(usuario_id))

        if not libro or not usuario:
            flash("Libro o usuario no válido.", "danger")
            return redirect("/prestamos")

        if libro.disponible is False:
            flash("Ese libro ya está prestado.", "danger")
            return redirect("/prestamos")

        nuevo_prestamo = Prestamo(libro_id=libro.id, usuario_id=usuario.id)
        db.session.add(nuevo_prestamo)

        libro.disponible = False
        db.session.commit()

        flash("Préstamo registrado correctamente.", "success")
        return redirect("/prestamos")

    prestamos = Prestamo.query.all()
    usuarios = Usuario.query.all()
    libros_disponibles = Libro.query.filter_by(disponible=True).all()

    return render_template(
        "prestamos.html",
        prestamos=prestamos,
        usuarios=usuarios,
        libros=libros_disponibles,
    )


# ======================
# DEVOLVER
# ======================
@app.route("/devolver/<int:id>")
def devolver(id):
    if not protegido():
        return redirect("/login")

    prestamo = Prestamo.query.get(id)
    if not prestamo:
        flash("Préstamo no encontrado.", "warning")
        return redirect("/prestamos")

    libro = Libro.query.get(prestamo.libro_id)
    if libro:
        libro.disponible = True

    db.session.delete(prestamo)
    db.session.commit()

    flash("Libro devuelto correctamente.", "success")
    return redirect("/prestamos")


if __name__ == "__main__":
    app.run(debug=True)