from flask import Flask, request, render_template, redirect, url_for, session, request, escape
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime as DT



app = Flask(__name__)

conn = psycopg2.connect(
    database = "commerce",
    user = "violet",
    password = "CS22FC1",
    host = "localhost",
    port = 5432
)

app.secret_key = 'mamamomabantot'

@app.route('/')
@app.route('/index')
def index():
    if (checkSession()):
        cartNumber = getCartNumber()
        return render_template('index.html', cartNumber=cartNumber)
    return "<script>alert('Please login first');window.location.href='/login';</script>"

@app.route('/shop', defaults={'category': None})
@app.route('/shop/<category>')
def shop(category):
    if (not checkSession()):
         return "<script>alert('Please login first');window.location.href='/login';</script>"
    cartNumber=getCartNumber()

    cur = conn.cursor(cursor_factory=RealDictCursor)
    if category is None:
        cur.execute("Select * from products inner join product_images on products.product_id = product_images.product_id order by products.product_id asc")  
    else:
        cur.execute("Select * from products inner join category on products.product_id = category.product_id inner join product_images on products.product_id = product_images.product_id where category.category_name = %s order by products.product_id asc", (category,))
    rows = cur.fetchall()
    cur.close()
    return render_template('shop.html', cartNumber=cartNumber, rows = rows)

@app.route('/addToCart/<product_id>', methods=['POST','GET'])
def addToCart(product_id):
    quantity = request.form.get('points')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select customer_id from customers where username = %s", (session['username'],))
    customer = cursor.fetchone()
    customer_id = customer['customer_id']
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("Insert into cart(customer_id,product_id,amount) values (%s,%s,%s);", (customer_id,product_id,quantity))
    conn.commit()
    cursor.close()

    return redirect(url_for('shop'))

@app.route('/about')
def about():
    if (not checkSession()):
         return "<script>alert('Please login first');window.location.href='/login';</script>"
    cartNumber =getCartNumber()
    return render_template('about.html', cartNumber=cartNumber)

@app.route('/contact')
def contact():
    if (not checkSession()):
         return "<script>alert('Please login first');window.location.href='/login';</script>"
    cartNumber =getCartNumber()
    return render_template('contact.html', cartNumber=cartNumber)


@app.route('/cart')
def cart():
    if (not checkSession()):
         return "<script>alert('Please login first');window.location.href='/login';</script>"
    cartNumber =getCartNumber()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select * from cart inner join products on cart.product_id = products.product_id inner join product_images on products.product_id = product_images.product_id where customer_id = (Select customer_id from customers where username = %s);", (session['username'],))
    cart = cursor.fetchall()
    cursor.close()
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select sum(amount * price) as totalAmmount from cart inner join products on cart.product_id = products.product_id where cart.customer_id = (Select customer_id from customers where username = %s);", (session['username'],))
    totalAmmount = cursor.fetchone()
    cursor.close()

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select * from customers inner join addresses on customers.customer_id = addresses.customer_id where customers.customer_id = (Select customer_id from customers where username = %s);", (session['username'],))
    customer = cursor.fetchone()
    cursor.close()

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select * from courier where courier_id = (SELECT floor(random()*(2-1+1))+1);")
    courier = cursor.fetchone()
    cursor.close()

    return render_template('cart.html', cart=cart, totalAmmount = totalAmmount, customer = customer, courier = courier, cartNumber=cartNumber)

@app.route('/deletecart/<id>', methods=['POST','GET'])
def deleteCart(id):
    cursor = conn.cursor()
    cursor.execute("Delete from cart where cart_id=%s;", (id,))
    conn.commit()
    cursor.close()
    return redirect(url_for('cart'))

@app.route('/checkout/<id>/<cour>', methods=['POST'])
def checkout(id,cour):
    payment = request.form.get('Payment')
    creditCard = request.form.get('CC')
    address = request.form.get('Address')
    status = 'Delivering'
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select price from courier where courier_id = %s;", (cour,))
    courierr= cursor.fetchone()
    shipping_fee = courierr['price']
    cursor.close()
    courier_id = cour

    total_tax = 0
    total_price = request.form.get('total')

    today = DT.date.today()
    next_week = today + DT.timedelta(days=7)

    delivery_date = next_week

    cursor = conn.cursor()
    cursor.execute("insert into payment_type(customer_id,payment_method,credit_card_number,currency_id);", (id,payment,creditCard,1))
    conn.commit()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("Select payment_id from payment_type where customer_id =%s;", (id,))
    paymentid= cursor.fetchone()
    payment_id = paymentid[0]
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("insert into orders(customer_id,status,carrier_id,address_id,invoice_no,shipping_fee,total_tax,total_price,payment_id,delivery_date) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", (id,status,courier_id,address,id,shipping_fee,total_tax,total_price,payment_id,delivery_date))
    conn.commit()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("delete from cart where customer_id = %s;", (id,))
    conn.commit()
    cursor.close()

    return "<script>alert('Successfully Ordered Products');window.location.href='/';</script>"

