from flask import render_template

class HomeController:
    @staticmethod
    def go_home():
        return render_template("open/home.html")