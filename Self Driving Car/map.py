# Self Driving Car

# Importing the libraries
import numpy as np
from random import random, randint
import matplotlib.pyplot as plt
import time

# Importing the Kivy packages
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.config import Config
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
# Importing the Dqn object from our AI in ai.py
from ai import Dqn

Builder.load_file("menu.kv")
# Adding this line if we don't want the right click to put a red point
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Introducing last_x and last_y, used to keep the last point in memory when we draw the sand on the map
last_x = 0
last_y = 0
n_points = 0
length = 0

# Getting our AI, which we call "brain", and that contains our neural network that represents our Q-function
brain = Dqn(5,3,0.9)
action2rotation = [0,20,-20]
last_reward = 0
scores = []

# Initializing the map
first_update = True
def init():
    global sand
    global goal_x
    global goal_y
    global first_update
    sand = np.zeros((swidth,sheight))
    goal_x = 30
    goal_y = sheight - 30
    first_update = False
    print("firstUpdate");

# Initializing the last distance
last_distance = 0

# Creating the car class

class Car(Widget):

    angle = NumericProperty(0)
    rotation = NumericProperty(0)
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    sensor1_x = NumericProperty(0)
    sensor1_y = NumericProperty(0)
    sensor1 = ReferenceListProperty(sensor1_x, sensor1_y)
    sensor2_x = NumericProperty(0)
    sensor2_y = NumericProperty(0)
    sensor2 = ReferenceListProperty(sensor2_x, sensor2_y)
    sensor3_x = NumericProperty(0)
    sensor3_y = NumericProperty(0)
    sensor3 = ReferenceListProperty(sensor3_x, sensor3_y)
    signal1 = NumericProperty(0)
    signal2 = NumericProperty(0)
    signal3 = NumericProperty(0)

    def move(self, rotation):
        self.pos = Vector(*self.velocity) + self.pos
        self.rotation = rotation
        self.angle = self.angle + self.rotation
        self.sensor1 = Vector(30, 0).rotate(self.angle) + self.pos
        self.sensor2 = Vector(30, 0).rotate((self.angle+30)%360) + self.pos
        self.sensor3 = Vector(30, 0).rotate((self.angle-30)%360) + self.pos
        self.signal1 = int(np.sum(sand[int(self.sensor1_x)-20:int(self.sensor1_x)+20, int(self.sensor1_y)-20:int(self.sensor1_y)+20]))/400.
        self.signal2 = int(np.sum(sand[int(self.sensor2_x)-20:int(self.sensor2_x)+20, int(self.sensor2_y)-20:int(self.sensor2_y)+20]))/400.
        self.signal3 = int(np.sum(sand[int(self.sensor3_x)-20:int(self.sensor3_x)+20, int(self.sensor3_y)-20:int(self.sensor3_y)+20]))/400.
        if self.sensor1_x>swidth-20 or self.sensor1_x<20 or self.sensor1_y>sheight-20 or self.sensor1_y<20:
            self.signal1 = 1.
        if self.sensor2_x>swidth-20 or self.sensor2_x<20 or self.sensor2_y>sheight-20 or self.sensor2_y<20:
            self.signal2 = 1.
        if self.sensor3_x>swidth-20 or self.sensor3_x<20 or self.sensor3_y>sheight-20 or self.sensor3_y<20:
            self.signal3 = 1.

class Ball1(Widget):
    pass
class Ball2(Widget):
    pass
class Ball3(Widget):
    pass

# Creating the game class

