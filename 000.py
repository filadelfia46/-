from flask import Flask, session, redirect, render_template, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from models import UsersModel, CarsModel, DealersModel
from forms import LoginForm, RegisterForm, AddCarForm, SearchPriceForm, SearchDealerForm, AddDealerForm
from db import DB

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db = DB()
UsersModel(db.get_connection()).init_table()
CarsModel(db.get_connection()).init_table()
DealersModel(db.get_connection()).init_table()


@app.route('/')
@app.route('/index')
def index():
    """
    Главная страница
    :return:
    Основная страница сайта, либо редирект на авторизацю
    """
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('/login')
    # если админ, то его на свою страницу
    if session['username'] == 'admin':
        return render_template('index_admin.html', username=session['username'])
    # если обычный пользователь, то его на свою
    cars = CarsModel(db.get_connection()).get_all()
    return render_template('car_user.html', username=session['username'], title='Просмотр базы', cars=cars)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Страница авторизации
    :return:
    переадресация на главную, либо вывод формы авторизации
    """
    form = LoginForm()
    if form.validate_on_submit():  # ввели логин и пароль
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        # проверяем наличие пользователя в БД и совпадение пароля
        if user_model.exists(user_name)[0] and check_password_hash(user_model.exists(user_name)[1], password):
            session['username'] = user_name  # запоминаем в сессии имя пользователя и кидаем на главную
            return redirect('/index')
        else:
            flash('Пользователь или пароль не верны')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    """
    Выход из системы
    :return:
    """
    session.pop('username', 0)
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Форма регистрации
    """
    form = RegisterForm()
    if form.validate_on_submit():
        # создать пользователя
        users = UsersModel(db.get_connection())
        if form.user_name.data in [u[1] for u in users.get_all()]:
            flash('Такой пользователь уже существует')
        else:
            users.insert(user_name=form.user_name.data, email=form.email.data,
                         password_hash=generate_password_hash(form.password_hash.data))
            # редирект на главную страницу
            return redirect(url_for('index'))
    return render_template("register.html", title='Регистрация пользователя', form=form)


"""Работа с обувью"""


@app.route('/car_admin', methods=['GET'])
def car_admin():
    """
    Вывод всей информации об всех моделях обуви
    :return:
    информация для авторизованного пользователя
    """
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('/login')
    # если админ, то его на свою страницу
    if session['username'] != 'admin':
        flash('Доступ запрещен')
        redirect('index')
    # если обычный пользователь, то его на свою
    cars = CarsModel(db.get_connection()).get_all()
    return render_template('car_admin.html',
                           username=session['username'],
                           title='Просмотр обуви',
                           cars=cars)


@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    """
    Добавление модели обуви
    """
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('login')
    # если админ, то его на свою страницу
    if session['username'] != 'admin':
        return redirect('index')
    form = AddCarForm()
    available_dealers = [(i[0], i[1]) for i in DealersModel(db.get_connection()).get_all()]
    form.dealer_id.choices = available_dealers
    if form.validate_on_submit():
        # создать автомобиль
        cars = CarsModel(db.get_connection())
        cars.insert(model=form.model.data,
                    price=form.price.data,
                    power=form.power.data,
                    color=form.color.data,
                    dealer=form.dealer_id.data)
        # редирект на главную страницу
        return redirect(url_for('car_admin'))
    return render_template("add_car.html", title='Добавление обуви', form=form)


@app.route('/car/<int:car_id>', methods=['GET'])
def car(car_id):
    """
    Вывод всей информации о модели
    :return:
    информация для авторизованного пользователя
    """
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('/login')
    # если не админ, то его на главную страницу
    '''if session['username'] != 'admin':
        return redirect(url_for('index'))'''
    # иначе выдаем информацию
    car = CarsModel(db.get_connection()).get(car_id)
    dealer = DealersModel(db.get_connection()).get(car[5])
    return render_template('car_info.html',
                           username=session['username'],
                           title='Просмотр обуви',
                           car=car,
                           dealer=dealer[1])


@app.route('/search_price', methods=['GET', 'POST'])
def search_price():
    """
    Запрос обуви, удовлетворяющих определенной цене
    """
    form = SearchPriceForm()
    if form.validate_on_submit():
        # получить все модели по определенной цене
        cars = CarsModel(db.get_connection()).get_by_price(form.start_price.data, form.end_price.data)
        # редирект на страницу с результатами
        return render_template('car_user.html', username=session['username'], title='Просмотр базы', cars=cars)
    return render_template("search_price.html", title='Подбор по цене', form=form)


@app.route('/search_dealer', methods=['GET', 'POST'])
def search_dealer():
    
    form = SearchDealerForm()
    available_dealers = [(i[0], i[1]) for i in DealersModel(db.get_connection()).get_all()]
    form.dealer_id.choices = available_dealers
    if form.validate_on_submit():
        #
        cars = CarsModel(db.get_connection()).get_by_dealer(form.dealer_id.data)
        # редирект на главную страницу
        return render_template('car_user.html', username=session['username'], title='Просмотр базы', cars=cars)
    return render_template("search_dealer.html", title='Подбор по цене', form=form)


'''Работа с магазином'''


@app.route('/dealer_admin', methods=['GET'])
def dealer_admin():
    
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('/login')
    # если админ, то его на свою страницу
    if session['username'] != 'admin':
        flash('Доступ запрещен')
        redirect('index')
    # иначе это админ
    dealers = DealersModel(db.get_connection()).get_all()
    return render_template('dealer_admin.html',
                           username=session['username'],
                           title='Просмотр по магазинам',
                           dealers=dealers)


@app.route('/dealer/<int:dealer_id>', methods=['GET'])
def dealer(dealer_id):
    """
    Вывод всей информации о магазине
    :return:
    информация для авторизованного пользователя
    """
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('/login')
    # если не админ, то его на главную страницу
    if session['username'] != 'admin':
        return redirect(url_for('index'))
    # иначе выдаем информацию
    dealer = DealersModel(db.get_connection()).get(dealer_id)
    return render_template('dealer_info.html',
                           username=session['username'],
                           title='Просмотр информации о магазине',
                           dealer=dealer)


@app.route('/add_dealer', methods=['GET', 'POST'])
def add_dealer():
    """
    Добавление магазина и вывод на экран информации о нем
    """
    # если пользователь не авторизован, кидаем его на страницу входа
    if 'username' not in session:
        return redirect('/login')
    # если админ, то его на свою страницу
    if session['username'] == 'admin':
        form = AddDealerForm()
        if form.validate_on_submit():
            # создать дилера
            dealers = DealersModel(db.get_connection())
            dealers.insert(name=form.name.data, address=form.address.data)
            # редирект на главную страницу
            return redirect(url_for('index'))
        return render_template("add_dealer.html", title='Добавление дилерского центра', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
