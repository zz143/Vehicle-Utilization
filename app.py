from flask import Flask, render_template, url_for, flash, redirect, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from forms import OrderForm, VehicleForm
from decimal import Decimal

app = Flask(__name__)

app.config['SECRET_KEY']='d6cc147eb5b3298ee5f3e629268e454c'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

#Models
class Vehicledetails(db.Model):

    __table_args__ = ( db.CheckConstraint('id in ("Bike", "Scooter", "Truck")'), )

    id = db.Column(db.String(10), primary_key = True)
    capacity = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return 'Vehicledetails({}, {})'.format(self.id, self.capacity)

class Vehicles(db.Model):

    __table_args__ = ( db.CheckConstraint('type in ("Bike", "Scooter", "Truck")'), )

    id = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.String(10), db.ForeignKey('vehicledetails.id'), nullable=False)
    isAssigned = db.Column(db.Boolean, default=False)
    orders = db.relationship('Orders', backref='assigned_vehicle', lazy=True)

    def __repr__(self):
        return 'Vehicles({}, {}, {})'.format(self.id, self.type, self.isAssigned)

class Orders(db.Model):

    __table_args__ = ( db.CheckConstraint('slot in (1, 2, 3, 4)'), )

    id = db.Column(db.Integer, primary_key = True)
    weight = db.Column(db.DECIMAL(5, 2), nullable=False)
    slot = db.Column(db.Integer, nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), default=0)
    
    def __repr__(self):
        return 'Orders({}, {}, {}, {})'.format(self.id, self.weight, self.slot, self.vehicle_id)
      
#Home Page
@app.route('/', methods=['GET', 'POST'])
def home():
    form = OrderForm()
    if form.validate_on_submit():
        qry = db.session.query(func.sum(Orders.weight).label('sum'))
        qry = qry.filter(Orders.slot==form.slot.data)
        sum_list = [q.sum for q in qry.all()]
        if(sum_list[0] and (Decimal(sum_list[0])+Decimal(form.weight.data))>100):
            formatted_weight = "{:.2f}".format(Decimal(sum_list[0]))
            flash('Unable to add this order in DB. Exceeding upper limit of total weight of 100Kg per slot. Current total weight for Slot : {} is {} Kg'.format(form.slot.data, formatted_weight), 'danger')
        else:
            order = Orders(weight=form.weight.data, slot=form.slot.data)
            db.session.add(order)
            db.session.commit()
            flash('Order placed successfully!', 'success')
    
    orders = Orders.query.all()
    return render_template('index.html', form=form, orders=orders)

