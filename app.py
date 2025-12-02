from flask import Flask, flash, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask_matomo2 import Matomo

app = Flask(__name__)
matomo = Matomo(
    app,
    matomo_url="http://localhost:8080/matomo",
    id_site=1
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogSite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_super_secret_key_here'
UPLOAD_FOLDER = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Database Models for Blogs, Comments, Users, Projects, Categories

class AboutMe(db.Model):
    ProfileID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    PictureID = db.Column(db.Integer, db.ForeignKey('pictures.PictureID'), nullable=True, default=None)
    Description = db.Column(db.Text, nullable=False)

class Pictures(db.Model):
    PictureID = db.Column(db.Integer, primary_key=True)
    FileNamePFP = db.Column(db.String, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aboutme = db.relationship('AboutMe', backref='pictures', lazy=True)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(100), nullable= False)
    is_admin = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comments', backref='user', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    aboutme = db.relationship('AboutMe', backref='user', lazy=True)
    blogs = db.relationship('Blogs', backref='user', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    categories = db.relationship('Categories', backref='user', lazy=True)

class Comments(db.Model):
    CommentID = db.Column(db.Integer, primary_key=True)
    CommentContents = db.Column(db.Text, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    BlogID = db.Column(db.Integer, db.ForeignKey('blogs.BlogID', ondelete='CASCADE'), nullable=False)

class BlogImage(db.Model):
    ImageID = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=True)
    BlogID = db.Column(db.Integer, db.ForeignKey('blogs.BlogID', ondelete='CASCADE'), nullable=False)

class Blogs(db.Model):
    BlogID = db.Column(db.Integer, primary_key=True)
    BlogName = db.Column(db.String(100), nullable=False)
    BlogContents = db.Column(db.String, nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('Users', backref='blog', foreign_keys=[UserID])
    categoryships = db.relationship('Categoryship', backref='blog', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    comments = db.relationship('Comments', backref='blog', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    image_paths = db.relationship('BlogImage', backref='blog', lazy=True, cascade='all, delete-orphan', passive_deletes=True)

class Categories(db.Model):
    CategoryID = db.Column(db.Integer, primary_key=True)
    CategoryName = db.Column(db.String(100), nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    categoryships = db.relationship('Categoryship', backref='category', lazy=True)

class Categoryship(db.Model):
    CategoryshipID = db.Column(db.Integer, primary_key=True)
    BlogID = db.Column(db.Integer, db.ForeignKey('blogs.BlogID', ondelete='CASCADE'), nullable=False)
    CategoryID = db.Column(db.Integer, db.ForeignKey('categories.CategoryID'), nullable=False)

class Portfolio(db.Model):
    PortfolioID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    CodeSnippet = db.Column(db.Text, nullable=True)  # Optional
    ImagePath = db.Column(db.String, nullable=True)  # Optional
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('Users', backref='portfolio')

# Database end

@app.route('/')
def default():
    return render_template('default.html')

@app.route('/aboutme/<username>')
@login_required
def about_me(username):
    user = Users.query.filter_by(Username=username).first_or_404()
    picture = Pictures.query.filter_by(UserID=user.id).order_by(Pictures.PictureID.desc()).first()
    aboutme = AboutMe.query.filter_by(UserID=user.id).order_by(AboutMe.ProfileID.desc()).first()
    blogs = Blogs.query.filter_by(UserID=user.id).order_by(Blogs.Timestamp.desc()).all()
    portfolios = Portfolio.query.order_by(Portfolio.Timestamp.desc()).all()
    return render_template('about_me.html', user=user, aboutme=aboutme, blogs=blogs, picture=picture, portfolios=portfolios)

@app.route('/aboutme/search/', methods=['GET', 'POST'])
def profile_search():
    query = request.args.get('Usernames', '').strip().lower()
    users = Users.query.all()
    user_profiles = []
    for user in users:
        if query and query not in user.Username.lower():
            continue
        
        aboutme = AboutMe.query.filter_by(UserID=user.id).order_by(AboutMe.ProfileID.desc()).first()
        if aboutme and aboutme.Description:
            sentences = aboutme.Description.strip().split('.')
            short_description = '. '.join(sentences[:2]).strip()
            if short_description and short_description[-1] not in '.?!':
                short_description += '.'
        else:
            short_description = "This person does not have an about me yet."    
        
        user_profiles.append({'user': user, 'aboutme': aboutme, 'short_description': short_description})
    
    return render_template('profile_search.html', user_profiles=user_profiles, query=query)

@app.route('/blog/add', methods=['GET', 'POST'])
@login_required
def add_blog():
    uploaded_filenames = []
    selected_ids = []
    categories_all = Categories.query.filter_by(UserID=current_user.id).all()
    if request.method == 'POST':
        if 'submit_category' in request.form:
            category_name = request.form.get('categoryName')
            if category_name:
                new_category = Categories(
                    UserID=current_user.id,
                    CategoryName=category_name
                )
                db.session.add(new_category)
                db.session.commit()
                categories_all = Categories.query.filter_by(UserID=current_user.id).all()
                return render_template('add_blog.html', categories=categories_all, previews=uploaded_filenames)
            
        elif 'submit_blog' in request.form:
            new_blog = Blogs(
                BlogName=request.form['blogname'],
                BlogContents=request.form['blogcontents'],
                UserID=current_user.id
            )
            db.session.add(new_blog)
            db.session.flush()  # Get BlogID

            # Handle file uploads
            files = request.files.getlist('fileInput')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.root_path, 'static', 'uploads', filename)
                    try:
                        file.save(filepath)
                        uploaded_filenames.append(filename)
                        db.session.add(BlogImage(BlogID=new_blog.BlogID, filename=filename))
                    except Exception as e:
                        print("File save error:", e)

            valid_ids = {c.CategoryID for c in Categories.query.filter_by(UserID=current_user.id).all()}
            selected_ids = request.form.getlist('CategoryID') if request.method == 'POST' else []
            for CategoryID in selected_ids:
                if int(CategoryID) in valid_ids:
                    db.session.add(Categoryship(BlogID=new_blog.BlogID, CategoryID=int(CategoryID)))
                else:
                    print(f"Invalid CategoryID: {CategoryID}")

            db.session.commit()
            return redirect(url_for('blog_display', blog_id=new_blog.BlogID))
    return render_template('add_blog.html', categories=categories_all, previews=uploaded_filenames, selected_ids=selected_ids)

@app.route('/blogs/view', methods=['GET','POST'])
def blog_display():
    search_term = request.args.get('query', '').strip()

    if request.method == 'POST':
        BlogID_raw = request.form.get('BlogID')
        CommentContents = request.form.get('content', '').strip()

        if not BlogID_raw:
            flash('Missing BlogID in form submission.', 'danger')
            return redirect(url_for('blog_display', query=search_term))

        BlogID = int(BlogID_raw)

        if current_user.is_authenticated:
            new_comment = Comments(
                CommentContents=CommentContents,
                BlogID=BlogID,
                UserID=current_user.id
            )
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment added!', 'success')
            return redirect(url_for('blog_display', query=search_term))
        else:
            flash('You must be logged in to comment.', 'danger')
            return redirect(url_for('login'))

    edit_id = request.args.get('edit_id', type=int)

    if search_term:
        # First try exact match on blog name
        blog = Blogs.query.filter(Blogs.BlogName.ilike(search_term)).first()
        if blog:
            return render_template('blog_display.html', blogs=[blog], edit_id=edit_id)

        # Otherwise, try exact match on category name
        category = Categories.query.filter(Categories.CategoryName.ilike(search_term)).first()
        if category:
            blogs = Blogs.query.join(Categoryship).filter(
                Categoryship.CategoryID == category.CategoryID
            ).all()
            return render_template('blog_display.html', blogs=blogs, edit_id=edit_id)

        user = Users.query.filter(Users.Username.ilike(search_term)).first()
        if user:
            blogs = Blogs.query.filter_by(UserID=user.id).all()
            return render_template('blog_display.html', blogs=blogs, edit_id=edit_id)

        # Fallback: partial match (like before)
        blogs = Blogs.query.join(Categoryship).join(Categories).filter(
            db.or_(
                Blogs.BlogName.ilike(f'%{search_term}%'),
                Categories.CategoryName.ilike(f'%{search_term}%')
            )
        ).distinct().all()
        return render_template('blog_display.html', blogs=blogs, edit_id=edit_id)

    # Default: show all blogs
    blogs = Blogs.query.all()
    return render_template('blog_display.html', blogs=blogs, edit_id=edit_id)

@app.route('/blogs/view/<int:id>')
def blogs_display():
    blogs = Blogs.query.get_or_404(id)
    return render_template('blog_display.html', blogs=[blogs])

@app.route('/blogs/<int:id>/delete', methods=['POST'])
@login_required
def delete_blog(id):
    blog = Blogs.query.get_or_404(id)
    if blog.UserID == current_user.id or current_user.IsAdmin:
        db.session.delete(blog)
        db.session.commit()
        flash('Blog Deleted.', 'success')
    else:
        flash('You are not authorized to delete this blog.', 'danger')
    
    return redirect(url_for('about_me', username=current_user.Username))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comments.query.get_or_404(comment_id)

    if comment.UserID == current_user.id or current_user.IsAdmin:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted.', 'success')
    else:
        flash('You are not authorized to delete this comment.', 'danger')

    return redirect(url_for('blog_display', query=request.args.get('query')))

@app.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comments.query.get_or_404(comment_id)
    new_content = request.form.get('content', '').strip()

    if comment.UserID == current_user.id:
        comment.CommentContents = new_content
        db.session.commit()
        flash('Comment updated.', 'success')
    else:
        flash('Unauthorized edit attempt.', 'danger')

    return redirect(url_for('blog_display', query=request.args.get('query')))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Username = request.form['username'].strip()
        Password = request.form['password']

        user = Users.query.filter_by(Username=Username).first()
        if user and check_password_hash(user.Password, Password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('blog_display'))  # or user dashboard
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        Username = request.form['username'].strip()
        Password = request.form['password']

        if not Username or not Password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('signup'))

        existing_user = Users.query.filter_by(Username=Username).first()
        if existing_user:
            flash('Username already taken.', 'warning')
            return redirect(url_for('sign_up'))

        hashed_pw = generate_password_hash(Password)
        new_user = Users(Username=Username, Password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('sign_up.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))  # or redirect to homepage

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    savedfiles = []
    if request.method == 'POST':
        if 'submit_settings' in request.form:
            desc = request.form.get('Description')
            savedfiles = request.files['fileInput']
            aboutme = AboutMe.query.filter_by(UserID=current_user.id).order_by(AboutMe.ProfileID.desc()).first()
            os.makedirs('./static/profileuploads', exist_ok=True)
            if savedfiles and savedfiles.filename:
                FileNamePFP = secure_filename(savedfiles.filename)
                upload_folder = os.path.join(app.root_path, 'static', 'profileuploads')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, FileNamePFP)
                try:
                    savedfiles.save(filepath)
                    print("Saved to file path:", filepath)
                    upload_folder.append(FileNamePFP)
                    savedfiles.append(FileNamePFP)
                except Exception as e:
                    print("File save error:", e)
                print("Saved Files: ", savedfiles)
                new_image = Pictures(
                    UserID=current_user.id,
                    FileNamePFP=FileNamePFP
                )
                db.session.add(new_image)
                db.session.commit()
            else:
                print("Skip empty file input")
        if desc:
            newAboutMe = AboutMe(
                UserID=current_user.id,
                Description = desc
            )
            db.session.add(newAboutMe)
            db.session.commit()
        return redirect(url_for('settings'))
        
    aboutme = AboutMe.query.filter_by(UserID=current_user.id).order_by(AboutMe.ProfileID.desc()).first()
    return render_template('settings.html', aboutme=aboutme, savedfiles=savedfiles)

@app.route('/edit_blog/<int:blog_id>', methods=['GET', 'POST'])
@login_required
def edit_blog(blog_id):
    blog = Blogs.query.get_or_404(blog_id)
    categories = Categories.query.filter_by(UserID=current_user.id).all()
    selected_category_ids = [cs.CategoryID for cs in blog.categoryships]

    if request.method == 'POST' and 'submit_blog' in request.form:
        blog.BlogName = request.form['BlogName']
        blog.BlogContents = request.form['BlogContents']
        
        Categoryship.query.filter_by(BlogID=blog.BlogID).delete(synchronize_session=False)
        
        selected_ids = request.form.getlist('CategoryID')
        for cat_id in selected_ids:
            db.session.add(Categoryship(BlogID=blog.BlogID, CategoryID=int(cat_id)))
            db.session.commit()
        return redirect(url_for('blog_display', blog_id=blog.BlogID))
    return render_template('edit_blog.html', blog=blog, categories=categories, selected_category_ids=selected_category_ids)

@app.route('/portfolio/add', methods=['GET', 'POST'])
@login_required
def add_portfolio():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        code = request.form.get('code')
        image = request.files.get('image')

        image_path = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename

        new_portfolio = Portfolio(
            Title=title,
            Description=description,
            CodeSnippet=code,
            ImagePath=image_path,
            UserID=current_user.id
        )
        db.session.add(new_portfolio)
        db.session.commit()
        return redirect(url_for('about_me', username=current_user.Username))

    return render_template('add_portfolio.html')

@app.route('/portfolio/edit/<int:portfolio_id>', methods=['GET', 'POST'])
@login_required
def edit_portfolio(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    # Only allow owner or admin
    if portfolio.UserID != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        portfolio.Title = request.form['title']
        portfolio.Description = request.form['description']
        portfolio.CodeSnippet = request.form.get('code')

        image = request.files.get('image')
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            portfolio.ImagePath = filename

        db.session.commit()
        return redirect(url_for('about_me', username=current_user.Username))

    return render_template('edit_portfolio.html', portfolio=portfolio)

@app.route('/portfolio/delete/<int:portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    if portfolio.UserID == current_user.id or current_user.IsAdmin:
        db.session.delete(portfolio)
        db.session.commit()
        flash('Blog Deleted.', 'success')
    else:
        flash('You are not authorized to delete this portfolio.', 'danger')
        
    return redirect(url_for('about_me', username=current_user.Username))

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

# Create DB if not exists
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)