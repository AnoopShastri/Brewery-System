from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, ReviewForm, SearchForm
from models import db, User, Review
import requests

app = Flask(__name__)
app.config.from_object('config.Config')

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/home")
@login_required
def home():
    form = SearchForm()
    return render_template('home.html', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

'''
@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    breweries = None
    if form.validate_on_submit():
        search_type = form.search_type.data
        query = form.query.data
        if search_type == 'by_city':
            response = requests.get(f'https://api.openbrewerydb.org/breweries?by_city={query}')
        elif search_type == 'by_name':
            response = requests.get(f'https://api.openbrewerydb.org/breweries?by_name={query}')
        elif search_type == 'by_type':
            response = requests.get(f'https://api.openbrewerydb.org/breweries?by_type={query}')
        breweries = response.json()
    return render_template('search.html', form=form, breweries=breweries)
'''
@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        query = request.form.get('query')
        if search_type == 'by_city':
            response = requests.get(f'https://api.openbrewerydb.org/breweries?by_city={query}')
        elif search_type == 'by_name':
            response = requests.get(f'https://api.openbrewerydb.org/breweries?by_name={query}')
        elif search_type == 'by_type':
            response = requests.get(f'https://api.openbrewerydb.org/breweries?by_type={query}')
        breweries = response.json()
        return render_template('search_results.html', breweries=breweries)
    return render_template('search.html')

@app.route("/brewery/<string:brewery_id>", methods=['GET', 'POST'])
@login_required
def brewery(brewery_id):
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(rating=form.rating.data, description=form.description.data, brewery_id=brewery_id, user_id=current_user.id)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been added!', 'success')
        return redirect(url_for('brewery', brewery_id=brewery_id))

    response = requests.get(f'https://api.openbrewerydb.org/breweries/{brewery_id}')
    brewery = response.json()
    reviews = Review.query.filter_by(brewery_id=brewery_id).all()
    return render_template('brewery.html', brewery=brewery, reviews=reviews, form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