@app.route('/vehicle_distribution', methods=['GET', 'POST'])
def vehicle_distribution():
    form = VehicleForm()
    unassigned_orders = []
    assigned_order = []
    if form.validate_on_submit():

        vehicle_used = []
        for i in range(11):
            vehicle_used.append([])

        qry = db.session.query(Orders).filter(Orders.slot==form.slot.data).order_by(Orders.weight.desc())
        orders_list = [(q.id, q.weight) for q in qry.all()]

        qry = db.session.query(func.sum(Orders.weight).label('sum'))
        qry = qry.filter(Orders.slot==form.slot.data)
        sum_list = [q.sum for q in qry.all()]
        if(sum_list and sum_list[0]):
            weight_sum = sum_list[0]
        else:
            weight_sum = 0
    
        if form.slot.data=='1':
            if weight_sum>80:
                cur_sum=0
                scooter_idx = 5
                for item in orders_list:

                    if item[1]>50:
                        vehicle_used[0].append(item[0])

                    elif cur_sum + item[1] <= 50:
                        vehicle_used[scooter_idx].append(item[0])
                        cur_sum += item[1]
                    
                    elif cur_sum + item[1] > 50:
                        cur_sum=item[1]
                        scooter_idx+=1
                        vehicle_used[scooter_idx].append(item[0])

            elif weight_sum>50:
                scooter_idx , bike_idx, scooter_cap , bike_cap = 5, 1, 50, 30
                for item in orders_list:
                    if(scooter_cap-item[1]>0):
                        scooter_cap-=item[1]
                        vehicle_used[scooter_idx].append(item[0])
                    elif(bike_cap-item[1]>0):
                        bike_cap-=item[1]
                        vehicle_used[bike_idx].append(item[0])

            elif weight_sum>30:
                scooter_idx = 5
                for item in orders_list:
                    vehicle_used[scooter_idx].append(item[0])

            elif weight_sum>0:
                bike_idx = 1
                for item in orders_list:
                    vehicle_used[bike_idx].append(item[0])

        if form.slot.data=='2' or form.slot.data=='3':

            if weight_sum>80:
                truck_idx = 9
                for item in orders_list:
                    vehicle_used[truck_idx].append(item[0])

            elif weight_sum>50:
                scooter_idx , bike_idx, scooter_cap , bike_cap = 5, 1, 50, 30
                for item in orders_list:
                    if(scooter_cap-item[1]>0):
                        scooter_cap-=item[1]
                        vehicle_used[scooter_idx].append(item[0])
                    elif(bike_cap-item[1]>0):
                        bike_cap-=item[1]
                        vehicle_used[bike_idx].append(item[0])

            elif weight_sum>30:
                scooter_idx = 5
                for item in orders_list:
                    vehicle_used[scooter_idx].append(item[0])

            elif weight_sum>0:
                bike_idx = 1
                for item in orders_list:
                    vehicle_used[bike_idx].append(item[0])
            
        if form.slot.data=='4':

                truck_idx = 9
                for item in orders_list:
                    vehicle_used[truck_idx].append(item[0])

        for i in range(len(vehicle_used)):
            if(vehicle_used[i]):
                if(i==0):
                    unassigned_orders = vehicle_used[i]
                elif i<5:
                    assigned_order.append({
                            'id' : i,
                            'type' : "Bike",
                            'orders' : vehicle_used[i]
                        })
                elif i<9:
                    assigned_order.append({
                            'id' : i,
                            'type' : "Scooter",
                            'orders' : vehicle_used[i]
                        })
                elif i<11:
                    assigned_order.append({
                            'id' : i,
                            'type' : "Truck",
                            'orders' : vehicle_used[i]
                        }) 

    vehicles = Vehicles.query.all()
    vehicle_details = Vehicledetails.query.all()
    return render_template('assigned_vehicle.html', form=form, vehicles=vehicles, vehicle_details=vehicle_details, assigned_order=assigned_order, unassigned_orders=unassigned_orders)

@app.route('/reset', methods=['GET', 'POST'])
def reset_table():
    Orders.__table__.drop(db.engine)
    Orders.__table__.create(db.engine)
    flash('Successfully cleared Orders Table!', 'success')
    return redirect(url_for('home'))


'''-------------------Restful APIs-------------------------------------------'''
@app.route('/orders', methods=['GET'])
def getOrders():
    orders = Orders.query.all()
    orders_list = []
    for item in orders:
        orders_list.append({
            'id' : item.id,
            'slot' : item.slot,
            'weight' : item.weight
        })
    return jsonify({'orders': orders_list})

@app.route('/create', methods=['POST'])
def createOrder():
    req = request.get_json(force=True)
    slot = req['slot']
    weight = req['weight']

    if(slot>4 or slot<=0):
        return 'not a valid slot'
    if(weight>100 or slot<=0):
        return 'not a valid weight'

    qry = db.session.query(func.sum(Orders.weight).label('sum'))
    qry = qry.filter(Orders.slot==slot)
    sum_list = [q.sum for q in qry.all()]

    if(sum_list[0] and (Decimal(sum_list[0])+Decimal(weight))>100):
        formatted_weight = "{:.2f}".format(Decimal(sum_list[0]))
        return 'Unable to add this order in DB. Exceeding upper limit of total weight of 100Kg per slot. Current total weight for Slot : {} is {} Kg'.format(slot, formatted_weight)
    else:
        order = Orders(weight=weight, slot=slot)
        db.session.add(order)
        db.session.commit()
        return 'Order placed successfully!'