class Game(Widget):

    car = ObjectProperty(None)
    ball1 = ObjectProperty(None)
    ball2 = ObjectProperty(None)
    ball3 = ObjectProperty(None)

    def serve_car(self):
        self.car.center = self.center
        self.car.velocity = Vector(3, 0)

    def update(self, dt):

        global brain
        global last_reward
        global scores
        global last_distance
        global goal_x
        global goal_y
        global swidth
        global sheight

        swidth = self.width
        sheight = self.height
        if first_update:
            init()

        xx = goal_x - self.car.x
        yy = goal_y - self.car.y
        orientation = Vector(*self.car.velocity).angle((xx,yy))/180.
        last_signal = [self.car.signal1, self.car.signal2, self.car.signal3, orientation, -orientation]
        action = brain.update(last_reward, last_signal)
        scores.append(brain.score())
        rotation = action2rotation[action]
        self.car.move(rotation)
        distance = np.sqrt((self.car.x - goal_x)**2 + (self.car.y - goal_y)**2)
        self.ball1.pos = self.car.sensor1
        self.ball2.pos = self.car.sensor2
        self.ball3.pos = self.car.sensor3

        if sand[int(self.car.x),int(self.car.y)] > 0:
            self.car.velocity = Vector(1, 0).rotate(self.car.angle)
            last_reward = -1
        else: # otherwise
            self.car.velocity = Vector(3, 0).rotate(self.car.angle)
            last_reward = -0.2
            if distance < last_distance:
                last_reward = 0.1

        if self.car.x < 10:
            self.car.x = 10
            last_reward = -2
        if self.car.x > self.width - 10:
            self.car.x = self.width - 10
            last_reward = -2
        if self.car.y < 20:
            self.car.y = 20
            last_reward = -2
        if self.car.y > self.height - 10:
            self.car.y = self.height - 10
            last_reward = -2

        if distance < 70:
            goal_x = self.width-goal_x
            goal_y = self.height-goal_y
        last_distance = distance

# Adding the painting tools

class MyPaintWidget(Widget):

    def on_touch_down(self, touch):
        global length, n_points, last_x, last_y
        with self.canvas:
            Color(1, 0, 0)
            d = 10.
            touch.ud['line'] = Line(points = (touch.x, touch.y), width = 10)
            last_x = int(touch.x)
            last_y = int(touch.y)
            n_points = 0
            length = 0
            sand[int(touch.x),int(touch.y)] = 1

    def on_touch_move(self, touch):
        global length, n_points, last_x, last_y
        if touch.button == 'left':
            touch.ud['line'].points += [touch.x, touch.y]
            x = int(touch.x)
            y = int(touch.y)
            length += np.sqrt(max((x - last_x)**2 + (y - last_y)**2, 2))
            n_points += 1.
            density = n_points/(length)
            touch.ud['line'].width = int(20 * density + 1)
            sand[int(touch.x) - 10 : int(touch.x) + 10, int(touch.y) - 10 : int(touch.y) + 10] = 1
            last_x = x
            last_y = y
class MenuGridlayout(GridLayout):
     def manual(self):
        self.box=FloatLayout()

        self.Imgl=Image(source='guide.png',allow_stretch =True, keep_ratio = False)
        self.box.add_widget(self.Imgl)


        self.but=(Button(text="Close",size_hint=(None,None),
        	width=150,height=30,pos_hint={'x':0,'y':0}))
        self.box.add_widget(self.but)

        self.main_pop = Popup(title="GAME GUIDE",content=self.box,auto_dismiss=False,size=(500,500))

        self.but.bind(on_release=self.main_pop.dismiss)
        self.main_pop.open()
#
     def save(self): # save button
         print("saving brain...")
         brain.save()
         plt.plot(scores)
         plt.show()
#
     def load(self): # load button
         print("loading last saved brain...")
         brain.load()
# Adding the API Buttons (clear, save and load)

class CarApp(App):

    def build(self):
        parent = Game()
        parent.serve_car()
        self.menu = MenuGridlayout()
        Clock.schedule_interval(parent.update, 1.0/60.0)
        self.painter = MyPaintWidget()
        clearbtn = Button(text = 'clear',width= 80,height= 20)
        clearbtn.bind(on_release = self.clear_canvas)
        goal1 = Label(text = 'Airport', pos = (20, 500),font_size='20sp')
        goal2 = Label(text = 'Downtown', pos = (660, -10),font_size='20sp')
        parent.add_widget(clearbtn)
        parent.add_widget(self.painter)
        parent.add_widget(self.menu)
        parent.add_widget(goal1)
        parent.add_widget(goal2)
        return parent

    def clear_canvas(self, obj):
        global sand
        self.painter.canvas.clear()
        sand = np.zeros((swidth,sheight))

# Running the whole thing
if __name__ == '__main__':
    CarApp().run()