@app.route('/facebook')
def facebook():
    return redirect("https:/facebook.com")

@app.route('/twitter')
def twitter():
    return redirect("https:/twitter.com")

@app.route('/instagram')
def instagram():
    return redirect("https:/instagram.com")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/verify', methods = ["GET", "POST"])
def verify():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cur = conn.cursor()
        cur.execute("SELECT * from customers where username = %s AND password = %s" , (username, password))
        rows = cur.fetchall()
        if(len(rows) == 1):
            session['username'] = username
            cur.close()
            return render_template('index.html')
        else:
            error = "Invalid Credentials"
            return render_template('login.html', error=error)
    if request.method == 'GET':
        firstName =request.args.get('FirstName')        
        lastName =request.args.get('LastName')
        gender=request.args.get('Gender')
        if(genderChooser(gender) <2):
            gender = genderChooser(gender)
        else:
            error = "Invalid Gender"
            return render_template('login.html',error=error)
        birthday= request.args.get('BirthDay')
        email=request.args.get('Email')
        username=request.args.get('UserName')
        password=request.args.get('Password')
        contact=request.form.get('Contacted')
        address1=request.args.get('Address1')
        address2=request.args.get('Address2')
        city = request.args.get('City')
        postal = request.args.get('Postal Code')
        country = request.args.get('Country')

        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("Select * from customers where username = %s" , (username,))
        rows = cur.fetchall()
        cur.close()

        if(len(rows) != 0):
            error = "UserName Already Taken"
            return render_template('login.html', error =error)
        else:
            cur = conn.cursor()
            cur.execute("Insert into customers (first_name,last_name,gender,birthday,email_address,username,password,contact) values (%s,%s,%s,%s,%s,%s,%s,%s);" , (firstName,lastName,gender, birthday,email,username,password,contact,))
            conn.commit()
            cur.close()
            cur = conn.cursor()

            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("Select customer_id from customers where username = %s" , (username,))
            rows = cur.fetchone()
            customer_id = rows['customer_id']
            cur.close()

            cur = conn.cursor()
            cur.execute("Insert into addresses(address1,address2,city,postal_code,country_id,customer_id) values (%s,%s,%s,%s,%s,%s);", (address1,address2,city,postal,country,customer_id,))
            conn.commit()
            cur.close()
            return "<script>alert('Successfully Registered');window.location.href='/login';</script>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

def checkSession():
    if 'username' in session:
        return True
    return False

def genderChooser(gend):
    temp = str(gend).lower()
    switcher = {
        "male": 0,
        "female": 1 
    }
    return switcher.get(temp, 2)

def getCartNumber():
    cur= conn.cursor()
    cur.execute("Select * from cart where customer_id = (Select customer_id from customers where username = %s);", (session['username'],))
    rows = cur.fetchall()
    cartNumber=len(rows)
    cur.close()
    return cartNumber


@app.route('/godMode')
def godMode():
    return render_template('addItem.html')

@app.route('/insertProduct', methods= ["POST"])
def insertProduct():
    image = request.form.get('img')
    name = request.form.get('Name')
    description = request.form.get('Description')
    stock = request.form.get('Stock')
    variation = request.form.get('Variation')
    brand = request.form.get('Brand')
    price = request.form.get('Price')
    category = request.form.get('Category')
    finalImage = '/static/images/' + image

    cursor = conn.cursor()
    cursor.execute("Insert into products(name,description,price,stock,variation,brand) values (%s,%s,%s,%s,%s,%s);", (name,description,price,stock,variation,brand,))
    conn.commit()
    cursor.close()

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("Select product_id from products where name = %s;", (name,))
    row = cursor.fetchone()
    product_id = row['product_id']
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("Insert into product_images(product_id,image_name,image_sorting) values (%s,%s,%s);", (product_id,finalImage,0,))
    conn.commit()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("Insert into category(product_id,category_name) values (%s,%s);", (product_id,category))
    conn.commit()
    cursor.close()

    return redirect(url_for('godMode'))

if __name__ == '__main__':
    app.debug=True
    app.run(host='127.0.0.1', port=5000)