@app.route('/get_vehicle_distribution', methods=['GET'])
def get_vehicle_distribution():
    req = request.args.get('slot')
    
    if(req>'4' or req<='0'):
        return 'not a valid slot'

    unassigned_orders = []
    assigned_order = []
    vehicle_used = []
    for i in range(11):
        vehicle_used.append([])

    qry = db.session.query(Orders).filter(Orders.slot==req).order_by(Orders.weight.desc())
    orders_list = [(q.id, q.weight) for q in qry.all()]

    qry = db.session.query(func.sum(Orders.weight).label('sum'))
    qry = qry.filter(Orders.slot==req)
    sum_list = [q.sum for q in qry.all()]
    if(sum_list and sum_list[0]):
        weight_sum = sum_list[0]
    else:
        weight_sum = 0

    if req=='1':
        if weight_sum>80:
            cur_sum=0
            scooter_idx = 5
            for item in orders_list:

                if item[1]>50:
                    vehicle_used[0].append(item[0])

                elif cur_sum + item[1] <= 50:
                    vehicle_used[scooter_idx].append(item[0])
                    cur_sum += item[1]
                
                elif cur_sum + item[1] > 50:
                    cur_sum=item[1]
                    scooter_idx+=1
                    vehicle_used[scooter_idx].append(item[0])

        elif weight_sum>50:
            scooter_idx , bike_idx, scooter_cap , bike_cap = 5, 1, 50, 30
            for item in orders_list:
                if(scooter_cap-item[1]>0):
                    scooter_cap-=item[1]
                    vehicle_used[scooter_idx].append(item[0])
                elif(bike_cap-item[1]>0):
                    bike_cap-=item[1]
                    vehicle_used[bike_idx].append(item[0])

        elif weight_sum>30:
            scooter_idx = 5
            for item in orders_list:
                vehicle_used[scooter_idx].append(item[0])

        elif weight_sum>0:
            bike_idx = 1
            for item in orders_list:
                vehicle_used[bike_idx].append(item[0])

    if req=='2' or req=='3':

        if weight_sum>80:
            truck_idx = 9
            for item in orders_list:
                vehicle_used[truck_idx].append(item[0])

        elif weight_sum>50:
            scooter_idx , bike_idx, scooter_cap , bike_cap = 5, 1, 50, 30
            for item in orders_list:
                if(scooter_cap-item[1]>0):
                    scooter_cap-=item[1]
                    vehicle_used[scooter_idx].append(item[0])
                elif(bike_cap-item[1]>0):
                    bike_cap-=item[1]
                    vehicle_used[bike_idx].append(item[0])

        elif weight_sum>30:
            scooter_idx = 5
            for item in orders_list:
                vehicle_used[scooter_idx].append(item[0])

        elif weight_sum>0:
            bike_idx = 1
            for item in orders_list:
                vehicle_used[bike_idx].append(item[0])
        
    if req=='4':

            truck_idx = 9
            for item in orders_list:
                vehicle_used[truck_idx].append(item[0])

    for i in range(len(vehicle_used)):
        if(vehicle_used[i]):
            if(i==0):
                unassigned_orders = vehicle_used[i]
            elif i<5:
                assigned_order.append({
                        'id' : i,
                        'type' : "Bike",
                        'orders' : vehicle_used[i]
                    })
            elif i<9:
                assigned_order.append({
                        'id' : i,
                        'type' : "Scooter",
                        'orders' : vehicle_used[i]
                    })
            elif i<11:
                assigned_order.append({
                        'id' : i,
                        'type' : "Truck",
                        'orders' : vehicle_used[i]
                    })
    return jsonify({
        'assigned_order': assigned_order,
        'unassigned_orders' : unassigned_orders
    })

if  __name__ == '__main__':
    app.run(debug=True)